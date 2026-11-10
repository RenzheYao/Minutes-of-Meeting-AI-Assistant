import os
import imageio_ffmpeg
import subprocess
import pytesseract

# 1. Configure Tesseract OCR path for Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
tesseract_exe = pytesseract.pytesseract.tesseract_cmd

# Robust patch for OpenAI Whisper on Windows to locate bundled ffmpeg
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
_original_init = subprocess.Popen.__init__

def _patched_init(self, args, *a, **kw):
    if isinstance(args, (list, tuple)) and len(args) > 0:
        if args[0] == "ffmpeg":
            args = list(args)
            args[0] = ffmpeg_exe
        elif args[0] == "tesseract":
            args = list(args)
            args[0] = tesseract_exe
    elif isinstance(args, str):
        if args.startswith("ffmpeg"):
            args = args.replace("ffmpeg", f'"{ffmpeg_exe}"', 1)
        elif args.startswith("tesseract"):
            args = args.replace("tesseract", f'"{tesseract_exe}"', 1)
            
    return _original_init(self, args, *a, **kw)

subprocess.Popen.__init__ = _patched_init

import sys
from flask import Flask, render_template, request, send_file, flash, redirect
from werkzeug.utils import secure_filename

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "meeting_suite"))

from main import run_pipeline

app = Flask(__name__)
app.secret_key = "super_secret_meeting_suite_key"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB limit

ALLOWED_MEDIA = {'mp3', 'wav', 'm4a', 'mp4', 'mkv', 'avi'}
ALLOWED_IMAGE = {'png', 'jpg', 'jpeg'}
ALLOWED_NOTES = {'txt', 'docx', 'pdf'}

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def extract_text_from_file(file_path):
    """Extracts text from TXT, DOCX, or PDF files."""
    ext = file_path.rsplit('.', 1)[1].lower()
    if ext == 'txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    elif ext == 'docx':
        from docx import Document
        return "\n".join([p.text for p in Document(file_path).paragraphs if p.text])
    elif ext == 'pdf':
        import pypdf
        reader = pypdf.PdfReader(file_path)
        return "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])
    return ""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        media_file = request.files.get("media_file")
        image_file = request.files.get("image_file")
        notes_file = request.files.get("notes_file")
        use_llm = request.form.get("use_llm") == "on"
        model_name = request.form.get("model_name", "gemma2:2b").strip()

        saved_media_path, saved_image_path, saved_notes_path = None, None, None

        if media_file and media_file.filename:
            if allowed_file(media_file.filename, ALLOWED_MEDIA):
                fn = secure_filename(media_file.filename)
                saved_media_path = os.path.join(app.config["UPLOAD_FOLDER"], fn)
                media_file.save(saved_media_path)

        if image_file and image_file.filename:
            if allowed_file(image_file.filename, ALLOWED_IMAGE):
                fn = secure_filename(image_file.filename)
                saved_image_path = os.path.join(app.config["UPLOAD_FOLDER"], fn)
                image_file.save(saved_image_path)

        if notes_file and notes_file.filename:
            if allowed_file(notes_file.filename, ALLOWED_NOTES):
                fn = secure_filename(notes_file.filename)
                raw_path = os.path.join(app.config["UPLOAD_FOLDER"], fn)
                notes_file.save(raw_path)

                extracted_text = extract_text_from_file(raw_path)
                saved_notes_path = os.path.join(app.config["UPLOAD_FOLDER"], "extracted_notes.txt")
                with open(saved_notes_path, "w", encoding="utf-8") as f:
                    f.write(extracted_text)

        if not (saved_media_path or saved_image_path or saved_notes_path):
            flash("Please upload at least one file!")
            return redirect(request.url)

        output_filename = "Generated_Meeting_Minutes.docx"
        output_docx_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)

        run_pipeline(
            media_file=saved_media_path,
            image_file=saved_image_path,
            notes_file=saved_notes_path,
            output_docx=output_docx_path,
            use_llm=use_llm,
            model_name=model_name
        )
        return send_file(output_docx_path, as_attachment=True, download_name=output_filename)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)