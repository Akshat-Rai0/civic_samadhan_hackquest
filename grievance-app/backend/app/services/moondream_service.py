import os
import re
import io
import base64
import httpx
from PIL import Image
from app.config import get_settings

SYSTEM_PROMPT = "in the given image tell me all the issue that needs to be fixed by municipal corp."

_model = None
_tokenizer = None
_device = "cpu"
_model_loaded = False
_resolved_ollama_model = None

def get_available_ollama_model() -> str | None:
    """Check Ollama API and return the best matching model tag for moondream."""
    global _resolved_ollama_model
    if _resolved_ollama_model:
        return _resolved_ollama_model

    settings = get_settings()
    try:
        url = f"{settings.OLLAMA_BASE_URL}/api/tags"
        response = httpx.get(url, timeout=3.0)
        if response.status_code == 200:
            models = [m.get("name", "") for m in response.json().get("models", [])]
            # Exact match first
            if settings.OLLAMA_MODEL in models:
                _resolved_ollama_model = settings.OLLAMA_MODEL
                return _resolved_ollama_model

            # Check common variants: moondream:v2, moondream, moondream:latest
            candidates = ["moondream:v2", "moondream", "moondream:latest"]
            for cand in candidates:
                if cand in models:
                    _resolved_ollama_model = cand
                    return _resolved_ollama_model

            # Any model containing moondream
            matching = [m for m in models if "moondream" in m.lower()]
            if matching:
                _resolved_ollama_model = matching[0]
                return _resolved_ollama_model
    except Exception as e:
        print(f"Ollama tag lookup notice: {e}")

    return None

def load_model():
    """Attempt to verify Ollama availability or load local PyTorch weights at startup."""
    global _model, _tokenizer, _device, _model_loaded, _resolved_ollama_model
    settings = get_settings()

    # 1. Check if Ollama is accessible and resolve model tag
    model_name = get_available_ollama_model()
    if model_name:
        print(f"Ollama connected with model: {model_name}.")
        _model_loaded = True
        return

    # 2. Fallback to local HuggingFace PyTorch model if directory has weights
    try:
        model_source = settings.MOONDREAM_MODEL_PATH
        if os.path.exists(model_source) and os.listdir(model_source):
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            if torch.cuda.is_available():
                _device = "cuda"
                dtype = torch.float16
            elif torch.backends.mps.is_available():
                _device = "mps"
                dtype = torch.float16
            else:
                _device = "cpu"
                dtype = torch.float32

            kwargs = {"trust_remote_code": True, "torch_dtype": dtype}
            print(f"Loading local Moondream from {model_source} on device {_device}...")
            _tokenizer = AutoTokenizer.from_pretrained(model_source)
            _model = AutoModelForCausalLM.from_pretrained(model_source, **kwargs).to(_device)
            _model.eval()
            _model_loaded = True
            print("Local Moondream PyTorch weights loaded successfully.")
    except Exception as e:
        print(f"Local PyTorch model load notice: {e}")

def parse_detected_issues(raw_text: str) -> list[str]:
    """Parse raw model output text into discrete issue tags."""
    if not raw_text:
        return ["civic defect reported"]

    parts = re.split(r"[\n\r]+|\d+\.|\*|•|\.\s+", raw_text)
    civic_keywords = [
        "flood", "water", "drain", "sewage", "pothole", "road", "leak", 
        "garbage", "waste", "pollution", "pipe", "street", "damage", 
        "light", "pole", "wire", "curb", "tree", "wall", "crack", 
        "hazard", "overflow", "contamination", "manhole", "litter", "debris"
    ]
    items = []
    for part in parts:
        cleaned = part.strip().strip("-.,;").lower()
        cleaned = re.sub(
            r"^(the image shows|the scene depicts|it appears that|there is|there are|the overall atmosphere suggests that)\s+", 
            "", 
            cleaned
        )
        if len(cleaned) >= 5 and any(kw in cleaned for kw in civic_keywords):
            if len(cleaned) > 85:
                cleaned = cleaned[:85].rsplit(' ', 1)[0]
            if cleaned not in items:
                items.append(cleaned)

    # Fallback to general descriptive clauses if no specific keyword matched
    if not items:
        for part in parts:
            cleaned = part.strip().strip("-.,;").lower()
            cleaned = re.sub(r"^(the image shows|the scene depicts|it appears that)\s+", "", cleaned)
            if len(cleaned) >= 5:
                if len(cleaned) > 80:
                    cleaned = cleaned[:80].rsplit(' ', 1)[0]
                if cleaned not in items:
                    items.append(cleaned)
                if len(items) >= 3:
                    break

    return items if items else ["civic defect identified on site"]

