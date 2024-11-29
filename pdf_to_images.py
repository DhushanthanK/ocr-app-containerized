import fitz  # Import the pymupdf library as fitz
import os


def convert_to_images(pdf_path):
    pdf = fitz.open(pdf_path)  # Open the PDF file
    base_path = os.path.dirname(pdf_path)
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Create a directory with the file name
    new_dir_path = os.path.join(base_path, file_name)
    os.makedirs(new_dir_path, exist_ok=True)

    # Convert each page of the PDF to an image
    for idx, page in enumerate(pdf, start=1):
        page_img = page.get_pixmap()  # Render the page as an image
        img_out_path = os.path.join(new_dir_path, f"page_{idx}.png")
        page_img.save(img_out_path)  # Save the image

    pdf.close()
