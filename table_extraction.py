from transformers import AutoImageProcessor, TableTransformerForObjectDetection
from transformers import DetrFeatureExtractor, DetrForObjectDetection
import torch
from PIL import Image
import cv2
import numpy as np
from paddleocr import PaddleOCR
import pandas as pd
import os
import json


ocr = PaddleOCR(
    lang="en",
    use_gpu=False,
    show_log=False,
)

image_processor = AutoImageProcessor.from_pretrained(
    "microsoft/table-transformer-detection"
)
model = TableTransformerForObjectDetection.from_pretrained(
    "microsoft/table-transformer-detection"
)

model_structure = TableTransformerForObjectDetection.from_pretrained(
    "microsoft/table-transformer-structure-recognition"
)


def get_row_col_bounds(table, ts_thresh=0.7, plot=False):
    feature_extractor = DetrFeatureExtractor()
    table_encoding = feature_extractor(table, return_tensors="pt")

    # predict table structure
    with torch.no_grad():
        outputs = model_structure(**table_encoding)

    # visualize table structure
    target_sizes = [table.size[::-1]]
    table_struct_results = feature_extractor.post_process_object_detection(
        outputs, threshold=ts_thresh, target_sizes=target_sizes
    )[0]

    row_boxes = table_struct_results["boxes"][
        table_struct_results["labels"] == model_structure.config.label2id["table row"]
    ]

    row_scores = table_struct_results["scores"][
        table_struct_results["labels"] == model_structure.config.label2id["table row"]
    ]

    col_boxes = table_struct_results["boxes"][
        table_struct_results["labels"]
        == model_structure.config.label2id["table column"]
    ]

    col_scores = table_struct_results["scores"][
        table_struct_results["labels"]
        == model_structure.config.label2id["table column"]
    ]

    table_header_box = table_struct_results["boxes"][
        table_struct_results["labels"]
        == model_structure.config.label2id["table column header"]
    ]
    table_header_score = table_struct_results["scores"][
        table_struct_results["labels"]
        == model_structure.config.label2id["table column header"]
    ]

    print(f"Num rows initially detected: {len(row_boxes)}")
    print(f"Num cols initially detected: {len(col_boxes)}")
    print(f"Num table header detected: {len(table_header_box)}")

    return (
        row_boxes,
        row_scores,
        col_boxes,
        col_scores,
        table_header_box,
        table_header_score,
    )


def sort_row_col_boxes(row_boxes, col_boxes):
    row_boxes = row_boxes.tolist()
    col_boxes = col_boxes.tolist()
    row_boxes.sort(key=lambda x: x[1])  # [top_x, top_y, bottom_x, bottom_y]
    col_boxes.sort(key=lambda x: x[0])
    return row_boxes, col_boxes


def get_cells_by_intersecting_rows_and_cols(row_boxes, col_boxes, padding=(0, 0)):
    cells = []
    for row_box in row_boxes:
        for col_box in col_boxes:
            cell_left_upper_x = col_box[0]
            cell_left_upper_y = row_box[1]
            cell_right_lower_x = col_box[2]
            cell_right_lower_y = row_box[3]
            cells.append(
                [
                    cell_left_upper_x,
                    cell_left_upper_y,
                    cell_right_lower_x,
                    cell_right_lower_y,
                ]
            )
    return cells


def PIL_to_cv(pil_img):
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def add_padding(image, padding_width, color=(255, 255, 255)):
    """Adds padding to a PIL image.

    Args:
      image: The PIL Image object.
      padding_width: The width of the padding in pixels.
      color: The color of the padding (default: white).

    Returns:
      A new PIL Image object with the padding added.
    """
    width, height = image.size
    new_width = width + 2 * padding_width
    new_height = height + 2 * padding_width
    new_image = Image.new(image.mode, (new_width, new_height), color)
    new_image.paste(image, (padding_width, padding_width))
    return new_image


