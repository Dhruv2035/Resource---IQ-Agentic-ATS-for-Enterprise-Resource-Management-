const API_BASE = ""; // same-origin: FastAPI serves this file, so relative paths work

// ---------------- Tabs ----------------
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("panel-" + btn.dataset.tab).classList.add("active");
  });
});

// ---------------- Sample job descriptions ----------------
async function loadSampleJDs() {
  try {
    const res = await fetch(`${API_BASE}/api/sample-job-descriptions`);
    const data = await res.json();
    const container = document.getElementById("jdSamples");
    data.samples.forEach(s => {
      const chip = document.createElement("span");
      chip.className = "jd-sample-chip";
      chip.textContent = s.title;
      chip.addEventListener("click", () => {
        document.getElementById("jdInputSingle").value = s.text;
      });
      container.appendChild(chip);
    });
  } catch (e) {
    console.warn("Could not load sample JDs (backend not running yet?)", e);
  }
}
loadSampleJDs();

// ---------------- Dropzone helper ----------------
function wireDropzone(zoneId, inputId, onFiles, multiple) {
  const zone = document.getElementById(zoneId);
  const input = document.getElementById(inputId);
  zone.addEventListener("click", () => input.click());
  input.addEventListener("change", () => onFiles(multiple ? Array.from(input.files) : input.files[0]));

  ["dragenter", "dragover"].forEach(evt =>
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.add("drag"); })
  );
  ["dragleave", "drop"].forEach(evt =>
    zone.addEventListener(evt, e => { e.preventDefault(); zone.classList.remove("drag"); })
  );
  zone.addEventListener("drop", e => {
    const files = Array.from(e.dataTransfer.files);
    if (!multiple) { onFiles(files[0]); input.files = e.dataTransfer.files; }
    else { onFiles(files); }
  });
}

// ---------------- TAB 1: Analyze ----------------
let singleFile = null;
wireDropzone("dropzoneSingle", "fileInputSingle", (file) => {
  singleFile = file;
  document.getElementById("dzFileNameSingle").textContent = file ? `Selected: ${file.name}` : "";
}, false);

let lastReport = null; // stored so the Simulator tab can reuse resume skills

document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const statusEl = document.getElementById("analyzeStatus");
  if (!singleFile) { setStatus(statusEl, "Please choose a resume file first.", "error"); return; }

  const form = new FormData();
  form.append("resume", singleFile);
  form.append("job_description", document.getElementById("jdInputSingle").value || "");

  setStatus(statusEl, "Scanning layout & extracting skills…", "");
  toggleBtn("analyzeBtn", true);

  try {
    const res = await fetch(`${API_BASE}/api/analyze`, { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Analysis failed.");
    setStatus(statusEl, "Done.", "ok");
    renderAnalyzeResults(data);
    lastReport = data;
    populateSimulatorFromLastReport();
  } catch (e) {
    setStatus(statusEl, e.message, "error");
  } finally {
    toggleBtn("analyzeBtn", false);
  }
});

function setStatus(el, msg, cls) {
  el.textContent = msg;
  el.className = "status-line" + (cls ? " " + cls : "");
}
function toggleBtn(id, disabled) {
  const b = document.getElementById(id);
  b.disabled = disabled;
  b.textContent = disabled ? "Working…" : (id === "analyzeBtn" ? "Scan & Analyze" : (id === "compareBtn" ? "Compare Sets" : "Run Simulation"));
}

