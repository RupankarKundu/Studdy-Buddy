from PIL import Image
import pytesseract


def extract_text_from_image(file) -> str:
    """
    Extract text from image using Pillow + Tesseract.

    - Safe if Tesseract is missing
    - Safe for corrupt / unsupported images
    - Always returns a string (never crashes)
    """

    try:
        # Load and preprocess image
        image = Image.open(file).convert("L")  # grayscale

        text = pytesseract.image_to_string(
            image,
            config="--psm 6"
        )

        if not text or not text.strip():
            return ""

        return text.strip()

    except pytesseract.TesseractNotFoundError:
        # Tesseract not installed on system
        return ""

    except Exception:
        # Any other image/OCR error
        return ""
