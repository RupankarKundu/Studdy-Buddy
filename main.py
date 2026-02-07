import json
import re
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from ai_service import analyze_syllabus
from pdf_service import extract_text_from_pdf
from youtube_service import search_youtube_playlist
from image_service import extract_text_from_image


app = FastAPI()

# -------------------------------
# CORS (LOCAL DEV SAFE)
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# STATIC FILES (FRONTEND)
# -------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")


# -------------------------------
# FRONTEND ENTRY POINT
# -------------------------------
@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


# -------------------------------
# SAFE JSON PARSER (CRITICAL FIX)
# -------------------------------
def extract_json_safely(text: str) -> dict:
    """
    Extract valid JSON from AI output.
    Handles markdown, extra text, and noise.
    """
    if not text:
        raise ValueError("Empty AI response")

    # Remove markdown code fences if present
    text = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()

    # Extract first JSON object
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON found in AI response")

    return json.loads(match.group())


# -------------------------------
# HELPER: ATTACH YT PLAYLISTS
# -------------------------------
def attach_playlists(data: dict) -> dict:
    for unit in data.get("units", []):
        for level in ["very_important", "important"]:
            enriched = []

            for topic in unit.get(level, []):
                playlist = search_youtube_playlist(
                    f"{topic} full course playlist"
                )

                enriched.append({
                    "topic": topic,
                    "playlist": playlist
                })

            unit[level] = enriched

    return data


# -------------------------------
# COMMON ANALYSIS PIPELINE
# -------------------------------
def analyze_pipeline(text: str, include_playlists: bool):
    text = text.strip()
    if not text or len(text.strip()) < 5:
        return JSONResponse(
            status_code=400,
            content={"error": "Syllabus text is too short or empty"}
        )

    try:
        raw = analyze_syllabus(text)
        data = extract_json_safely(raw)

        if include_playlists:
            data = attach_playlists(data)

        return data

    except json.JSONDecodeError:
        return JSONResponse(
            status_code=500,
            content={"error": "AI returned invalid JSON"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# -------------------------------
# ANALYZE TEXT
# -------------------------------
@app.post("/analyze-text")
async def analyze_text(
    text: str = Form(...),
    include_playlists: bool = Form(True)
):
    return analyze_pipeline(text, include_playlists)


# -------------------------------
# ANALYZE PDF
# -------------------------------
@app.post("/analyze-pdf")
async def analyze_pdf(
    pdf: UploadFile = File(...),
    include_playlists: bool = Form(True)
):
    text = extract_text_from_pdf(pdf.file)
    return analyze_pipeline(text, include_playlists)


# -------------------------------
# ANALYZE IMAGE
# -------------------------------
@app.post("/analyze-image")
async def analyze_image(
    image: UploadFile = File(...),
    include_playlists: bool = Form(True)
):
    text = extract_text_from_image(image.file)
    return analyze_pipeline(text, include_playlists)