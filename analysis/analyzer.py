import json
import re
from datetime import datetime
from rag.llm_interface import llm_generate

# -----------------------------
# JSON Extraction
# -----------------------------
def extract_json(text):
    """
    Extract the first valid JSON block from LLM response.
    Attempts to fix minor formatting issues.
    """
    try:
        # First try direct load
        return json.loads(text)
    except:
        # Fallback: regex to find JSON block
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                return {"error": "Failed to parse JSON even after regex extraction", "raw_output": text}
        else:
            return {"error": "No JSON found", "raw_output": text}


# -----------------------------
# Date Normalization
# -----------------------------
def normalize_dates(phases):
    for p in phases:
        for key in ["Start_Date", "End_Date"]:
            if key in p and p[key]:
                try:
                    # Try ISO format first
                    dt = datetime.strptime(p[key], "%Y-%m-%d")
                except:
                    try:
                        # Try common alternate format
                        dt = datetime.strptime(p[key], "%d/%m/%Y")
                    except:
                        dt = None
                if dt:
                    p[key] = dt.strftime("%Y-%m-%d")
                else:
                    p[key] = "1970-01-01"  # fallback default
    return phases


# -----------------------------
# Budget Fixing
# -----------------------------
def fix_budgets(data):
    # Ensure Timeline exists
    if "Timeline" not in data:
        data["Timeline"] = {"Phases": [], "Total_Duration_Days": 0}
    if "Phases" not in data["Timeline"]:
        data["Timeline"]["Phases"] = []

    phases = data["Timeline"]["Phases"]

    # Ensure Cost_Estimate exists
    cost_estimate = data.get("Cost_Estimate", {}).get("Amount", 0)
    if not cost_estimate or cost_estimate <= 0:
        cost_estimate = 1_000_000  # placeholder budget

    # Ensure each phase has Duration_Days
    for p in phases:
        if "Duration_Days" not in p or not isinstance(p["Duration_Days"], (int, float)):
            p["Duration_Days"] = 1

    # Normalize dates
    phases = normalize_dates(phases)

    # Compute total duration
    total_days = sum(p.get("Duration_Days", 1) for p in phases) or 1

    # Distribute budget across phases
    for p in phases:
        p["Estimated_Budget"] = round(cost_estimate * (p["Duration_Days"] / total_days), 2)

    data["Timeline"]["Phases"] = phases
    data["Timeline"]["Total_Duration_Days"] = total_days
    data["Cost_Estimate"] = {"Amount": cost_estimate, "Currency": "INR", "Estimated": True}

    return data


# -----------------------------
# Main RFP Analysis Function
# -----------------------------
def analyze_rfp(file_name, file_text, llm_generate):
    prompt = f"""
You are an AI assistant analyzing an RFP document.

Return ONLY a valid JSON object. 
Do not include explanations, markdown, comments, or text outside JSON.

The JSON must follow this structure:

{{
  "Project_Type": "...",
  "Scope": {{
    "Objectives": [...],
    "Description": "..."
  }},
  "Deliverables": [...],
  "Required_Skills": [...],
  "Tasks_Roles": [
    {{
      "Role": "...",
      "Tasks": [...]
    }}
  ],
  "Timeline": {{
    "Phases": [
      {{
        "Phase": "...",
        "Start_Date": "YYYY-MM-DD",
        "End_Date": "YYYY-MM-DD",
        "Duration_Days": ...,
        "Estimated_Budget": ...
      }}
    ],
    "Total_Duration_Days": ...
  }},
  "Cost_Estimate": {{
    "Amount": ...,
    "Currency": "INR",
    "Estimated": true
  }},
  "RFP_File": "{file_name}"
}}

⚠️ Rules:
- No empty task lists. Remove roles with empty tasks.
- No zero budgets. If missing → distribute placeholder budget of 1,000,000 INR across phases.
- Normalize dates to YYYY-MM-DD.
- Ensure valid JSON only.

RFP text:

{file_text}
"""

    response = llm_generate(prompt, max_tokens=2000)
    data = extract_json(response)

    # If JSON extraction failed
    if isinstance(data, dict) and data.get("error"):
        return data

    # Fix budgets, dates, and empty fields
    data = fix_budgets(data)

    # Remove roles with empty tasks
    if "Tasks_Roles" in data:
        data["Tasks_Roles"] = [r for r in data["Tasks_Roles"] if r.get("Tasks")]

    return data
