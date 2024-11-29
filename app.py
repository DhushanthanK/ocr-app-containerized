from flask import Flask, request, render_template, redirect, url_for
import os
import pdf_to_images
import ocr_extraction
import page_classification
import key_value_extraction
import table_extraction
import post_processing

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Ensure the upload folder exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

@app.route("/")
def index():
    """Render the index page."""
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    """Handle file uploads."""
    file = request.files.get("file")
    
    if not file or file.filename == "":
        return redirect(request.url)
    
    pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(pdf_path)
    process_pdf(pdf_path)
    
    return redirect(url_for("results", filename=file.filename))

def check_pages(data):
    """Check the pages and extract keys."""
    result = {}
    for page_key, page_value in data.items():
        if isinstance(page_value, dict) and page_value:
            result[page_key] = list(page_value.keys())
        else:
            result[page_key] = []
    return result

def process_pdf(pdf_path):
    """Process the uploaded PDF."""
    base_dir = os.path.splitext(pdf_path)[0]
    os.makedirs(base_dir, exist_ok=True)
    
    # Convert PDF to images
    pdf_to_images.convert_to_images(pdf_path)
    
    # OCR extraction
    ocr_extraction.extract_text_from_images(base_dir)
    ocr_path = os.path.join(base_dir, "ocr_results.json")
    
    # Page classification
    classification_result = page_classification.classify_images(base_dir)
    classification_keys = check_pages(classification_result)
    
    # Key-value extraction
    key_value_results = key_value_extraction.extract_key_info_from_ocr_results(
        ocr_path, classification_keys
    )
    
    # Table extraction
    table_results = table_extraction.extract_tables_from_images(base_dir)
    
    # Post-processing
    post_processing.extract_combined_information(
        classification_result, key_value_results, table_results, base_dir
    )

@app.route("/results/<filename>")
def results(filename):
    """Display results after processing."""
    return f"Processed {filename}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)