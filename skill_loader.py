"""
skills_loader.py
Parses skills/*.md into Skill objects: name, description (routing signal),
body (procedure text injected when matched), gated_groups (which optional
tool tiers this skill needs — 'mcp', 'web', 'paper').
"""

import os
import re
from dataclasses import dataclass, field


@dataclass
class Skill:
    name: str
    description: str
    body: str
    gated_groups: set = field(default_factory=set)


def _parse_frontmatter(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    fm_text, body = m.groups()
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


_GATE_KEYWORDS = {
    "mcp": ["mcp", "context7", "docs-lookup"],
    "web": ["web_search", "web search"],
    "paper": ["paper_tools", "paper-research", "paper search"],
}


def _detect_gated_groups(body: str) -> set:
    m = re.search(r"Gated.*?:\s*(.*)", body)
    gated_line = m.group(1).lower() if m else ""
    return {
        group
        for group, keywords in _GATE_KEYWORDS.items()
        if any(kw in gated_line for kw in keywords)
    }


def load_skills(skills_dir: str) -> list[Skill]:
    skills = []
    if not os.path.isdir(skills_dir):
        return skills
    for fname in sorted(os.listdir(skills_dir)):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(skills_dir, fname), "r", encoding="utf-8") as f:
            text = f.read()
        fm, body = _parse_frontmatter(text)
        if "name" not in fm or "description" not in fm:
            continue
        skills.append(Skill(
            name=fm["name"],
            description=fm["description"],
            body=body.strip(),
            gated_groups=_detect_gated_groups(body),
        ))
    return skills