function renderAnalyzeResults(data) {
  document.getElementById("emptyState").classList.add("hidden");
  document.getElementById("resultsContent").classList.remove("hidden");

  const report = data.report;
  document.getElementById("scoreHeroFile").textContent = data.filename;
  document.getElementById("scoreRingLabel").textContent = report.overall_score;
  drawScoreRing(report.overall_score);

  setBar("barKeyword", "valKeyword", report.keyword_match.score);
  setBar("barFormat", "valFormat", report.formatting.score);
  setBar("barSection", "valSection", report.sections.score);

  const matchedWrap = document.getElementById("matchedSkills");
  const missingWrap = document.getElementById("missingSkills");
  matchedWrap.innerHTML = "";
  missingWrap.innerHTML = "";

  const matched = report.keyword_match.matched.length ? report.keyword_match.matched : report.resume_skills;
  matched.forEach(s => matchedWrap.appendChild(makeChip(s)));
  if (!matched.length) matchedWrap.innerHTML = `<span class="muted">None detected</span>`;

  const missing = report.keyword_match.missing;
  missing.forEach(s => missingWrap.appendChild(makeChip(s, true)));
  if (!missing.length) missingWrap.innerHTML = `<span class="muted">${report.jd_skills.length ? "No gaps — full match!" : "Add a job description to see gaps"}</span>`;

  const issuesList = document.getElementById("issuesList");
  issuesList.innerHTML = "";
  const allIssues = [...report.formatting.issues];
  if (report.sections.missing_sections.length) {
    allIssues.push(`Missing standard section(s): ${report.sections.missing_sections.join(", ")}.`);
  }
  if (report.buzzwords_found.length) {
    allIssues.push(`Overused generic buzzwords found: ${report.buzzwords_found.join(", ")} — replace with quantified achievements.`);
  }
  if (!allIssues.length) allIssues.push("No major formatting red flags detected. Nicely structured resume.");
  allIssues.forEach(i => {
    const li = document.createElement("li");
    li.textContent = i;
    issuesList.appendChild(li);
  });

  renderRoadmapChart(data.skill_gap_simulation);
}

function makeChip(text, missing) {
  const span = document.createElement("span");
  span.className = "chip" + (missing ? " missing" : "");
  span.textContent = text;
  return span;
}

function setBar(barId, valId, score) {
  document.getElementById(barId).style.width = score + "%";
  document.getElementById(valId).textContent = score + "%";
}

let scoreRingChart = null;
function drawScoreRing(score) {
  const ctx = document.getElementById("scoreRing").getContext("2d");
  if (scoreRingChart) scoreRingChart.destroy();
  const color = score >= 75 ? "#00C896" : score >= 45 ? "#F2A93B" : "#E4573D";
  scoreRingChart = new Chart(ctx, {
    type: "doughnut",
    data: { datasets: [{ data: [score, 100 - score], backgroundColor: [color, "#EEF1F5"], borderWidth: 0 }] },
    options: { cutout: "78%", plugins: { legend: { display: false }, tooltip: { enabled: false } }, animation: { duration: 700 } },
  });
}

let roadmapChartInstance = null;
function renderRoadmapChart(gap) {
  const canvas = document.getElementById("roadmapChart");
  if (roadmapChartInstance) roadmapChartInstance.destroy();
  if (!gap || !gap.roadmap || !gap.roadmap.length) {
    canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);
    return;
  }
  const labels = gap.roadmap.map(r => r.skill);
  const values = gap.roadmap.map(r => r.estimated_score_gain);
  roadmapChartInstance = new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: {
      labels,
      datasets: [{ label: "Estimated ATS score gain if learned (%)", data: values, backgroundColor: "#00C896", borderRadius: 6 }],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, grid: { color: "#EEF1F5" } }, y: { grid: { display: false } } },
    },
  });
}

// ---------------- TAB 2: Compare ----------------
let multiFiles = [];
wireDropzone("dropzoneMulti", "fileInputMulti", (files) => {
  multiFiles = files;
  const wrap = document.getElementById("multiFileList");
  wrap.innerHTML = "";
  files.forEach(f => {
    const pill = document.createElement("span");
    pill.className = "file-pill";
    pill.textContent = f.name;
    wrap.appendChild(pill);
  });
}, true);

