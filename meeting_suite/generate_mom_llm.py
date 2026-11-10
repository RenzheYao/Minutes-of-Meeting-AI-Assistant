import os
import argparse
import ollama
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def prompt_local_llm_for_mom(notes_text="", transcript_text="", model_name="gemma2:2b"):
    system_prompt = """
    You are an expert executive project assistant. Your task is to analyze raw meeting notes/OCR and the audio transcript to synthesize a structured Minutes of Meeting (MoM).

    CRITICAL INSTRUCTIONS & GUARDRAILS:
    1. CONTENT RELEVANCE CHECK: First, evaluate the input text. If the uploaded content appears to be random noise, gibberish, music transcripts, or completely unrelated to a professional meeting or project discussion, DO NOT invent meeting minutes. Instead, output a clear warning starting with:
       "[WARNING: INVALID CONTENT]" followed by an explanation for human review.
    2. Compare notes and transcripts. If there are contradictions (e.g., conflicting dates, owners, deadlines), you MUST explicitly list them under '[CONTRADICTIONS & REVIEW NEEDED]'.
    3. Strictly follow the formatting structure shown in the example below.

    --- FORMATTING EXAMPLE ---
    [DATE & ATTENDEES]
    Date: October 12, 2026
    Attendees: Alice, Bob, Charlie

    [EXECUTIVE SUMMARY]
    The team reviewed the project milestone and addressed upcoming deployment risks.

    [KEY DISCUSSION POINTS]
    * Database migration needs to complete before Friday.
    * Server scaling limits were discussed.

    [DECISIONS & ACTION ITEMS]
    * Finalize database backup script | Alice | Oct 15
    * Update API documentation | Bob | Oct 18

    [CONTRADICTIONS & REVIEW NEEDED]
    * Notes state deployment is on Thursday, but audio transcript explicitly postponed it to next Monday.
    --------------------------
    """

    user_content = f"--- ROUGH NOTES / SLIDES ---\n{notes_text}\n\n--- AUDIO TRANSCRIPT ---\n{transcript_text}"

    print(f"Calling local LLM ('{model_name}') via Ollama...")
    response = ollama.chat(
        model=model_name,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_content}
        ]
    )
    return response['message']['content']

def export_llm_mom_to_docx(llm_output, output_docx="Minutes_of_Meeting_Draft.docx"):
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    NAVY = RGBColor(31, 78, 120)
    DARK_RED = RGBColor(156, 42, 42)

    # Handle Warning/Invalid content route if flagged by the LLM guardrail
    if "[WARNING: INVALID CONTENT]" in llm_output:
        p = doc.add_paragraph()
        r = p.add_run("⚠️ MEETING MINUTES - HUMAN REVIEW REQUIRED")
        r.font.name, r.font.size, r.font.bold, r.font.color.rgb = "Calibri", Pt(16), True, DARK_RED

        p_desc = doc.add_paragraph(llm_output)
        p_desc.style.font.name = "Calibri"
        p_desc.style.font.size = Pt(11)
        
        doc.save(output_docx)
        print(f"Generated Warning Review Notice: {output_docx}")
        return output_docx

    p = doc.add_paragraph()
    r = p.add_run("MINUTES OF MEETING (DRAFT - FOR HUMAN REVIEW)")
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = "Calibri", Pt(18), True, NAVY

    lines = llm_output.split('\n')
    current_section = None
    action_items_lines = []

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        if line_clean.startswith('[CONTRADICTIONS & REVIEW NEEDED]'):
            current_section = "CONTRADICTIONS"
            h = doc.add_paragraph()
            r = h.add_run("⚠️ CONTRADICTIONS & REVIEW NEEDED")
            r.font.name, r.font.size, r.font.bold, r.font.color.rgb = "Calibri", Pt(14), True, DARK_RED
        elif line_clean.startswith('[DECISIONS & ACTION ITEMS]'):
            current_section = "ACTION_ITEMS"
            h = doc.add_paragraph()
            r = h.add_run("Decisions & Action Items")
            r.font.name, r.font.size, r.font.bold, r.font.color.rgb = "Calibri", Pt(14), True, NAVY
        elif line_clean.startswith('['):
            current_section = "NORMAL"
            header_title = line_clean.replace('[', '').replace(']', '').title()
            h = doc.add_paragraph()
            r = h.add_run(header_title)
            r.font.name, r.font.size, r.font.bold, r.font.color.rgb = "Calibri", Pt(14), True, NAVY
        else:
            if current_section == "ACTION_ITEMS" and "|" in line_clean:
                action_items_lines.append(line_clean)
            elif current_section == "CONTRADICTIONS":
                p = doc.add_paragraph()
                r = p.add_run(line_clean)
                r.font.name, r.font.size = "Calibri", Pt(11)
                r.font.color.rgb = DARK_RED
            else:
                p = doc.add_paragraph(line_clean)
                p.style.font.name = "Calibri"
                p.style.font.size = Pt(11)

    if action_items_lines:
        act_table = doc.add_table(rows=1, cols=3)
        act_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr = act_table.rows[0].cells
        for idx, name in enumerate(["Task / Action Item", "Owner", "Deadline"]):
            hdr[idx].text = name
            set_cell_background(hdr[idx], "1F4E78")
            hdr[idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
            hdr[idx].paragraphs[0].runs[0].font.bold = True

        for item_line in action_items_lines:
            parts = [p.strip().lstrip('*').strip() for p in item_line.split("|")]
            row = act_table.add_row().cells
            row[0].text = parts[0] if len(parts) > 0 else ""
            row[1].text = parts[1] if len(parts) > 1 else "TBD"
            row[2].text = parts[2] if len(parts) > 2 else "TBD"

    doc.save(output_docx)
    print(f"Generated Draft MoM: {output_docx}")
    return output_docx