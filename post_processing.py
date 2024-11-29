import json
import os


def extract_combined_information(
    classification_result, key_value_extraction_result, table_result, output_file_path
):
    combined_output = {}

    for page_num in classification_result.keys():
        # Initialize the output for each page
        combined_output[page_num] = {
            "Classification": (),
            "Key_information": {},
            "table_result": "",
        }

        # Process classification result
        if classification_result[page_num]:
            classification_type, classification_details = next(
                iter(classification_result[page_num].items())
            )
            average_score = classification_details["average_score"]
            combined_output[page_num]["Classification"] = (
                classification_type,
                average_score,
            )

        # Process key value extraction result
        if page_num in key_value_extraction_result:
            combined_output[page_num]["Key_information"] = key_value_extraction_result[
                page_num
            ]

        # Process table result
        if page_num in table_result:
            combined_output[page_num]["table_result"] = table_result[page_num]

    output_path = os.path.join(output_file_path, "final_results.json")
    with open(output_path, "w", encoding="utf-8") as json_file:
        json.dump(combined_output, json_file, ensure_ascii=False, indent=4)
    print(f"Combined output written to {output_file_path}")

    return combined_output