import os
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()

# -------------------------------
# ENV SETUP
# -------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY not set. "
        "Create a .env file and add OPENROUTER_API_KEY=your_key"
    )

# OpenAI SDK expects this variable name
os.environ["OPENAI_API_KEY"] = OPENROUTER_API_KEY


# -------------------------------
# OPENROUTER CLIENT
# -------------------------------
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost",
        "X-Title": "Study Buddy"
    }
)


# -------------------------------
# SYLLABUS ANALYSIS
# -------------------------------
def analyze_syllabus(text: str) -> str:
    """
    Calls OpenRouter LLM and returns raw text output.
    JSON parsing is handled safely in main.py.
    """

    text = text.strip()

    # ✅ RELAXED CHECK (IMPORTANT FIX)
    if not text or len(text) < 3:
        raise ValueError("Input text too short for analysis")

    # ✅ STRONG SYSTEM PROMPT (FORCES IMPORTANT POINTS)
    system_prompt = (
        "You are a STRICT JSON generator.\n"
        "You MUST return ONLY valid JSON.\n"
        "DO NOT include markdown, comments, or extra text.\n"
        "\n"
        "Rules you MUST follow:\n"
        "- Every unit MUST contain AT LEAST 3 very_important topics\n"
        "- Every unit MUST contain AT LEAST 3 important topics\n"
        "- optional topics MAY be empty\n"
        "- very_important and important MUST NEVER be empty arrays\n"
        "\n"
        "If the input is only a subject name, infer standard university syllabus units.\n"
        "If unsure, still infer reasonable exam-relevant topics.\n"
    )

    # ✅ IMPROVED USER PROMPT (EXAM-FOCUSED)
    user_prompt = f"""
Analyze the following syllabus or subject name.

Tasks:
1. Identify the subject
2. Identify standard university-level units/modules
3. Infer exam-relevant topics commonly asked in exams

Return JSON in EXACT format:

{{
  "subject": "",
  "units": [
    {{
      "unit_name": "",
      "very_important": [],
      "important": [],
      "optional": []
    }}
  ]
}}

Input:
{text}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            timeout=30
        )

        if not response.choices:
            raise RuntimeError("Empty response from AI")

        content = response.choices[0].message.content

        if not content or not content.strip():
            raise RuntimeError("AI returned empty output")

        return content.strip()

    except OpenAIError as e:
        raise RuntimeError(f"AI request failed: {str(e)}")

    except Exception as e:
        raise RuntimeError(f"Unexpected AI error: {str(e)}")