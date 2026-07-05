"""
skill_router.py
Matches a user message against loaded Skills using keyword overlap —
no LLM call, near-zero latency cost. Returns None if nothing clears the
threshold, meaning: use core tools only, no skill injected.
"""

import re
from skill_loader import Skill

_STOPWORDS = {
    "the", "a", "an", "to", "of", "and", "or", "in", "on", "for", "is",
    "this", "that", "with", "use", "when", "user", "asks", "not",
    "you", "can", "give", "me", "please", "i", "my", "it", "so", "what",
    "if", "up", "then", "look", "check", "make",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z_]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def match_skill(user_message: str, skills: list[Skill], threshold: int = 1) -> Skill | None:
    msg_tokens = _tokenize(user_message)
    if not msg_tokens:
        return None

    best, best_score = None, 0
    for skill in skills:
        desc_tokens = _tokenize(skill.description) | _tokenize(skill.name)
        score = len(msg_tokens & desc_tokens)
        if score > best_score:
            best, best_score = skill, score

    return best if best_score >= threshold else None