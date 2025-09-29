import os
import json
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def export_json(all_analyses, output_folder="data/processed_json", base_name="multi_rfp_analysis"):
    os.makedirs(output_folder, exist_ok=True)
    save_path = os.path.join(output_folder, base_name + ".json")
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(all_analyses, f, indent=2, ensure_ascii=False)
    return save_path

def export_excel(all_analyses, output_folder="data/processed_json", base_name="multi_rfp_analysis"):
    os.makedirs(output_folder, exist_ok=True)
    save_path = os.path.join(output_folder, base_name + ".xlsx")
    writer = pd.ExcelWriter(save_path, engine='xlsxwriter')
    
    for analysis in all_analyses:
        sheet_name = analysis["RFP_File"][:31]  # Excel sheet name limit
        rows = []
        rows.append(["Project Type", analysis.get("Project_Type", "")])
        rows.append(["Scope", str(analysis.get("Scope", ""))])
        rows.append(["Deliverables", ", ".join(analysis.get("Deliverables", []))])
        rows.append(["Required Skills", ", ".join(analysis.get("Required_Skills", []))])
        rows.append(["Total Duration", analysis.get("Timeline", {}).get("Total_Duration_Days", 0)])
        rows.append(["Total Budget", analysis.get("Cost_Estimate", {}).get("Amount", 0)])
        df = pd.DataFrame(rows, columns=["Field", "Value"])
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    writer.save()
    return save_path

def export_pdf(all_analyses, output_folder="data/processed_json", base_name="multi_rfp_analysis"):
    os.makedirs(output_folder, exist_ok=True)
    save_path = os.path.join(output_folder, base_name + ".pdf")
    doc = SimpleDocTemplate(save_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    for analysis in all_analyses:
        story.append(Paragraph(f"<b>{analysis.get('RFP_File')}</b>", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>Project Type:</b> {analysis.get('Project_Type', 'N/A')}", styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Scope</b>", styles["Heading2"]))
        story.append(Paragraph(str(analysis.get("Scope", {})), styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Deliverables</b>", styles["Heading2"]))
        for d in analysis.get("Deliverables", []):
            story.append(Paragraph(f"- {d}", styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Required Skills</b>", styles["Heading2"]))
        for s in analysis.get("Required_Skills", []):
            story.append(Paragraph(f"- {s}", styles["Normal"]))
        story.append(Spacer(1, 12))
        if "Cost_Estimate" in analysis:
            story.append(Paragraph("<b>Cost Estimate</b>", styles["Heading2"]))
            story.append(Paragraph(str(analysis["Cost_Estimate"]), styles["Normal"]))
            story.append(Spacer(1, 12))
    
    doc.build(story)
    return save_path
