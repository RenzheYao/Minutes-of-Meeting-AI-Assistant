import os
import re
import argparse
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def parse_txt_to_mom_data(txt_path):
    mom_data = {
        "date": "N/A", "attendees": "N/A", "summary": "", "key_points": [], "action_items": []
    }
    if not os.path.exists(txt_path):
        return mom_data

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    current_section = None
    for line in lines:
        line_lower = line.lower()
        if "date:" in line_lower:
            mom_data["date"] = line.split(":", 1)[1].strip()
        elif "attendees:" in line_lower:
            mom_data["attendees"] = line.split(":", 1)[1].strip()
        elif "summary:" in line_lower:
            current_section = "summary"
            content = line.split(":", 1)[1].strip()
            if content: mom_data["summary"] += content + " "
        elif "key points:" in line_lower:
            current_section = "key_points"
        elif "action items:" in line_lower:
            current_section = "action_items"
        else:
            if current_section == "summary":
                mom_data["summary"] += line + " "
            elif current_section == "key_points":
                clean_line = re.sub(r'^[\*\-\d\.\s]+', '', line)
                if clean_line: mom_data["key_points"].append(clean_line)
            elif current_section == "action_items":
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    mom_data["action_items"].append({"task": parts[0], "owner": parts[1], "deadline": parts[2]})
                else:
                    clean_line = re.sub(r'^[\*\-\d\.\s]+', '', line)
                    mom_data["action_items"].append({"task": clean_line, "owner": "TBD", "deadline": "TBD"})

    return mom_data

def generate_mom_word_doc(txt_path, output_docx="Minutes_of_Meeting.docx"):
    data = parse_txt_to_mom_data(txt_path)
    doc = Document()

    # Set 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    NAVY = RGBColor(31, 78, 120)

    # Document Header
    p = doc.add_paragraph()
    r = p.add_run("MINUTES OF MEETING")
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = "Calibri", Pt(22), True, NAVY

    # Metadata Block
    table = doc.add_table(rows=2, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.rows[0].cells[0].text, table.rows[0].cells[1].text = "Date:", data["date"]
    table.rows[1].cells[0].text, table.rows[1].cells[1].text = "Attendees:", data["attendees"]

    for row in table.rows:
        for cell in row.cells:
            set_cell_background(cell, "F2F4F7")

    # Section 1: Executive Summary
    h1 = doc.add_paragraph()
    r1 = h1.add_run("1. Executive Summary")
    r1.font.name, r1.font.size, r1.font.bold, r1.font.color.rgb = "Calibri", Pt(14), True, NAVY
    doc.add_paragraph(data["summary"] or "Summary text here.")

    # Section 2: Key Discussion Points
    h2 = doc.add_paragraph()
    r2 = h2.add_run("2. Key Discussion Points")
    r2.font.name, r2.font.size, r2.font.bold, r2.font.color.rgb = "Calibri", Pt(14), True, NAVY
    for pt in data["key_points"]:
        doc.add_paragraph(pt, style='List Bullet')

    # Section 3: Action Items Table
    h3 = doc.add_paragraph()
    r3 = h3.add_run("3. Action Items")
    r3.font.name, r3.font.size, r3.font.bold, r3.font.color.rgb = "Calibri", Pt(14), True, NAVY

    act_table = doc.add_table(rows=1, cols=3)
    hdr = act_table.rows[0].cells
    for idx, name in enumerate(["Task / Description", "Owner", "Deadline"]):
        hdr[idx].text = name
        set_cell_background(hdr[idx], "1F4E78")
        hdr[idx].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        hdr[idx].paragraphs[0].runs[0].font.bold = True

    for item in data["action_items"]:
        row = act_table.add_row().cells
        row[0].text = item.get("task", "")
        row[1].text = item.get("owner", "TBD")
        row[2].text = item.get("deadline", "TBD")

    doc.save(output_docx)
    print(f"Generated: {output_docx}")
    return output_docx

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deterministic Word MoM Generator")
    parser.add_argument("txt_file", help="Path to meeting notes TXT file")
    parser.add_argument("--output", default="Minutes_of_Meeting.docx", help="Output DOCX file path")
    args = parser.parse_args()

    generate_mom_word_doc(args.txt_file, args.output)