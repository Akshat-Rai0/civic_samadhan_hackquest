from app.config import get_settings

SYSTEM_PROMPT = "in the given image tell me all the issue that needs to be fixed by municipal corp."

_model = None

def load_model():
    """Load the Moondream model. Called once at startup."""
    global _model
    settings = get_settings()
    # Model loading would happen here.
    # from moondream import Moondream
    # _model = Moondream.from_pretrained(settings.MOONDREAM_MODEL_PATH)
    _model = "stub"  # Replace with actual model when available

def analyze_image(image_path: str) -> list[str]:
    """Run Moondream on an image and return detected civic issues."""
    if _model is None:
        load_model()
    # Stub response for development. Replace with actual inference.
    # result = _model.query(image_path, SYSTEM_PROMPT)
    return ["pothole on road surface", "broken curb edge"]
