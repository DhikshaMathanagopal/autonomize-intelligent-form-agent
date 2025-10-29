import os, uuid, cv2, numpy as np
from PIL import Image
import pytesseract
from pypdf import PdfReader
from google.cloud import vision
import torch
from transformers import AutoProcessor, VisionEncoderDecoderModel

# -------------------------------
# OCR Layer: EasyOCR, Tesseract, Google Vision
# -------------------------------

try:
    # Lazy-load the EasyOCR Reader on first use to avoid startup downloads
    import easyocr
    _easy_reader = None
    HAS_EASYOCR = True
except Exception:
    _easy_reader = None
    HAS_EASYOCR = False


def _read_pdf_text(path):
    try:
        reader = PdfReader(path)
        return "\n".join([p.extract_text() or "" for p in reader.pages])
    except Exception:
        return ""


def _ocr_easyocr(img_path):
    global _easy_reader
    # Allow disabling via environment to speed startup or avoid large downloads
    if os.getenv("DISABLE_EASYOCR", "false").lower() == "true":
        return ""
    if not HAS_EASYOCR:
        return ""
    if _easy_reader is None:
        # Instantiate on first use
        _easy_reader = easyocr.Reader(["en"], gpu=False)
    return "\n".join(_easy_reader.readtext(img_path, detail=0, paragraph=True))


def _ocr_tesseract(img_path):
    img = cv2.imread(img_path)
    if img is None:
        img = cv2.cvtColor(np.array(Image.open(img_path)), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY)
    return pytesseract.image_to_string(thresh)


def _ocr_google_vision(img_path):
    try:
        client = vision.ImageAnnotatorClient()
        with open(img_path, "rb") as f:
            image = vision.Image(content=f.read())
        response = client.text_detection(image=image)
        if response.error.message:
            raise Exception(response.error.message)
        return "\n".join([d.description for d in response.text_annotations])
    except Exception as e:
        print(f"⚠️ Google Vision failed: {e}")
        return ""


# -------------------------------
# Donut (HF Vision-Language Model)
# -------------------------------

_donut_processor, _donut_model = None, None
HAS_DONUT = False

def _ensure_donut_loaded():
    global _donut_processor, _donut_model, HAS_DONUT
    if HAS_DONUT:
        return True
    if os.getenv("DISABLE_DONUT", "false").lower() == "true":
        return False
    try:
        _donut_processor = AutoProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa")
        _donut_model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-docvqa")
        HAS_DONUT = True
        return True
    except Exception as e:
        print("⚠️ Could not load Donut model:", e)
        _donut_processor, _donut_model, HAS_DONUT = None, None, False
        return False


# ===============================================================
# 1️⃣ Donut-based Visual QA — answers a specific question visually
# ===============================================================
def _donut_answer(form_image_path: str, question: str):
    """
    Donut-based visual reasoning for healthcare forms.
    Optimized for checkbox and handwritten detection.
    """
    if not _ensure_donut_loaded():
        return ""

    image = Image.open(form_image_path).convert("RGB")

    prompt = (
        f"<s_docvqa><s_question>{question.strip()}? "
        "Answer directly with the exact field, checkbox, or handwritten value seen on the form. "
        "Do not repeat the question or include any unrelated text.</s_question><s_answer>"
    )

    inputs = _donut_processor(images=image, text=prompt, return_tensors="pt").to("cpu")

    with torch.no_grad():
        output_ids = _donut_model.generate(
            **inputs,
            max_new_tokens=64,
            pad_token_id=_donut_processor.tokenizer.pad_token_id,
            num_beams=3,
            early_stopping=True,
        )

    result = _donut_processor.batch_decode(output_ids, skip_special_tokens=True)[0]
    result = result.replace("<s_docvqa>", "").replace("<s_question>", "").replace("</s_question>", "")
    result = result.replace("<s_answer>", "").replace("</s_answer>", "").strip()

    # 🧹 Clean result
    result = result.replace(question, "").replace("Answer:", "").strip()
    if len(result.split()) < 2 and not any(c.isalpha() for c in result):
        result = result.strip(":;,. ").capitalize()

    # 🩺 Special heuristic: if therapy-type text is found, return it
    therapies = ["Physical Therapy", "Occupational Therapy", "Speech Therapy", "Cardiac Rehab"]
    for t in therapies:
        if t.lower() in result.lower():
            return t

    # fallback if too generic
    if result.lower() in ["patient information", "information", "form", "document"]:
        return ""

    return result


