from pdf2image import convert_from_path
import os
from pathlib import Path


def convert_pdf_to_images(pdf_path, output_dir="data/images"):
    """
    Convert a PDF file to a list of images (one per page).

    Args:
        pdf_path (str): Path to the source PDF file.
        output_dir (str): Directory to save the converted images.

    Returns:
        list: List of paths to the saved images.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        return []

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print(f"Converting '{pdf_path}'...")

    try:
        # standard dpi for OCR is 300
        images = convert_from_path(pdf_path, dpi=300)
    except Exception as e:
        print(f"Error converting PDF: {e}")
        print("Note: 'pdf2image' requires Poppler to be installed and in your PATH.")
        return []

    saved_paths = []
    pdf_name = Path(pdf_path).stem

    for i, image in enumerate(images):
        output_filename = f"{pdf_name}_page_{i + 1}.jpg"
        output_path = os.path.join(output_dir, output_filename)

        image.save(output_path, "JPEG")
        saved_paths.append(output_path)
        print(f"Saved: {output_path}")

    return saved_paths


if __name__ == "__main__":
    # Example usage
    # Ensure you have a 'data/pdfs' directory with a file
    # convert_pdf_to_images("data/pdfs/sample.pdf")
    pass
