import os
import argparse
from PIL import Image
import pytesseract

def extract_text_from_image(image_path, output_txt=None):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    print(f"Extracting OCR text from '{image_path}'...")
    image = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(image).strip()

    if not output_txt:
        base_name = os.path.splitext(image_path)[0]
        output_txt = f"{base_name}_ocr.txt"

    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    print(f"Saved: {output_txt}")
    return extracted_text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tesseract OCR Text Extractor")
    parser.add_argument("image_file", help="Path to image/screenshot (.png, .jpg)")
    parser.add_argument("--output", default=None, help="Output text file path")
    args = parser.parse_args()

    extract_text_from_image(args.image_file, args.output)