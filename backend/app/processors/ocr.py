import io
import os

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# On Linux (Railway) tesseract is at /usr/bin/tesseract
# On Windows (local) it's at C:\Program Files\Tesseract-OCR\tesseract.exe
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_from_image(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        image = image.filter(ImageFilter.SHARPEN)
        return pytesseract.image_to_string(
            image, lang="eng+ben+hin", config="--psm 6"
        ).strip()
    except Exception as e:
        print(f"OCR error: {e}")
        return ""