import os
import yt_dlp
from django.conf import settings

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
