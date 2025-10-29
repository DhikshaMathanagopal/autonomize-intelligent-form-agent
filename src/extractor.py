import json
from openai import OpenAI
from config import can_use_openai, OPENAI_MODEL


# Ollama has been removed — extractor uses OpenAI when available, otherwise a deterministic fallback


# ------------------------
# Adaptive Field Extractor
# ------------------------
def extract_fields(form_text: str):
    """
    Extract fields adaptively from healthcare or administrative forms.
    1️⃣ Try with local Ollama model (for offline/local extraction)
    2️⃣ If extraction confidence is low, fallback to OpenAI GPT-4o-mini
    """

    # --- Adaptive prompt (your full original logic preserved) ---
    adaptive_prompt = f"""
You are an intelligent medical document parser.

Your task:
1. Identify what kind of form this is (e.g., "Texas Prior Authorization", "Claim Form", "Prescription", "Referral", etc.).
2. Extract ALL clearly labeled fields and their values from the document text.
3. Preserve the original field labels exactly as they appear (e.g., "NPI #", "Diagnosis Description", "Request Type").
4. If a field has multiple values (e.g., multiple diagnoses or providers), store them as a list.
5. Ignore instructions, headers, or footnotes unless they contain actual data.
6. If the field value is missing or empty, skip it entirely.
7. Return only valid JSON, structured as:
{{
  "form_type": "<detected form type>",
  "fields": {{
    "<field_label>": "<field_value>",
    "<field_label>": ["<value1>", "<value2>"]
  }}
}}

Example:
Input text:
"Form Type: Prior Authorization\nPatient Name: Jane Doe\nDOB: 12/01/1989\nDiagnosis: Diabetes\nProvider: Dr. Smith\nICD10: E11.9"

Expected output:
{{
  "form_type": "Prior Authorization",
  "fields": {{
    "Patient Name": "Jane Doe",
    "DOB": "12/01/1989",
    "Diagnosis": "Diabetes",
    "Provider": "Dr. Smith",
    "ICD10": "E11.9"
  }}
}}

Now extract all fields from this text:
<<<FORM TEXT>>>
{form_text}
<<<END FORM TEXT>>>
"""

    # 1) OpenAI path (preferred)
    data = {}
    if can_use_openai():
        try:
            client = OpenAI()
            r = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise medical form parser."},
                    {"role": "user", "content": adaptive_prompt}
                ],
                temperature=0.1
            )
            text = r.choices[0].message.content.strip()
            start, end = text.find("{"), text.rfind("}")
            if start != -1:
                try:
                    data = json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    data = {"form_type": "Unknown", "fields": {}, "raw_text": text}
        except Exception as e:
            print(f"⚠️ OpenAI extraction failed: {e}")
            data = {}

    # 2) Refinement with OpenAI if extraction was weak
    if (not data or len(data.get("fields", {})) < 3) and can_use_openai():
        print("🔁 Refining extraction with OpenAI GPT...")
        try:
            client = OpenAI()

            refine_prompt = f"""
Refine and complete this adaptive JSON extraction.
Ensure valid JSON structure and infer missing values only if explicitly stated.

Form Text:
{form_text[:4000]}

Partial JSON (if any):
{json.dumps(data, indent=2)}
"""
            r = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise medical form parser."},
                    {"role": "user", "content": refine_prompt}
                ],
                temperature=0.1
            )
            text = r.choices[0].message.content.strip()
            start, end = text.find("{"), text.rfind("}")
            if start != -1:
                try:
                    data = json.loads(text[start:end+1])
                except json.JSONDecodeError:
                    data = {"form_type": "Unknown", "fields": {}, "raw_text": text}
        except Exception as e:
            print(f"⚠️ OpenAI refinement failed: {e}")
            # Keep existing data or set minimal structure
            if not data:
                data = {"form_type": "Unknown", "fields": {}}

    # 3) Guarantee “fields” shape; if no OpenAI, return minimal structure
    if "fields" not in data:
        # flatten nested if necessary
        flat_fields = {}
        for k, v in data.items():
            if isinstance(v, dict):
                for subk, subv in v.items():
                    flat_fields[f"{k.title()} {subk.title()}"] = subv
            elif k != "form_type":
                flat_fields[k.title()] = v

        data = {
            "form_type": data.get("form_type", "Unknown"),
            "fields": flat_fields
        }

    return data