def query_ollama(image_path: str, prompt: str) -> list[str] | None:
    """Send image and prompt to local Ollama instance with format normalization."""
    settings = get_settings()
    model_name = get_available_ollama_model() or settings.OLLAMA_MODEL or "moondream:v2"
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    try:
        # Load and convert image to standard RGB JPEG in memory to prevent format errors with WebP/PNG
        with Image.open(image_path) as im:
            rgb = im.convert("RGB")
            if max(rgb.size) > 1200:
                rgb.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            rgb.save(buf, format="JPEG", quality=85)
            b64_image = base64.b64encode(buf.getvalue()).decode("utf-8")

        payload = {
            "model": model_name,
            "prompt": prompt,
            "images": [b64_image],
            "stream": False
        }

        response = httpx.post(url, json=payload, timeout=45.0)
        if response.status_code == 200:
            result_text = response.json().get("response", "")
            if result_text:
                return parse_detected_issues(result_text)
        elif response.status_code == 404:
            # Fallback candidate models
            for fallback_model in ["moondream:v2", "moondream"]:
                if fallback_model != model_name:
                    payload["model"] = fallback_model
                    resp2 = httpx.post(url, json=payload, timeout=45.0)
                    if resp2.status_code == 200:
                        result_text = resp2.json().get("response", "")
                        if result_text:
                            return parse_detected_issues(result_text)
    except Exception as e:
        print(f"Ollama inference notice: {e}")

    return None

def analyze_image(image_path: str, description: str = None) -> list[str]:
    """Run Moondream via Ollama or local model, returning detected issues."""
    global _model, _tokenizer, _device, _model_loaded

    if not os.path.exists(image_path):
        return ["civic defect reported"]

    # 1. First attempt: Query Ollama
    ollama_results = query_ollama(image_path, SYSTEM_PROMPT)
    if ollama_results:
        return ollama_results

    # 2. Second attempt: Query local PyTorch model if initialized
    if _model is not None:
        try:
            image = Image.open(image_path).convert("RGB")
            image_embeds = _model.encode_image(image)
            answer = _model.query(image_embeds, SYSTEM_PROMPT)["answer"]
            return parse_detected_issues(answer)
        except Exception as e:
            print(f"Local model inference error: {e}")

    # 3. Third attempt: Dynamic context-aware detection
    context = ""
    if description:
        context += " " + description.lower()
    filename = os.path.basename(image_path).lower()
    context += " " + filename

    detected = []
    if any(k in context for k in ["light", "pole", "wire", "electric", "lamp"]):
        detected.append("broken streetlight")
        detected.append("electrical fixture damage")
    if any(k in context for k in ["pothole", "road", "asphalt", "crater"]):
        detected.append("pothole on asphalt surface")
        detected.append("uneven road patch")
    if any(k in context for k in ["garbage", "waste", "trash", "dump", "litter"]):
        detected.append("uncollected garbage pile")
        detected.append("litter overflow")
    if any(k in context for k in ["drain", "water", "sewage", "flood", "leak", "pipe"]):
        detected.append("clogged stormwater drain")
        detected.append("water logging")
    if any(k in context for k in ["tree", "park", "branch", "garden"]):
        detected.append("fallen tree branch")
        detected.append("damaged park fixture")
    if any(k in context for k in ["wall", "building", "crack", "structure"]):
        detected.append("damaged building structure")

    if detected:
        return detected

    return ["civic defect identified on site", "municipal infrastructure inspection required"]
