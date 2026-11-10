========================================================================
                 DETERMINISTIC MEETING SUITE - README
========================================================================

A 100% local, private, and deterministic automation pipeline for meeting
documentation (Minutes of Meeting - MoM).

This suite processes audio/video recordings, visual screenshots/slides,
and manual notes locally on your hardware. It uses OpenAI Whisper for
speech-to-text, Tesseract OCR for visual text extraction, Ollama
(Gemma 2B / Llama 3) for structured synthesis and contradiction tracking,
and Python-Docx to generate professional, styled Word documents (.docx).

------------------------------------------------------------------------
1. PROJECT ARCHITECTURE
------------------------------------------------------------------------

meeting_suite_flask/
│
├── app_flask.py              # Flask Web Server & UI routing
├── main.py                   # Master Pipeline Orchestrator
├── requirements.txt          # Package dependencies
├── templates/
│   └── index.html            # Web interface frontend
└── meeting_suite/            # Core modular processing scripts
    ├── transcribe_media.py        # Local Whisper Audio/Video transcription
    ├── extract_screenshot_text.py # Local Tesseract OCR wrapper
    ├── generate_mom_llm.py        # Local LLM synthesis & contradiction logging
    └── export_mom_docx.py         # Rule-based Word generator fallback

------------------------------------------------------------------------
2. PREREQUISITES & SETUP
------------------------------------------------------------------------

System Dependencies:
  - Python 3.10 or higher
  - Ollama installed and running locally (`ollama serve`)
  - Local LLM model downloaded (e.g., `ollama pull gemma2:2b`)
  - System binaries for FFmpeg (for Whisper) and Tesseract-OCR

Virtual Environment Setup (Windows / VS Code):
  1. Open terminal in project folder.
  2. Create virtual environment:
     python -m venv venv
  3. Activate environment:
     .\venv\Scripts\Activate.ps1
  4. Install Python dependencies:
     pip install -r requirements.txt

------------------------------------------------------------------------
3. HOW TO RUN THE SUITE
------------------------------------------------------------------------

METHOD A: Flask Web Interface (Recommended)
  1. Start the Flask server:
     python app_flask.py
  2. Open browser to: http://localhost:5000
  3. Upload your files:
     - Audio/Video: .mp3, .wav, .m4a, .mp4, .mkv
     - Screenshots: .png, .jpg, .jpeg
     - Rough Notes: .txt, .docx, .pdf
  4. Click "Export Minutes of Meeting (.docx)" to download the draft.

METHOD B: Command-Line Interface (CLI)
  Run directly via terminal arguments:
  python main.py --media meeting.mp4 --image slides.png --notes notes.txt --output MoM.docx

  Available CLI Flags:
    --media   : Path to audio/video file
    --image   : Path to screenshot/slide
    --notes   : Path to text notes file
    --output  : Custom output DOCX path
    --model   : Local Ollama model name (default: gemma2:2b)
    --no-llm  : Disable LLM synthesis and run pure rule-based fallback

------------------------------------------------------------------------
4. PRIVACY & CONTRADICTION LOGGING
------------------------------------------------------------------------

  - 100% Offline: Zero data leaves your computer.
  - Human-in-the-Loop Validation: Contradictory information between
    written notes and spoken audio (e.g., conflicting dates or owners)
    is explicitly flagged in red under a "CONTRADICTIONS & REVIEW NEEDED"
    section for quick review by a project manager.
========================================================================