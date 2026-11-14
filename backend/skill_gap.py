"""
skill_gap.py
Dynamic Skill Gap Simulation.

Given the resume's current skill set and a job description's required
skill set, this module simulates "what happens to my ATS score if I add
skill X" for every missing skill, and returns a ranked, prioritized
learning roadmap (highest score-impact first). This is the "agentic"
what-if simulation layer described in the project title -- it doesn't
just report a gap, it explores the decision space of which skills are
worth closing first.
"""

from typing import Any, Dict, List, Set

from skills_db import SKILLS_DB


def _category_weight(skill: str) -> float:
    """Skills central to the role's tech stack get slightly more simulated
    weight than generic soft skills, so the roadmap prioritizes sensibly."""
    category = SKILLS_DB.get(skill, {}).get("category", "")
    weights = {
        "Programming Language": 1.15,
        "Framework": 1.1,
        "Data/AI": 1.1,
        "Cloud/DevOps": 1.05,
        "Database": 1.0,
        "Design": 1.0,
        "Soft Skill": 0.8,
    }
    return weights.get(category, 1.0)


def simulate_skill_gap(resume_skills: Set[str], jd_skills: Set[str]) -> Dict[str, Any]:
    resume_skills = set(resume_skills)
    jd_skills = set(jd_skills)

    if not jd_skills:
        return {
            "current_match_pct": 0,
            "missing_skills": [],
            "roadmap": [],
            "projected_scores": [],
        }

    total = len(jd_skills)
    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    current_match_pct = round((len(matched) / total) * 100)

    # simulate adding each missing skill individually to estimate its
    # marginal impact on the keyword-match score
    impact_list = []
    for skill in missing:
        weight = _category_weight(skill)
        marginal_gain = round((1 / total) * 100 * weight, 1)
        impact_list.append({
            "skill": skill,
            "category": SKILLS_DB.get(skill, {}).get("category", "General"),
            "estimated_score_gain": marginal_gain,
        })

    # rank by biggest impact first -> this is the prioritized learning roadmap
    impact_list.sort(key=lambda x: x["estimated_score_gain"], reverse=True)

    # simulate cumulative "what if I close the top N gaps" trajectory
    projected_scores = []
    running_score = current_match_pct
    for i, item in enumerate(impact_list, start=1):
        running_score = min(100, round(running_score + item["estimated_score_gain"], 1))
        projected_scores.append({
            "after_adding": item["skill"],
            "cumulative_skills_added": i,
            "projected_match_pct": running_score,
        })

    return {
        "current_match_pct": current_match_pct,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "roadmap": impact_list,
        "projected_scores": projected_scores,
    }


def simulate_custom_addition(resume_skills: Set[str], jd_skills: Set[str], skills_to_add: List[str]) -> Dict[str, Any]:
    """Let the user hand-pick a set of skills (e.g. from a course they're
    considering) and see the projected new match score immediately."""
    resume_skills = set(resume_skills)
    jd_skills = set(jd_skills)
    skills_to_add = set(s.lower() for s in skills_to_add)

    if not jd_skills:
        return {"before_pct": 0, "after_pct": 0, "newly_covered": []}

    before = round((len(resume_skills & jd_skills) / len(jd_skills)) * 100)
    simulated_resume_skills = resume_skills | skills_to_add
    after = round((len(simulated_resume_skills & jd_skills) / len(jd_skills)) * 100)
    newly_covered = sorted((simulated_resume_skills & jd_skills) - (resume_skills & jd_skills))

    return {
        "before_pct": before,
        "after_pct": after,
        "score_delta": after - before,
        "newly_covered": newly_covered,
    }
