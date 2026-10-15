const evidenceInput = document.querySelector("#evidence");
const charCount = document.querySelector("#char-count");
const analyzeButton = document.querySelector("#analyze-button");
const errorMessage = document.querySelector("#error-message");
const emptyState = document.querySelector("#empty-state");
const loadingState = document.querySelector("#loading-state");
const analysisResults = document.querySelector("#analysis-results");
const resultsPanel = document.querySelector("#results-panel");

const exampleEvidence = `Source: observed evidence from the LinkWatch repository.

Repository: LinkWatch

Finding: Runtime dependency compatibility failure involving Jinja2 and MarkupSafe.

Dependency declarations:
- requirements.txt pins Jinja2==2.11.3.
- pyproject.toml pins Jinja2==2.11.3.
- Neither dependency file directly pins MarkupSafe.

Baseline test results:
- Installed Jinja2 version: 2.11.3.
- Installed MarkupSafe version: 3.0.4.
- Tests: 9 passed, 1 failed.
- Failure: ImportError: cannot import name 'soft_unicode' from 'markupsafe'.

Diagnostic experiment:
- Installed MarkupSafe==2.0.1 in the isolated environment.
- Tests afterward: 10 passed, 0 failed.
- pip check reported no broken requirements.

Limitations:
- No project source or dependency files have been changed.
- A clean installation has not been tested.
- Compatibility across Python versions has not been verified.
- The diagnostic experiment is not yet a permanent fix.`;

function updateCharacterCount() {
  const count = evidenceInput.value.length;
  charCount.textContent = `${count.toLocaleString()} character${count === 1 ? "" : "s"}`;
}

function setLoading(isLoading) {
  analyzeButton.disabled = isLoading;
  analyzeButton.querySelector(".button-label").textContent = isLoading ? "Analyzing..." : "Analyze evidence";
  resultsPanel.setAttribute("aria-busy", String(isLoading));
  emptyState.hidden = isLoading || analysisResults.dataset.hasResults === "true";
  loadingState.hidden = !isLoading;
  analysisResults.hidden = isLoading || analysisResults.dataset.hasResults !== "true";
}

function renderValue(value) {
  if (Array.isArray(value)) {
    const list = document.createElement("ul");
    value.forEach((item) => {
      const listItem = document.createElement("li");
      listItem.textContent = typeof item === "string" ? item : JSON.stringify(item);
      list.append(listItem);
    });
    return list;
  }
  const paragraph = document.createElement("p");
  paragraph.textContent = typeof value === "string" ? value : JSON.stringify(value);
  return paragraph;
}

function renderAnalysis(data) {
  const labels = [
    ["issue", "Issue"],
    ["evidence", "Evidence"],
    ["analysis", "Analysis"],
    ["recommended_action", "Recommended action"],
    ["compatibility_concerns", "Compatibility concerns"],
    ["limitations", "Limitations"],
    ["verification_status", "Verification status"],
  ];
  const fragment = document.createDocumentFragment();

  labels.forEach(([key, label]) => {
    if (!(key in data)) return;
    const section = document.createElement("section");
    section.className = `result-section${key === "recommended_action" ? " recommendation" : ""}`;
    const heading = document.createElement("h3");
    heading.textContent = label;
    section.append(heading, renderValue(data[key]));
    fragment.append(section);
  });

  analysisResults.replaceChildren(fragment);
  analysisResults.dataset.hasResults = "true";
  emptyState.hidden = true;
  analysisResults.hidden = false;
}

document.querySelector("#load-example").addEventListener("click", () => {
  evidenceInput.value = exampleEvidence;
  updateCharacterCount();
  evidenceInput.focus();
});

evidenceInput.addEventListener("input", updateCharacterCount);

analyzeButton.addEventListener("click", async () => {
  const evidence = evidenceInput.value.trim();
  errorMessage.hidden = true;
  errorMessage.textContent = "";

  if (!evidence) {
    errorMessage.textContent = "Add repository evidence before starting the analysis.";
    errorMessage.hidden = false;
    evidenceInput.focus();
    return;
  }

  setLoading(true);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ evidence }),
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || `Analysis failed (${response.status}).`);
    }
    renderAnalysis(result);
  } catch (error) {
    errorMessage.textContent = error instanceof TypeError
      ? "Could not reach Scout. Make sure the local server is running, then try again."
      : error.message;
    errorMessage.hidden = false;
    emptyState.hidden = analysisResults.dataset.hasResults === "true";
    analysisResults.hidden = analysisResults.dataset.hasResults !== "true";
  } finally {
    setLoading(false);
  }
});

updateCharacterCount();
