import os
import argparse
import json
from ingestion import convert_pdf_to_images
from detector import FieldDetector
from recognizer import TextRecognizer


def process_document(pdf_path, detector, recognizer, output_dir):
    """
    Full pipeline to process a single PDF document.
    """
    print(f"Processing: {pdf_path}")

    # 1. Convert PDF to Images
    image_paths = convert_pdf_to_images(
        pdf_path, output_dir=os.path.join(output_dir, "images")
    )

    document_results = []

    for img_path in image_paths:
        print(f"  Analyzing page: {os.path.basename(img_path)}")
        page_data = {"page": os.path.basename(img_path), "fields": []}

        # 2. Detect Fields
        detections = detector.detect(img_path)

        if not detections:
            print("    No fields detected (Did you train the model yet?)")

        for d in detections:
            field_name = d["class_name"]
            conf = d["confidence"]
            crop = d["crop"]

            print(f"    Detected '{field_name}' ({conf:.2f})")

            # 3. Recognize Text
            text = recognizer.recognize(crop)
            print(f"      -> Text: {text}")

            page_data["fields"].append(
                {
                    "field": field_name,
                    "text": text,
                    "confidence": conf,
                    "bbox": d["bbox"],
                }
            )

        document_results.append(page_data)

    return document_results


def main():
    parser = argparse.ArgumentParser(
        description="OCR Pipeline for Handwritten Documents"
    )
    parser.add_argument(
        "--input", "-i", type=str, required=True, help="Path to input PDF file"
    )
    parser.add_argument(
        "--model", "-m", type=str, default=None, help="Path to trained YOLO model (.pt)"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="results", help="Output directory"
    )

    args = parser.parse_args()

    # Initialize Models
    print("Initializing Pipeline...")
    detector = FieldDetector(model_path=args.model)
    recognizer = TextRecognizer()  # Downloads model on first run

    # Run
    results = process_document(args.input, detector, recognizer, args.output)

    # Save Results
    os.makedirs(args.output, exist_ok=True)
    result_path = os.path.join(args.output, "output.json")
    with open(result_path, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Done. Results saved to {result_path}")


if __name__ == "__main__":
    main()
