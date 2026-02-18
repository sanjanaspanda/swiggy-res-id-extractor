from ultralytics import YOLO
import cv2
import numpy as np


class FieldDetector:
    def __init__(self, model_path=None):
        """
        Initialize the YOLO field detector.

        Args:
            model_path (str): Path to the trained YOLOv8 model (.pt file).
                              If None, loads a pre-trained generic model (not useful for custom fields).
        """
        if model_path:
            self.model = YOLO(model_path)
        else:
            # Load a standard model just for structure (will detect 'person', 'car', etc. until retrained)
            print("Warning: Loading generic YOLOv8n model. Please train on your data.")
            self.model = YOLO("yolov8n.pt")

    def detect(self, image_path, conf_threshold=0.5):
        """
        Detect fields in a document image.

        Args:
            image_path (str): Path to the image file.
            conf_threshold (float): Confidence threshold for detections.

        Returns:
            list: List of dictionaries containing detection info:
                  {'class_id': int, 'class_name': str, 'confidence': float, 'bbox': [x1, y1, x2, y2], 'crop': numpy_array}
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not read image at {image_path}")
            return []

        results = self.model.predict(
            image_path, conf=conf_threshold, save=False, verbose=False
        )
        result = results[0]  # We process one image at a time

        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
            conf = float(box.conf[0].cpu().numpy())
            cls_id = int(box.cls[0].cpu().numpy())
            cls_name = result.names[cls_id]

            # Crop the detected region
            crop = image[y1:y2, x1:x2]

            detections.append(
                {
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": conf,
                    "bbox": [x1, y1, x2, y2],
                    "crop": crop,
                }
            )

        return detections


if __name__ == "__main__":
    # Test stub
    detector = FieldDetector()
    print("Detector initialized.")