document.getElementById("compareBtn").addEventListener("click", async () => {
  const statusEl = document.getElementById("compareStatus");
  if (multiFiles.length < 2) { setStatus(statusEl, "Please choose at least 2 resumes.", "error"); return; }

  const form = new FormData();
  multiFiles.forEach(f => form.append("resumes", f));
  form.append("job_description", document.getElementById("jdInputMulti").value || "");

  setStatus(statusEl, "Scanning all resume sets…", "");
  toggleBtn("compareBtn", true);

  try {
    const res = await fetch(`${API_BASE}/api/compare`, { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Comparison failed.");
    setStatus(statusEl, `Ranked ${data.ranked_results.length} resume(s).`, "ok");
    renderCompareTable(data);
  } catch (e) {
    setStatus(statusEl, e.message, "error");
  } finally {
    toggleBtn("compareBtn", false);
  }
});

function renderCompareTable(data) {
  document.getElementById("compareEmptyState").classList.add("hidden");
  const wrap = document.getElementById("compareTableWrap");
  wrap.classList.remove("hidden");

  let html = `<table class="compare-table"><thead><tr>
    <th>Rank</th><th>File</th><th>Overall</th><th>Keyword</th><th>Format</th><th>Sections</th><th>Top missing skills</th>
  </tr></thead><tbody>`;

  data.ranked_results.forEach(r => {
    html += `<tr>
      <td><span class="rank-badge">${r.rank}</span></td>
      <td>${escapeHtml(r.filename)}</td>
      <td><span class="score-pill">${r.overall_score}</span></td>
      <td>${r.keyword_match_pct}%</td>
      <td>${r.formatting_score}%</td>
      <td>${r.section_score}%</td>
      <td>${r.missing_skills.slice(0, 5).join(", ") || "—"}</td>
    </tr>`;
  });

  data.failed.forEach(r => {
    html += `<tr><td>—</td><td>${escapeHtml(r.filename)}</td><td colspan="5" style="color:#B23A22;">Error: ${escapeHtml(r.error)}</td></tr>`;
  });

  html += `</tbody></table>`;
  wrap.innerHTML = html;
}

function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

// ---------------- TAB 3: Simulate ----------------
let simResumeSkills = [];
let simJdText = "";
let simPicked = new Set();

function populateSimulatorFromLastReport() {
  if (!lastReport) return;
  simResumeSkills = lastReport.report.resume_skills;
  simJdText = document.getElementById("jdInputSingle").value || "";

  const curWrap = document.getElementById("simCurrentSkills");
  curWrap.innerHTML = "";
  simResumeSkills.forEach(s => curWrap.appendChild(makeChip(s)));
  if (!simResumeSkills.length) curWrap.innerHTML = `<span class="muted">None detected</span>`;

  const jdWrap = document.getElementById("simJdSkills");
  jdWrap.innerHTML = "";
  lastReport.report.jd_skills.forEach(s => jdWrap.appendChild(makeChip(s)));
  if (!lastReport.report.jd_skills.length) jdWrap.innerHTML = `<span class="muted">No job description was provided</span>`;

  const pickerWrap = document.getElementById("simMissingSkillsPicker");
  pickerWrap.innerHTML = "";
  simPicked = new Set();
  lastReport.report.keyword_match.missing.forEach(s => {
    const chip = document.createElement("span");
    chip.className = "chip selectable";
    chip.textContent = s;
    chip.addEventListener("click", () => {
      if (simPicked.has(s)) { simPicked.delete(s); chip.classList.remove("picked"); }
      else { simPicked.add(s); chip.classList.add("picked"); }
    });
    pickerWrap.appendChild(chip);
  });
  if (!lastReport.report.keyword_match.missing.length) {
    pickerWrap.innerHTML = `<span class="muted">No skill gaps to simulate — great match already!</span>`;
  }
}

document.getElementById("simulateBtn").addEventListener("click", async () => {
  const statusEl = document.getElementById("simulateStatus");
  if (!simJdText) { setStatus(statusEl, "Scan a resume with a job description in Tab 1 first.", "error"); return; }
  if (!simPicked.size) { setStatus(statusEl, "Pick at least one skill to simulate.", "error"); return; }

  setStatus(statusEl, "Simulating…", "");
  toggleBtn("simulateBtn", true);

  try {
    const res = await fetch(`${API_BASE}/api/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_skills: simResumeSkills,
        jd_text: simJdText,
        skills_to_add: Array.from(simPicked),
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Simulation failed.");
    setStatus(statusEl, "Done.", "ok");

    document.getElementById("simResult").classList.remove("hidden");
    document.getElementById("simBefore").textContent = data.before_pct + "%";
    document.getElementById("simAfter").textContent = data.after_pct + "%";
    document.getElementById("simDelta").textContent =
      `Adding ${Array.from(simPicked).join(", ")} would newly cover: ${data.newly_covered.join(", ") || "—"} ` +
      `(${data.score_delta >= 0 ? "+" : ""}${data.score_delta}% keyword match).`;
  } catch (e) {
    setStatus(statusEl, e.message, "error");
  } finally {
    toggleBtn("simulateBtn", false);
  }
});
