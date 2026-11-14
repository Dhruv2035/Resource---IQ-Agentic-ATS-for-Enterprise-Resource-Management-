"""
main.py
Agentic ATS backend.

Run with:  uvicorn main:app --reload --port 8000
Then open: http://127.0.0.1:8000  in Chrome
"""

from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from parser import parse_resume
from ats_scorer import compute_full_report, extract_skills
from skill_gap import simulate_skill_gap, simulate_custom_addition

app = FastAPI(title="Agentic ATS", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


# ---------- request/response models ----------

class SimulateCustomRequest(BaseModel):
    resume_skills: List[str]
    jd_text: str
    skills_to_add: List[str]


# ---------- helpers ----------

def _read_upload(file: UploadFile) -> bytes:
    content = file.file.read()
    if not content:
        raise HTTPException(status_code=400, detail=f"'{file.filename}' is empty.")
    return content


# ---------- API routes ----------

@app.post("/api/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(""),
):
    """Parse one resume + score it against an optional job description."""
    try:
        file_bytes = _read_upload(resume)
        parsed = parse_resume(resume.filename, file_bytes)
        report = compute_full_report(parsed, job_description)
        gap = simulate_skill_gap(set(report["resume_skills"]), set(report["jd_skills"]))

        return {
            "filename": resume.filename,
            "layout_flags": parsed["layout_flags"],
            "sections_found": list(parsed["sections_found"].keys()),
            "report": report,
            "skill_gap_simulation": gap,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze resume: {e}")


@app.post("/api/compare")
async def compare_resumes(
    resumes: List[UploadFile] = File(...),
    job_description: str = Form(""),
):
    """Multiple-sets comparison: analyze several resumes against the same
    job description and rank them side by side."""
    if len(resumes) < 2:
        raise HTTPException(status_code=400, detail="Upload at least 2 resumes to compare.")

    results = []
    for resume in resumes:
        try:
            file_bytes = _read_upload(resume)
            parsed = parse_resume(resume.filename, file_bytes)
            report = compute_full_report(parsed, job_description)
            results.append({
                "filename": resume.filename,
                "overall_score": report["overall_score"],
                "keyword_match_pct": report["keyword_match"]["score"],
                "formatting_score": report["formatting"]["score"],
                "section_score": report["sections"]["score"],
                "matched_skills": report["keyword_match"]["matched"],
                "missing_skills": report["keyword_match"]["missing"],
                "issues": report["formatting"]["issues"],
            })
        except Exception as e:
            results.append({"filename": resume.filename, "error": str(e)})

    ranked = sorted(
        [r for r in results if "error" not in r],
        key=lambda r: r["overall_score"],
        reverse=True,
    )
    for i, r in enumerate(ranked, start=1):
        r["rank"] = i

    failed = [r for r in results if "error" in r]
    return {"ranked_results": ranked, "failed": failed}


@app.post("/api/simulate")
async def simulate_addition(payload: SimulateCustomRequest):
    """Let the user hand-pick skills to 'add' and preview the new score
    (the dynamic what-if simulation)."""
    jd_skills = extract_skills(payload.jd_text)
    result = simulate_custom_addition(
        set(s.lower() for s in payload.resume_skills),
        jd_skills,
        payload.skills_to_add,
    )
    return result


@app.get("/api/sample-job-descriptions")
async def sample_job_descriptions():
    return {
        "samples": [
            {
                "title": "Backend Python Developer",
                "text": (
                    "We are hiring a Backend Python Developer. Required skills: Python, "
                    "FastAPI or Django, SQL, PostgreSQL, Docker, Git, REST API design, AWS. "
                    "Nice to have: Kubernetes, CI/CD, Redis. The ideal candidate has strong "
                    "problem solving and communication skills and experience with agile "
                    "project management."
                ),
            },
            {
                "title": "Data Scientist",
                "text": (
                    "Looking for a Data Scientist skilled in Python, Pandas, NumPy, "
                    "scikit-learn, machine learning and deep learning. Experience with "
                    "TensorFlow or PyTorch, SQL, and data analysis required. Tableau or "
                    "Power BI is a plus. Strong communication skills needed to present "
                    "findings to stakeholders."
                ),
            },
            {
                "title": "Frontend / Full-Stack Engineer",
                "text": (
                    "Full-Stack Engineer needed with strong JavaScript / TypeScript, React, "
                    "Node.js, and REST API experience. Familiarity with Git, Docker, "
                    "MongoDB or PostgreSQL, and CI/CD pipelines. UI/UX sensibility and "
                    "Figma familiarity a plus. Must work well in an agile team."
                ),
            },
        ]
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ---------- serve the frontend (so opening http://127.0.0.1:8000 in Chrome just works) ----------

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
