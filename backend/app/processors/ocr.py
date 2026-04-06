import io
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# Windows path to Tesseract — update if you installed elsewhere
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_from_image(image_bytes: bytes) -> str:
    """
    Takes raw image bytes, returns extracted text.
    Preprocessing improves accuracy on photos of paper forms.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to grayscale — improves OCR accuracy significantly
        image = image.convert("L")

        # Boost contrast — helps with faded or handwritten text
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Slight sharpening
        image = image.filter(ImageFilter.SHARPEN)

        # OCR with English + Bengali + Hindi language support
        text = pytesseract.image_to_string(
            image,
            lang="eng+ben+hin",
            config="--psm 6",  # assume uniform block of text
        )
        return text.strip()

    except Exception as e:
        print(f"OCR error: {e}")
        return ""