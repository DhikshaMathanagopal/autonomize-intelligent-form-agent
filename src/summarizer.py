from config import can_use_openai, OPENAI_MODEL, USE_OPENAI_ONLY
from openai import OpenAI

def summarize_doc(fields, full_text):
    # Limit input size for latency; fields usually carry the key signal
    MAX_TEXT_CHARS = 1500
    clipped_text = (full_text or "")[:MAX_TEXT_CHARS]

    prompt = f"""
    Summarize this medical form into 5 concise bullet points.
    Keep the answer under 120 words total.
    Fields: {fields}
    Text: {clipped_text}
    """
    if can_use_openai():
        try:
            client = OpenAI()
            r = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role":"user","content":prompt}],
                temperature=0.2,
                max_tokens=220
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ OpenAI summarization failed: {e}")

    # Prepare fast fallback summary (used when LLMs fail or unavailable)
    key_fields = []
    try:
        key_fields = [
            f"Form Type: {fields.get('form_type')}" if isinstance(fields, dict) and fields.get('form_type') else None,
        ]
        # Flatten first few fields for brevity
        if isinstance(fields, dict):
            fld = fields.get('fields') if 'fields' in fields else fields
            if isinstance(fld, dict):
                cnt = 0
                for k, v in fld.items():
                    if cnt >= 4:
                        break
                    key_fields.append(f"{k}: {v}")
                    cnt += 1
    except Exception:
        pass
    bullet_lines = ["- " + s for s in [x for x in key_fields if x]]

    # If OpenAI-only is requested, return fast fallback immediately
    if USE_OPENAI_ONLY:
        return "\n".join(bullet_lines) or "Summary unavailable (OpenAI not configured)."
    
    # Fast deterministic fallback (always available)
    return "\n".join(bullet_lines) or "Summary unavailable (no LLM service available)."
