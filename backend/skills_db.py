"""
skills_db.py
Lightweight skill taxonomy used by the ATS engine.
Each skill maps to a category + a list of synonyms/aliases that might
appear in a resume or job description in slightly different wording.
This keeps the project fully offline (no external API / paid NLP service
required) while still giving reasonably smart matching.
"""

SKILLS_DB = {
    # ---------------- Programming Languages ----------------
    "python": {"category": "Programming Language", "aliases": ["python3", "py"]},
    "java": {"category": "Programming Language", "aliases": ["core java", "j2ee"]},
    "javascript": {"category": "Programming Language", "aliases": ["js", "es6", "ecmascript"]},
    "typescript": {"category": "Programming Language", "aliases": ["ts"]},
    "c++": {"category": "Programming Language", "aliases": ["cpp"]},
    "c#": {"category": "Programming Language", "aliases": ["csharp", "c sharp"]},
    "sql": {"category": "Programming Language", "aliases": ["structured query language"]},
    "r": {"category": "Programming Language", "aliases": []},
    "go": {"category": "Programming Language", "aliases": ["golang"]},

    # ---------------- Web / Frameworks ----------------
    "react": {"category": "Framework", "aliases": ["react.js", "reactjs"]},
    "angular": {"category": "Framework", "aliases": ["angularjs"]},
    "vue": {"category": "Framework", "aliases": ["vue.js", "vuejs"]},
    "node.js": {"category": "Framework", "aliases": ["node", "nodejs", "express.js", "express"]},
    "django": {"category": "Framework", "aliases": []},
    "flask": {"category": "Framework", "aliases": []},
    "fastapi": {"category": "Framework", "aliases": ["fast api"]},
    "spring boot": {"category": "Framework", "aliases": ["spring"]},

    # ---------------- Data / AI ----------------
    "machine learning": {"category": "Data/AI", "aliases": ["ml"]},
    "deep learning": {"category": "Data/AI", "aliases": ["dl", "neural networks"]},
    "natural language processing": {"category": "Data/AI", "aliases": ["nlp"]},
    "pandas": {"category": "Data/AI", "aliases": []},
    "numpy": {"category": "Data/AI", "aliases": []},
    "tensorflow": {"category": "Data/AI", "aliases": ["tf"]},
    "pytorch": {"category": "Data/AI", "aliases": ["torch"]},
    "scikit-learn": {"category": "Data/AI", "aliases": ["sklearn"]},
    "data analysis": {"category": "Data/AI", "aliases": ["data analytics"]},
    "power bi": {"category": "Data/AI", "aliases": ["powerbi"]},
    "tableau": {"category": "Data/AI", "aliases": []},

    # ---------------- Cloud / DevOps ----------------
    "aws": {"category": "Cloud/DevOps", "aliases": ["amazon web services"]},
    "azure": {"category": "Cloud/DevOps", "aliases": ["microsoft azure"]},
    "gcp": {"category": "Cloud/DevOps", "aliases": ["google cloud", "google cloud platform"]},
    "docker": {"category": "Cloud/DevOps", "aliases": ["containerization"]},
    "kubernetes": {"category": "Cloud/DevOps", "aliases": ["k8s"]},
    "ci/cd": {"category": "Cloud/DevOps", "aliases": ["cicd", "continuous integration", "continuous deployment"]},
    "git": {"category": "Cloud/DevOps", "aliases": ["github", "gitlab", "version control"]},
    "linux": {"category": "Cloud/DevOps", "aliases": ["unix"]},

    # ---------------- Database ----------------
    "mysql": {"category": "Database", "aliases": []},
    "postgresql": {"category": "Database", "aliases": ["postgres"]},
    "mongodb": {"category": "Database", "aliases": ["mongo", "nosql"]},
    "redis": {"category": "Database", "aliases": []},

    # ---------------- Soft Skills ----------------
    "communication": {"category": "Soft Skill", "aliases": ["communication skills"]},
    "leadership": {"category": "Soft Skill", "aliases": ["team leadership"]},
    "teamwork": {"category": "Soft Skill", "aliases": ["collaboration", "team player"]},
    "problem solving": {"category": "Soft Skill", "aliases": ["problem-solving"]},
    "project management": {"category": "Soft Skill", "aliases": ["agile", "scrum"]},
    "time management": {"category": "Soft Skill", "aliases": []},

    # ---------------- Design ----------------
    "figma": {"category": "Design", "aliases": []},
    "ui/ux": {"category": "Design", "aliases": ["ux design", "ui design", "user experience"]},
}

# Standard ATS-friendly resume section headers (used for the layout / structure checks)
STANDARD_SECTIONS = [
    "summary", "objective", "experience", "work experience", "employment history",
    "education", "skills", "technical skills", "projects", "certifications",
    "achievements", "contact",
]

# Words/phrases considered generic filler that hurts keyword density if overused
BUZZWORDS = ["hardworking", "team player", "detail oriented", "go-getter", "synergy", "self-starter"]
