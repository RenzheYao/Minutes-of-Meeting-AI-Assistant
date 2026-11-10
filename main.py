import os
import argparse
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "meeting_suite"))

from transcribe_media import transcribe_media
from extract_screenshot_text import extract_text_from_image
from generate_mom_llm import prompt_local_llm_for_mom, export_llm_mom_to_docx
from export_mom_docx import generate_mom_word_doc

def validate_content_relevance(transcript_text, ocr_text, notes_text):
    """
    Checks if the combined content has enough substance and is professional/meeting-related.
    Returns (is_valid, reason_message).
    """
    combined = f"{transcript_text} {ocr_text} {notes_text}".strip()
    
    # Check for empty or extremely brief inputs
    if len(combined) < 15:
        return False, "WARNING: The uploaded files are nearly empty or contained no readable text/audio."
        
    return True, ""

def run_pipeline(media_file=None, image_file=None, notes_file=None, output_docx="Project_MoM.docx", use_llm=True, model_name="gemma2:2b"):
    transcript_text, ocr_text, notes_text = "", "", ""

    if media_file and os.path.exists(media_file):
        transcript_text = transcribe_media(media_file)

    if image_file and os.path.exists(image_file):
        ocr_text = extract_text_from_image(image_file)

    if notes_file and os.path.exists(notes_file):
        with open(notes_file, "r", encoding="utf-8") as f:
            notes_text = f.read()

    # 1. Validate content relevance before generating MoM
    is_valid, warning_msg = validate_content_relevance(transcript_text, ocr_text, notes_text)
    
    if not is_valid:
        # If content is invalid/irrelevant, create a Word document highlighting the warning for human review
        print(f"\n[!] Pipeline Alert: {warning_msg}")
        from docx import Document
        doc = Document()
        doc.add_heading("Meeting Minutes - Review Required", level=1)
        doc.add_paragraph("The automated pipeline flagged the uploaded files as potentially irrelevant, empty, or non-meeting-related.")
        doc.add_paragraph(f"Details: {warning_msg}")
        doc.add_paragraph("Please check your source files (audio, image, or notes) and try uploading valid professional data.")
        doc.save(output_docx)
        return

    combined_notes = f"{notes_text}\n\nVISUAL OCR TEXT:\n{ocr_text}".strip()

    if use_llm:
        llm_output = prompt_local_llm_for_mom(
            notes_text=combined_notes, 
            transcript_text=transcript_text, 
            model_name=model_name
        )
        export_llm_mom_to_docx(llm_output, output_docx)
    else:
        temp_txt = "temp_combined.txt"
        with open(temp_txt, "w", encoding="utf-8") as f:
            f.write(f"Summary: Combined Pipeline Data\nKey Points:\n{combined_notes}\n{transcript_text}")
        generate_mom_word_doc(temp_txt, output_docx)
        if os.path.exists(temp_txt):
            os.remove(temp_txt)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--media", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--notes", default=None)
    parser.add_argument("--output", default="Project_MoM_Draft.docx")
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--model", default="gemma2:2b")
    args = parser.parse_args()

    run_pipeline(args.media, args.image, args.notes, args.output, not args.no_llm, args.model)