# ===============================================================
# 2️⃣ Donut-based Structured Field Extraction — returns JSON
# ===============================================================
def _donut_extract_form_data(form_image_path: str):
    """
    Use Donut to extract structured key-value and checkbox data from a healthcare form.
    Returns a JSON-like dictionary of recognized fields.
    """
    if not _ensure_donut_loaded():
        return {}

    image = Image.open(form_image_path).convert("RGB")

    prompt = (
        "<s_docvqa><s_question>"
        "You are an intelligent form-understanding AI agent trained to interpret medical and administrative documents. "
        "Your goal is to extract all structured information visible on the form, including both printed text and handwritten or checkbox inputs. "
        "For every field label (like 'Therapy Type', 'Diagnosis', 'Provider', etc.), identify its corresponding value. "
        "If a checkbox or handwritten tick mark is visibly selected next to an option, treat that option as the field’s value. "
        "Do not ignore handwritten or ticked responses — they are the true answers for that field. "
        "Ignore empty boxes or unchecked fields. "
        "Return your output as a valid JSON object using clear key–value pairs, where keys are the field names and values are the detected answers. "
        "If a field has multiple checked boxes, return them as a list of selected values. "
        "Example output:\n"
        "{\n"
        '  \"Form Type\": \"Prior Authorization\",\n'
        '  \"Patient Name\": \"Jane Doe\",\n'
        '  \"Therapy Type\": \"Occupational Therapy\",\n'
        '  \"Diagnosis\": \"Salter-Harris Type\",\n'
        '  \"Services\": [\"Outpatient\", \"Home Health\"]\n'
        "}\n"
        "Now analyze the uploaded form carefully and return only the extracted JSON, nothing else."
        "</s_question><s_answer>"
    )

    inputs = _donut_processor(images=image, text=prompt, return_tensors="pt").to("cpu")
    with torch.no_grad():
        output_ids = _donut_model.generate(
            **inputs,
            max_new_tokens=256,
            pad_token_id=_donut_processor.tokenizer.pad_token_id,
            num_beams=3,
            early_stopping=True,
        )

    result = _donut_processor.batch_decode(output_ids, skip_special_tokens=True)[0]
    result = (
        result.replace("<s_docvqa>", "")
        .replace("<s_question>", "")
        .replace("</s_question>", "")
        .replace("<s_answer>", "")
        .replace("</s_answer>", "")
        .strip()
    )

    # Parse JSON-like text
    import re, json
    try:
        json_text = re.search(r"\{.*\}", result, re.DOTALL)
        if json_text:
            return json.loads(json_text.group(0))
    except Exception:
        pass

    return {"raw_text": result}


# ===============================================================
# 3️⃣ Combined Document Loader — integrates OCR + Donut fallback
# ===============================================================
def load_document_text(path):
    doc_id = os.path.basename(path) + "-" + str(uuid.uuid4())[:8]
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        text = _read_pdf_text(path)
        if text.strip():
            return doc_id, text
        # TODO: fallback to pdf2image if necessary

    else:
        if HAS_EASYOCR:
            try:
                return doc_id, _ocr_easyocr(path)
            except Exception:
                pass
        try:
            t_text = _ocr_tesseract(path)
            if t_text.strip():
                return doc_id, t_text
        except Exception:
            pass

        # final fallback: Google Vision OCR
        g_text = _ocr_google_vision(path)
        if g_text.strip():
            return doc_id, g_text

        # --- Visual fallback using Donut ---
        if _ensure_donut_loaded() and ("checkbox" in path.lower() or "form" in path.lower()):
            try:
                donut_answer = _donut_answer(path, "Extract all filled fields or marked options.")
                if donut_answer.strip():
                    return doc_id, donut_answer
            except Exception as e:
                print(f"⚠️ Donut fallback failed: {e}")

    return doc_id, ""
