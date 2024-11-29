from paddleocr import PaddleOCR, draw_ocr
import os
import json


def extract_text_from_images(pdf_dir_path):
    # Initialize the OCR model
    ocr = PaddleOCR(use_angle_cls=True, lang="en")

    # Dictionary to hold OCR results for each page
    ocr_results = {}

    # Loop through all images in the directory
    for filename in sorted(os.listdir(pdf_dir_path)):
        # Ensure the file is an image (you can add more extensions if needed)
        if filename.endswith(".png"):
            # Construct full path to the image file
            image_path = os.path.join(pdf_dir_path, filename)

            # Extract OCR result from the image
            ocr_result = ocr.ocr(image_path, cls=True)

            # Get the page number from filename (assuming it's like "page_1.png")
            page_num = os.path.splitext(filename)[0].split("_")[-1]

            # Store the OCR result in the dictionary with page number as key
            ocr_results[f"page_{page_num}"] = ocr_result

    # Save the OCR results to a JSON file in the same directory
    json_path = os.path.join(pdf_dir_path, "ocr_results.json")
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(ocr_results, json_file, ensure_ascii=False, indent=4)
