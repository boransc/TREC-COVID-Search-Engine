import html
import re

def normalize_tokens(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9-]+", text or "")]


def highlight_terms(text: str, query_terms: list[str]) -> str:
    escaped = html.escape(text or "")
    unique_terms = sorted({t for t in query_terms if len(t) > 1}, key=len, reverse=True)
    if not unique_terms:
        return escaped
    pattern = r"\\b(" + "|".join(re.escape(t) for t in unique_terms) + r")\\b"
    return re.sub(pattern, r"<mark>\\1</mark>", escaped, flags=re.IGNORECASE)


def build_snippet(abstract: str, query_terms: list[str]) -> str:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\\s+", abstract or "") if s.strip()]
    if not sentences:
        return "No abstract available."

    best_sentence = sentences[0]
    best_score = -1
    for sentence in sentences:
        score = sum(1 for t in query_terms if t in sentence.lower())
        if score > best_score:
            best_score = score
            best_sentence = sentence

    return highlight_terms(best_sentence, query_terms)