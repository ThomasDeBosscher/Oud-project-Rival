# Simple optional feature flag stub to "enable Claude Sonnet 4.5".
# No external API calls; purely illustrative.
import os

def is_enabled() -> bool:
    return os.getenv('ENABLE_CLAUDE', '0') == '1'

def generate_summary(text: str) -> str:
    if not is_enabled():
        return "(AI disabled)"
    # Placeholder deterministic pseudo "summary"
    words = text.split()
    if len(words) <= 20:
        return text
    return ' '.join(words[:20]) + ' ...'
