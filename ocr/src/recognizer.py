from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import torch
import cv2
import numpy as np


class TextRecognizer:
    def __init__(self, use_gpu=True):
        """
        Initialize TrOCR for handwriting recognition.
        Using 'microsoft/trocr-base-handwritten' by default.
        """
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        print(f"Loading TrOCR model on {self.device}...")

        try:
            self.processor = TrOCRProcessor.from_pretrained(
                "microsoft/trocr-base-handwritten"
            )
            self.model = VisionEncoderDecoderModel.from_pretrained(
                "microsoft/trocr-base-handwritten"
            ).to(self.device)
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading TrOCR: {e}")
            print("Ensure you have internet access to download the model.")
            self.model = None

    def preprocess(self, cv2_image):
        """
        Preprocess text crop for better recognition (binarization, denoising).
        """
        # Convert to grayscale
        if len(cv2_image.shape) == 3:
            gray = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = cv2_image

        # Simple denoising
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Adaptive thresholding to handle uneven lighting/shadows (common in scans)
        # binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

        # For TrOCR, pure binary might be too harsh, denoised grayscale is often good.
        # We'll convert back to RGB for the model input
        rgb = cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(rgb)

    def recognize(self, image_crop):
        """
        Recognize text from an image crop (numpy array).
        """
        if self.model is None:
            return "Model not loaded"

        if image_crop is None or image_crop.size == 0:
            return ""

        pil_image = self.preprocess(image_crop)

        pixel_values = self.processor(
            images=pil_image, return_tensors="pt"
        ).pixel_values.to(self.device)

        with torch.no_grad():
            generated_ids = self.model.generate(pixel_values)
            generated_text = self.processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0]

        return generated_text


if __name__ == "__main__":
    recognizer = TextRecognizer(use_gpu=False)  # Default to CPU for simple test
    print("Recognizer initialized.")
