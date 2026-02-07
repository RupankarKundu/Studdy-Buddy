/* ===============================
   API BASE (LOCAL)
================================ */
const API = "http://localhost:8000";
const ytToggle = document.getElementById("ytToggle");

/* ===============================
   ELEMENT REFERENCES
================================ */
const syllabusText = document.getElementById("syllabusText");
const fileInput = document.getElementById("fileInput");
const result = document.getElementById("result");

const filePreview = document.getElementById("filePreview");
const fileNameEl = document.getElementById("fileName");
const fileIconEl = document.getElementById("fileIcon");
const attachHint = document.getElementById("attachHint");

const themeToggle = document.getElementById("themeToggle");

let loadingElement = null;

/* ===============================
   FILE ATTACHMENT PREVIEW
================================ */
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;

  fileNameEl.textContent = file.name;
  fileIconEl.textContent = file.type.startsWith("image/") ? "🖼️" : "📄";

  filePreview.classList.remove("hidden");
  attachHint.style.display = "none";
});

function removeFile() {
  fileInput.value = "";
  filePreview.classList.add("hidden");
  attachHint.style.display = "inline";
}

/* ===============================
   LOADING INDICATOR
================================ */
function showLoading() {
  loadingElement = document.createElement("div");
  loadingElement.className = "loading";
  loadingElement.innerHTML = `
    <div class="spinner"></div>
    <div class="loading-text">Analyzing syllabus…</div>
  `;
  document.body.appendChild(loadingElement);
}

function removeLoading() {
  if (loadingElement) {
    loadingElement.remove();
    loadingElement = null;
  }
}

/* ===============================
   MAIN ANALYZE FUNCTION
================================ */
async function analyze() {
  const text = syllabusText.value.trim();
  const file = fileInput.files[0];

  if (!text && !file) {
    alert("Enter syllabus text or attach a PDF / image");
    return;
  }

  const form = new FormData();
  form.append("include_playlists", ytToggle.checked);

  let endpoint = "";

  if (file) {
    if (file.type.startsWith("image/")) {
      form.append("image", file);
      endpoint = "/analyze-image";
    } else {
      form.append("pdf", file);
      endpoint = "/analyze-pdf";
    }
  } else {
    form.append("text", text);
    endpoint = "/analyze-text";
  }

  showLoading();

  try {
    const response = await fetch(`${API}${endpoint}`, {
      method: "POST",
      body: form
    });

    const data = await response.json();

    removeLoading();

    if (!response.ok || data.error) {
      throw new Error(data.error || "Server error");
    }

    // Clear old results before rendering new ones
    result.innerHTML = "";

    // Clear inputs ONLY after success
    syllabusText.value = "";
    fileInput.value = "";
    filePreview.classList.add("hidden");
    attachHint.style.display = "inline";

    renderResult(data);

  } catch (error) {
    removeLoading();
    console.error(error);
    alert(error.message || "Something went wrong. Please try again.");
  }
}

/* ===============================
   RENDER RESULTS
================================ */
function renderResult(data) {
  if (!data || !data.units) {
    alert("No valid analysis data received.");
    return;
  }

  data.units.forEach(unit => {
    const unitDiv = document.createElement("div");
    unitDiv.className = "unit";

    unitDiv.innerHTML = `<h3>${unit.unit_name}</h3>`;

    /* COPY BUTTON */
    const copyBtn = document.createElement("button");
    copyBtn.className = "copy-btn";
    copyBtn.innerText = "📋 Copy";
    copyBtn.onclick = () => copyUnitText(copyBtn);
    unitDiv.appendChild(copyBtn);

    ["very_important", "important"].forEach(level => {
      (unit[level] || []).forEach(item => {
        const topicDiv = document.createElement("div");
        topicDiv.className = "topic";

        const topicText =
          typeof item === "string" ? item : item.topic;

        const playlistHtml =
          ytToggle.checked &&
          typeof item === "object" &&
          item.playlist
            ? ` – <a href="${item.playlist.url}" target="_blank">▶ Playlist</a>`
            : "";

        topicDiv.innerHTML = `
          <strong>${topicText}</strong>
          ${playlistHtml}
        `;

        unitDiv.appendChild(topicDiv);
      });
    });

    result.appendChild(unitDiv);
  });

  result.scrollTop = 0;
}

/* ===============================
   DARK MODE TOGGLE
================================ */
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
  themeToggle.textContent = "☀️";
}

themeToggle.addEventListener("click", () => {
  document.body.classList.toggle("dark");

  const isDark = document.body.classList.contains("dark");
  localStorage.setItem("theme", isDark ? "dark" : "light");

  themeToggle.textContent = isDark ? "☀️" : "🌙";
});

/* ===============================
   DOWNLOAD PDF
================================ */
document
  .getElementById("downloadPdfBtn")
  .addEventListener("click", downloadPDF);

function downloadPDF() {
  const resultPanel = document.getElementById("result");

  if (!resultPanel || resultPanel.children.length === 0) {
    alert("No results to download");
    return;
  }

  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF("p", "mm", "a4");

  const marginX = 15;
  let y = 18;
  const pageHeight = pdf.internal.pageSize.height;

  pdf.setFont("helvetica", "bold");
  pdf.setFontSize(18);
  pdf.text("Study Buddy – Syllabus Analysis", marginX, y);
  y += 12;

  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(11);

  [...resultPanel.children].forEach(unit => {
    const unitTitle = unit.querySelector("h3")?.innerText;

    if (y > pageHeight - 25) {
      pdf.addPage();
      y = 18;
    }

    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(13);
    pdf.text(unitTitle, marginX, y);
    y += 8;

    pdf.setFont("helvetica", "normal");
    pdf.setFontSize(11);

    unit.querySelectorAll(".topic").forEach(topicEl => {
      const topicText = topicEl.querySelector("strong")?.innerText || "";
      const linkEl = topicEl.querySelector("a");

      if (y > pageHeight - 20) {
        pdf.addPage();
        y = 18;
      }

      pdf.text(`• ${topicText}`, marginX + 2, y);
      y += 6;

      if (linkEl) {
        pdf.setTextColor(37, 99, 235);
        pdf.textWithLink("YouTube Playlist", marginX + 8, y, {
          url: linkEl.href
        });
        pdf.setTextColor(0, 0, 0);
        y += 6;
      }
    });

    y += 6;
  });

  pdf.save("study-buddy-syllabus.pdf");
}

/* ===============================
   COPY UNIT TEXT
================================ */
function copyUnitText(button) {
  const unit = button.closest(".unit");
  if (!unit) return;

  let text = "";
  const unitTitle = unit.querySelector("h3")?.innerText;

  if (unitTitle) {
    text += `Unit: ${unitTitle}\n\n`;
  }

  unit.querySelectorAll(".topic strong").forEach(topic => {
    text += `• ${topic.innerText}\n`;
  });

  navigator.clipboard.writeText(text.trim());

  const original = button.innerText;
  button.innerText = "✓ Copied";
  button.classList.add("copied");

  setTimeout(() => {
    button.innerText = original;
    button.classList.remove("copied");
  }, 1500);
}

/* ===============================
   INPUT MODE WRAPPERS
================================ */
function analyzeTextOnly() {
  fileInput.value = "";
  filePreview.classList.add("hidden");
  attachHint.style.display = "inline";
  analyze();
}

function analyzeFileOnly() {
  syllabusText.value = "";
  analyze();
}