import os
import yt_dlp
import whisper
from django.conf import settings
from google import genai
import json

from quiz_app.models import Question


def download_audio_from_url(url: str, output_dir: str = "/tmp") -> dict:
    """
    Lädt Audio über yt-dlp herunter und gibt Metadaten zurück.
    
    Args:
        url (str): Die Video-URL.
        output_dir (str): Zielverzeichnis (default: /tmp).
        
    Returns:
        dict: Enthält 'filepath', 'title' und 'success' (bool).
    """
    if not url:
        return {"success": False, "error": "No URL provided."}

    # Sicherstellen, dass der Ordner existiert
    os.makedirs(output_dir, exist_ok=True)

    # Dynamisches Ausgabeformat
    outtmpl = os.path.join(output_dir, "%(title)s.%(ext)s")

    # yt-dlp Optionen zusammenbauen
    ydl_opts = {**settings.YDL_BASE_OPTS, "outtmpl": outtmpl}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        return {
            "success": True,
            "filepath": filepath,
            "title": info.get("title"),
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
    

def run_whisper_transcription(audio_path: str) -> str:
    """
    Führt Whisper lokal aus (z. B. small oder medium Modell).
    """
    try:
        model = whisper.load_model("small")
        result = model.transcribe(audio_path, language="de")
        return result["text"]
    except Exception as e:
        print(f"Whisper-Fehler: {e}")
        return ""
    

def generate_quiz_with_gemini(transcript: str) -> dict:
    """
    Übergibt das Transkript an Gemini und erhält strukturiertes Quiz zurück.
    """
    if not transcript.strip():
        return {"title": "Fehler", "description": "Kein Transkript vorhanden", "questions": []}

    prompt = f"""
    Erstelle auf Grundlage des folgenden Videotranskripts ein Quiz.
    
    Anforderungen:
    - Erstelle 10 Multiple-Choice-Fragen.
    - Jede Frage hat genau 4 Antwortoptionen.
    - Gib die Antwort im folgenden JSON-Format zurück:

    {{
      "title": "Titel des Quizzes",
      "description": "Kurze Beschreibung",
      "questions": [
        {{
          "question_title": "...",
          "question_options": ["...", "...", "...", "..."],
          "answer": "..."
        }}
      ]
    }}

    Transkript:
    {transcript[:12000]}  # Beschränke Länge, damit das Prompt nicht zu groß wird
    """

    try:
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        raw_output = response.text.strip()

        # Versuche JSON zu extrahieren
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            # Wenn das Modell Text mit JSON mischt → nach JSON-Anteil suchen
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(raw_output[start:end])
            else:
                raise ValueError("Gemini-Ausgabe war kein valides JSON.")

    except Exception as e:
        print(f"Gemini-Fehler: {e}")
        return {
            "title": "Fehlerhafte Generierung",
            "description": str(e),
            "questions": [],
        }    

    

def generate_quiz_from_video(quiz):
    # 1️⃣ Audio laden
    result = download_audio_from_url(quiz.video_url)
    if not result["success"]:
        quiz.title = "Fehler beim Download"
        quiz.save()
        return

    audio_path = result["filepath"]

    # 2️⃣ Whisper: Transkription
    transcript = run_whisper_transcription(audio_path)

    # 3️⃣ Gemini: Quizdaten generieren
    quiz_data = generate_quiz_with_gemini(transcript)

    # 4️⃣ DB aktualisieren
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
