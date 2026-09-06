import os
import logging

logger = logging.getLogger(__name__)

def is_translation_enabled() -> bool:
    val = os.environ.get("TRANSLATION_ENABLED", "true").strip().lower()
    return val in ("true", "1", "yes", "on")

def translate_text(text: str, target_lang: str) -> str:
    """
    Translates text to target_lang using googletrans.
    Returns original text if translation is disabled, fails, or empty.
    """
    if not text or not text.strip():
        return text

    if not is_translation_enabled():
        return text

    target = (target_lang or "en").strip().lower()

    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, dest=target)
        if result and hasattr(result, 'text') and result.text:
            return result.text
        return text
    except Exception as e:
        logger.warning(f"Translation failed for '{text[:30]}...' to '{target}': {e}")
        return text