def extract_tables_from_images(dir_path):
    all_tables = {}  # Dictionary to store tables with keys as page numbers

    # Iterate over all images in the directory
    for image_file in os.listdir(dir_path):
        if image_file.endswith(".png") or image_file.endswith(".jpg"):
            # Load and preprocess image
            image_path = os.path.join(dir_path, image_file)
            image = Image.open(image_path).convert("RGB")

            # Detect tables in the image
            inputs = image_processor(images=image, return_tensors="pt")
            outputs = model(**inputs)
            target_sizes = torch.tensor([image.size[::-1]])
            results = image_processor.post_process_object_detection(
                outputs, threshold=0.9, target_sizes=target_sizes
            )[0]

            # Check if any tables were detected
            if results["scores"].numel() == 0:  # If no scores, no tables detected
                # Extract page number from the image file name
                page_num = os.path.splitext(image_file)[0].split("_")[-1]
                all_tables[f"page_{page_num}"] = ""  # Assign empty string for no table
                print(f"No table detected for {image_file}.")
                continue  # Skip to the next image

            # Process each detected table
            for score, label, box in zip(
                results["scores"], results["labels"], results["boxes"]
            ):
                box = [round(i, 2) for i in box.tolist()]
                padding = 10
                box = [
                    box[0] - padding,
                    box[1] - padding,
                    box[2] + padding,
                    box[3] + padding,
                ]
                table_image = image.crop(box)

                # Structure detection and extraction
                padded_image = add_padding(table_image, 20)
                table_structure_outs = get_row_col_bounds(padded_image)
                sorted_rows, sorted_cols = sort_row_col_boxes(
                    table_structure_outs[0], table_structure_outs[2]
                )
                cells = get_cells_by_intersecting_rows_and_cols(
                    sorted_rows, sorted_cols
                )

                # Extract cell data using OCR
                num_rows = len(sorted_rows)
                num_cols = len(sorted_cols)
                extracted_data = []
                confidence_scores = []  # List to store confidence scores

                for cell in cells:
                    cell_image = padded_image.crop(cell)
                    result = ocr.ocr(PIL_to_cv(cell_image))

                    # Check if result is valid and extract confidence score
                    if result and result[0]:
                        value = result[0][0][1][0]  # Extracted text
                        confidence = result[0][0][1][1]  # Confidence score
                        extracted_data.append(value)
                        confidence_scores.append(confidence)
                    else:
                        extracted_data.append(None)  # Append None if no result
                        confidence_scores.append(
                            0
                        )  # Append 0 for confidence if no result

                # Create a DataFrame with extracted data and confidence scores
                df = pd.DataFrame(index=range(num_rows), columns=range(num_cols))

                for i, data in enumerate(extracted_data):
                    df.iloc[i // num_cols, i % num_cols] = data

                # Add confidence scores to the DataFrame
                confidence_df = pd.DataFrame(
                    index=range(num_rows), columns=range(num_cols)
                )
                for i, score in enumerate(confidence_scores):
                    confidence_df.iloc[i // num_cols, i % num_cols] = score

                # Combine extracted data and confidence scores into a single DataFrame
                combined_df = pd.concat(
                    [df, confidence_df], axis=1, keys=["Data", "Confidence"]
                )

                # Convert DataFrame to JSON format
                json_output = combined_df.to_json(orient="records")

                # Extract page number from the image file name
                page_num = os.path.splitext(image_file)[0].split("_")[-1]

                # Store the extracted table in the dictionary
                all_tables[f"page_{page_num}"] = json_output

                # Save to a JSON file named after the image
                json_file_name = f"{os.path.splitext(image_file)[0]}_table.json"
                json_output_path = os.path.join(dir_path, json_file_name)
                with open(json_output_path, "w") as json_file:
                    json.dump(json_output, json_file)

                print(f"Extracted table saved to {json_output_path}")

    # Save all extracted tables to a single JSON file
    all_tables_output_path = os.path.join(dir_path, "all_extracted_tables.json")
    with open(all_tables_output_path, "w") as all_tables_file:
        json.dump(all_tables, all_tables_file, ensure_ascii=False, indent=4)

    print(f"All extracted tables saved to {all_tables_output_path}")

    return all_tables
