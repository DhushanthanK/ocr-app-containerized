import spacy
import cv2
from paddleocr import PaddleOCR
from fuzzywuzzy import fuzz
import json
import os


def extract_row_lines(ocr_output, y_threshold=40):
    """
    Extracts row lines from PaddleOCR output based on bounding box positions.

    Args:
        ocr_output (list): List of OCR outputs, each containing a bounding box and text.
        y_threshold (int): Maximum difference in the y-coordinate to group bounding boxes into a row.

    Returns:
        list: A list of rows, where each row is a list of text elements found in that row.
    """
    # Sort the OCR output by the y-coordinate of the top-left corner of the bounding box

    rows = []
    current_row = []
    row_center = 0
    for box in ocr_output:
        # Extract the top-left and bottom-left y-coordinates of the bounding box
        top_left_y = box[0][0][1]
        bottom_left_y = box[0][3][1]
        cell_center = (top_left_y + bottom_left_y) / 2

        if row_center == 0:
            row_center = cell_center
        print(box[1][0])
        print(abs(row_center - cell_center))
        if abs(row_center - cell_center) > y_threshold:
            # If current_row is not empty, append it to rows
            if current_row:
                rows.append(current_row)
                row_center = cell_center
            current_row = [box[1][0]]  # Start a new row with the current text
        else:
            current_row.append(box[1][0])  # Append the text to the current row

    # Append the last row if it has content
    if current_row:
        rows.append(current_row)

    return rows


def extract_key_value_pairs_fuzzy(lines, keys, threshold=80):
    """
    Extract key-value pairs from lines of text using fuzzy matching for keys (fuzz.partial_ratio).

    Args:
        lines (list): List of strings representing the text lines.
        keys (list): List of keys to search for in the text.
        threshold (int): Minimum fuzzy match score to consider a match valid (default: 80).

    Returns:
        dict: Extracted key-value pairs along with confidence scores.
    """
    key_value_pairs = {}

    for line in lines:
        # Iterate over each key to find the best fuzzy match
        for key in keys:
            match_ratio = fuzz.partial_ratio(key.lower(), line.lower())

            # If match ratio is above the threshold, consider it a match
            if match_ratio >= threshold:
                # Extract the value before the key and assign the rest of the line as the value
                key_index = line.lower().find(key.lower())

                # If the key is found, split the line into the part before and after the key
                if key_index != -1:
                    value_before_key = line[:key_index].strip()
                    value_after_key = line[key_index + len(key) :].strip()

                    # Combine the extracted value and assign to the matched key
                    value = f"{value_before_key} {value_after_key}".strip()
                    # Store the extracted value and its confidence score
                    key_value_pairs[key] = (
                        value,
                        match_ratio,
                    )  # Tuple of (value, confidence score)

                # Remove the matched key from the keys list (if you want to avoid matching it again)
                keys.remove(key)
                break  # Exit loop after finding a match for this line

    return key_value_pairs


def extract_key_info_from_ocr_results(ocr_results_path, classification_result):
    keys_bank_statement = [
        "Account Name",
        "Address",
        "Date",
        "Account Number",
        "Branch",
        "Drawing Power",
        "Interest Rate",
        "MOD Balance",
        "CIF No.",
        "IFS Code",
        "MICR Code",
        "Nomination Registered",
        "Balance",
        "Account Statement",
    ]
    keys_Medical_Documents = [
        "Patient Name",
        "Date of Birth",
        "Gender",
        "Medical Record Number",
        "Diagnosis",
        "Allergies",
        "Medications",
        "Dosage",
        "Prescribing Doctor",
        "Date of Visit",
        "Treatment Plan",
        "Follow-up Appointment",
        "Vital Signs",
        "Lab Results",
        "Imaging Studies",
        "Insurance Information",
        "Emergency Contact",
        "Medical History",
        "Lifestyle Factors",
        "Family History",
    ]
    keys_Invoices = [
        "Invoice Number",
        "Invoice Date",
        "Due Date",
        "Bill To",
        "Ship To",
        "Company Name",
        "Contact Person",
        "Address",
        "City",
        "State",
        "Zip Code",
        "Country",
        "Item Description",
        "Quantity",
        "Unit Price",
        "Total Price",
        "Tax Rate",
        "Tax Amount",
        "Subtotal",
        "Total Amount",
        "Payment Terms",
        "Payment Method",
        "Invoice Status",
        "Notes",
        "Purchase Order Number",
    ]

    # Load OCR results JSON
    with open(ocr_results_path, "r", encoding="utf-8") as file:
        ocr_results = json.load(file)

    # Dictionary to hold extracted key-value data
    extracted_data = {}

    # Process each page in OCR results
    for page_num, page_data in ocr_results.items():
        if classification_result[page_num] == ["Bank Statements"]:
            keys = keys_bank_statement
        elif classification_result[page_num] == ["Medical Documents"]:
            keys = keys_Medical_Documents
        elif classification_result[page_num] == ["Invoices"]:
            keys = keys_Invoices
        else:
            keys = []
        # Extract text lines from page data
        rows = [
            line[1][0] for line in page_data[0]
        ]  # Adjust based on OCR output structure
        row_lines = []

        # Combine words into lines
        for row in rows:
            line = ""
            for word in row:
                line += word + " "
            row_lines.append(line.strip())

        # Extract key-value pairs
        if keys == []:
            extracted_data[page_num] = {}
        else:
            page_extracted_data = extract_key_value_pairs_fuzzy(row_lines, keys)
            extracted_data[page_num] = page_extracted_data

    # Save extracted data to new JSON file
    output_path = os.path.join(
        os.path.dirname(ocr_results_path), "extracted_key_information.json"
    )
    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(extracted_data, output_file, ensure_ascii=False, indent=4)

    print(f"Extracted data saved to {output_path}")
    return extracted_data
