import os
import yt_dlp
import whisper
from django.conf import settings
from google import genai
from dotenv import load_dotenv
import json
 
from core.settings import YDL_BASE_OPTS
from quiz_app.models import Question

load_dotenv()

def download_audio_from_url(url: str, quiz_id: int = None) -> dict:
    """
    Load audio from a video URL using yt-dlp.
    Callback to local storage path.
    """
    if not url:
        return {"success": False, "error": "No URL provided."}

    output_dir = os.path.join(os.getcwd(), "quiz_app", "media")
    os.makedirs(output_dir, exist_ok=True)

    filename = f"quiz_{quiz_id or 'temp'}_%(id)s.%(ext)s"
    outtmpl = os.path.join(output_dir, filename)

    ydl_opts = {
        **settings.YDL_BASE_OPTS,
        "outtmpl": outtmpl,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = os.path.normpath(ydl.prepare_filename(info))

        return {
            "success": True,
            "filepath": filepath,
            "title": info.get("title"),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def run_whisper_transcription(audio_path: str) -> str:
    """
    startet Whisper_Model(small or medium) to transcribe audio file.
    """
    audio_path = os.path.abspath(audio_path)

    try:
        model = whisper.load_model("small")
        result = model.transcribe(audio_path, language="de")
        os.remove(audio_path)
        return result["text"]
    except Exception as e:
        return ""
    

def generate_quiz_with_gemini(transcript: str) -> dict:
    """
    Generate quiz data using Gemini API.
    """
    if not transcript.strip():
        return {"title": "Fehler", "description": "Kein Transkript vorhanden", "questions": []}

    prompt = f"""
    Create a quiz based on the following video transcript.
    
    Requirements:
    - Create 10 multiple-choice questions.
    - Each question must have exactly 4 answer options.
    - Return the answer in the following JSON format:

    {{
      "title": "Quiz Title",
      "description": "Brief description",
      "questions": [
        {{
          "question_title": "...",
          "question_options": ["...", "...", "...", "..."],
          "answer": "..."
        }}
      ]
    }}

    Transcript:
    {transcript[:12000]}  # Limit length to avoid prompt being too large
    """

    api_key = os.getenv('api_key')
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=(prompt)
        )
        raw_output = response.text.strip()

        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            """
            If the model mixes text with JSON → look for JSON part
            """
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(raw_output[start:end])
            else:
                raise ValueError("Gemini output was not valid JSON.")

    except Exception as e:
        print(f"Gemini error: {e}")
        return {
            "title": "Failed Generation",
            "description": str(e),
            "questions": [],
        }    

    
def generate_quiz_from_video(quiz):
    """
    Load audio, transcribe and generate quiz data (modifies the DB)."""
    result = download_audio_from_url(quiz.url, quiz_id=quiz.id)
    if not result["success"]:
        quiz.title = "Error downloading"
        quiz.save()
        return

    audio_path = result["filepath"]

    transcript = run_whisper_transcription(audio_path)

    quiz_data = generate_quiz_with_gemini(transcript)

    quiz.title = quiz_data["title"]
    quiz.description = quiz_data["description"]
    quiz.save()

    for q in quiz_data["questions"]:
        Question.objects.create(
            quiz=quiz,
            question_title=q["question_title"],
            question_options=q["question_options"],
            answer=q["answer"],
        )

    return quiz


def generate_quiz_data_from_video(url: str, quiz_id: int = None) -> dict:
    """
    Helper function: Downloads audio, transcribes and generates quiz data (without modifying the DB).
    
    Return format:
      {"success": True, "data": {"title":..., "description":..., "questions": [...]}}
    or
      {"success": False, "error": "..."} 
    """
    result = download_audio_from_url(url, quiz_id=quiz_id)
    if not result.get("success"):
        return {"success": False, "error": result.get("error", "Download failed")}

    audio_path = result.get("filepath")

    transcript = run_whisper_transcription(audio_path)
    if not transcript or not transcript.strip():
        return {"success": False, "error": "Empty or failed transcript"}

    quiz_data = generate_quiz_with_gemini(transcript)

    if not isinstance(quiz_data, dict):
        return {"success": False, "error": "Invalid quiz format from Gemini"}

    questions = quiz_data.get("questions")
    if not questions or not isinstance(questions, list):
        return {"success": False, "error": "No questions generated"}

    for i, q in enumerate(questions):
        if not all(k in q for k in ("question_title", "question_options", "answer")):
            return {"success": False, "error": f"Frage {i} unvollständig"}

    return {"success": True, "data": quiz_data}
