"""
ats_scorer.py
Computes an overall ATS-friendliness + job-match score for a parsed resume.

Score = 0.60 * keyword_match_score + 0.25 * formatting_score + 0.15 * section_score
(weights are intentionally simple/transparent so the project stays explainable)
"""

import re
from typing import Any, Dict, List, Set

from skills_db import SKILLS_DB, STANDARD_SECTIONS, BUZZWORDS


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def extract_skills(text: str) -> Set[str]:
    """Return the canonical skill names found in a block of text."""
    norm = _normalize(text)
    found = set()
    for skill, meta in SKILLS_DB.items():
        candidates = [skill] + meta["aliases"]
        for c in candidates:
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(c.lower()) + r"(?![a-zA-Z0-9])"
            if re.search(pattern, norm):
                found.add(skill)
                break
    return found


def count_buzzwords(text: str) -> List[str]:
    norm = _normalize(text)
    return [b for b in BUZZWORDS if b in norm]


def score_formatting(layout_flags: Dict[str, Any]) -> Dict[str, Any]:
    """0-100 score based on layout red flags that break real-world ATS parsers."""
    score = 100
    issues = []

    if layout_flags.get("possible_multi_column"):
        score -= 25
        issues.append("Multi-column layout detected — many ATS engines read columns left-to-right across the whole line and scramble your content.")

    if layout_flags.get("has_images_or_icons"):
        score -= 15
        issues.append("Images/icons detected — ATS engines cannot read text embedded in graphics (e.g. skill icons, profile photo).")

    if layout_flags.get("has_tables"):
        score -= 15
        issues.append("Table layout detected — content inside tables is frequently misread or dropped by ATS parsers.")

    if layout_flags.get("used_ocr_fallback"):
        score -= 20
        issues.append("Resume appears to be a scanned image with no selectable text — most ATS software cannot read this at all.")

    font_variety = layout_flags.get("font_size_variety", 0)
    if font_variety and font_variety > 8:
        score -= 10
        issues.append("Too many distinct font sizes — this usually means inconsistent formatting that looks unprofessional and can confuse parsers.")

    page_count = layout_flags.get("page_count")
    if page_count and page_count > 2:
        score -= 10
        issues.append(f"Resume is {page_count} pages — keep it to 1-2 pages for most roles.")

    score = max(0, min(100, score))
    return {"score": score, "issues": issues}


def score_sections(sections_found: Dict[str, int]) -> Dict[str, Any]:
    """Checks presence of core resume sections ATS engines look for."""
    core_required = ["experience", "education", "skills"]
    normalized_found = set(sections_found.keys())

    # allow synonyms (e.g. "work experience" counts as "experience")
    synonym_map = {
        "experience": ["experience", "work experience", "employment history"],
        "education": ["education"],
        "skills": ["skills", "technical skills"],
    }

    missing = []
    present_count = 0
    for req, alts in synonym_map.items():
        if any(a in normalized_found for a in alts):
            present_count += 1
        else:
            missing.append(req)

    score = round((present_count / len(synonym_map)) * 100)
    return {"score": score, "missing_sections": missing}


def score_keyword_match(resume_skills: Set[str], jd_skills: Set[str]) -> Dict[str, Any]:
    if not jd_skills:
        return {"score": 0, "matched": [], "missing": []}
    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)
    score = round((len(matched) / len(jd_skills)) * 100)
    return {"score": score, "matched": matched, "missing": missing}


def compute_full_report(parsed_resume: Dict[str, Any], job_description: str) -> Dict[str, Any]:
    resume_text = parsed_resume["raw_text"]
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_description) if job_description else set()

    keyword_report = score_keyword_match(resume_skills, jd_skills)
    formatting_report = score_formatting(parsed_resume["layout_flags"])
    section_report = score_sections(parsed_resume["sections_found"])
    buzzwords = count_buzzwords(resume_text)

    if jd_skills:
        overall = round(
            0.60 * keyword_report["score"]
            + 0.25 * formatting_report["score"]
            + 0.15 * section_report["score"]
        )
    else:
        # No JD supplied -> pure resume-quality score (formatting + sections + skill richness)
        richness = min(100, len(resume_skills) * 8)
        overall = round(0.4 * formatting_report["score"] + 0.3 * section_report["score"] + 0.3 * richness)

    return {
        "overall_score": overall,
        "resume_skills": sorted(resume_skills),
        "jd_skills": sorted(jd_skills),
        "keyword_match": keyword_report,
        "formatting": formatting_report,
        "sections": section_report,
        "buzzwords_found": buzzwords,
        "word_count": len(resume_text.split()),
    }
