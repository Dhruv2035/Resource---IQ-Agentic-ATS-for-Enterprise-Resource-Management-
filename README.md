# Agentic ATS
### Multimodal Layout Parsing & Dynamic Skill Gap Simulation for Intelligent Resume Optimization

A capstone project: upload a resume (PDF/DOCX/TXT), get an ATS-friendliness score, a
keyword/skill match against a job description, formatting/layout red flags, and a
**dynamic skill-gap simulator** that predicts how your score would change if you learned
specific missing skills. Also supports comparing **multiple resume sets** side by side.

- **Backend:** Python (FastAPI) — does the real work: layout-aware parsing, ATS scoring, skill-gap simulation.
- **Frontend:** plain HTML/CSS/JS (no build step) — opens directly in Chrome, talks to the backend over `fetch`.
- **No paid/external AI API required** — everything runs locally and offline.

---

## 1. Project structure

```
agentic-ats/
├── backend/
│   ├── main.py            # FastAPI app + API routes (also serves the frontend)
│   ├── parser.py           # Multimodal layout parser (PDF/DOCX/TXT, + OCR fallback)
│   ├── ats_scorer.py        # ATS scoring: keywords, formatting, sections
│   ├── skill_gap.py         # Dynamic skill-gap "what-if" simulation engine
│   ├── skills_db.py         # Offline skill taxonomy used for matching
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── README.md
```

## 2. Setup in VS Code

1. Open the `agentic-ats` folder in VS Code (`File > Open Folder…`).
2. Open a terminal in VS Code (`` Ctrl+` ``) and create a virtual environment:

   ```bash
   cd backend
   python -m venv venv
   ```

   Activate it:
   - **Windows:** `venv\Scripts\activate`
   - **macOS/Linux:** `source venv/bin/activate`

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   > OCR (`pytesseract`) is optional and only used as a fallback for scanned/image-only
   > resumes. If you don't want it, remove the last two lines of `requirements.txt` and
   > delete the `try/except` OCR block usage in `parser.py` — the app works fine without it.

4. Run the backend:

   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. Open **Chrome** and go to:

   ```
   http://127.0.0.1:8000
   ```

   FastAPI serves the frontend directly, so this single URL is the whole app —
   no separate frontend server needed.

## 3. How to use it

- **Tab 1 — Scan Resume:** Drag a resume in, optionally paste a job description (or click
  one of the sample JD chips), click **Scan & Analyze**. You'll get an overall score ring,
  a keyword/formatting/section breakdown, matched vs. missing skills, layout red flags, and
  a ranked skill-gap roadmap chart.
- **Tab 2 — Compare Sets:** Upload multiple resume versions (or multiple candidates) and one
  job description — get a ranked comparison table across all of them.
- **Tab 3 — Skill Simulator:** After scanning a resume in Tab 1, come here to hand-pick
  missing skills and instantly preview the projected score change — the "what if I learn X"
  simulation.

## 4. What "multimodal layout parsing" means here

Most resume checkers only read plain text. This project also reads the document's **visual
layout** using PyMuPDF (for PDFs) and python-docx (for Word files):

- font sizes/variety → detects inconsistent formatting
- block x/y positions → detects multi-column layouts (a common ATS parsing failure)
- embedded images/icons → flags graphics that ATS engines can't read
- tables → flags content ATS engines frequently scramble
- OCR fallback → if a PDF has no selectable text (i.e. it's a scanned image), it falls back
  to Tesseract OCR so it can still extract *something*, while flagging this as a major issue.

## 5. What "dynamic skill gap simulation" means here

`skill_gap.py` doesn't just list missing skills — it **simulates** the marginal ATS-score
impact of learning each one individually, ranks them into a prioritized roadmap, and (in
Tab 3) lets you pick a custom combination of skills to preview a projected before/after score,
similar to a lightweight "agentic what-if" planner.

## 6. Extending it further (ideas for the report/viva)

- Swap the offline `skills_db.py` taxonomy for a live O*NET / ESCO skills API.
- Add a resume rewrite suggester (bullet-point rewriting) as a 4th tab.
- Persist scan history per user with a small SQLite database.
- Add authentication + multi-user support for a recruiter-facing "Compare Sets" mode.
