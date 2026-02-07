import pdfplumber


MAX_PAGES = 20        # safety limit
MAX_CHARS = 8000     # prevents huge AI prompts


def extract_text_from_pdf(file) -> str:
    """
    Extract text from a PDF safely.

    - Handles corrupt PDFs
    - Handles scanned PDFs (returns empty text)
    - Limits pages and characters
    - Never crashes
    """

    text_chunks = []

    try:
        with pdfplumber.open(file) as pdf:
            for i, page in enumerate(pdf.pages):
                if i >= MAX_PAGES:
                    break

                page_text = page.extract_text()
                if page_text:
                    cleaned = page_text.replace("\x00", "").strip()
                    if cleaned:
                        text_chunks.append(cleaned)

                # Stop if text is already large
                if sum(len(chunk) for chunk in text_chunks) > MAX_CHARS:
                    break

    except Exception:
        # Any PDF parsing error
        return ""

    text = "\n".join(text_chunks).strip()

    if not text:
        return ""

    # Final length guard
    return text[:MAX_CHARS]
