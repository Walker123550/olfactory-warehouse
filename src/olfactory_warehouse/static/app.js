const form = document.querySelector("#recordForm");
const recordsBody = document.querySelector("#recordsBody");
const searchInput = document.querySelector("#searchInput");
const statusEl = document.querySelector("#status");
const modelButton = document.querySelector("#modelButton");
const modelBox = document.querySelector("#modelBox");

let records = [];

function today() {
  return new Date().toISOString().slice(0, 10);
}

function formToJson(formElement) {
  const data = new FormData(formElement);
  return Object.fromEntries(data.entries());
}

function showStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "var(--warn)" : "var(--muted)";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function keywordPills(value) {
  if (!value) return "";
  return value
    .split("、")
    .filter(Boolean)
    .map((keyword) => `<span class="pill">${escapeHtml(keyword)}</span>`)
    .join("");
}

function recordText(record) {
  return Object.values(record).join(" ").toLowerCase();
}

function renderRecords() {
  const query = searchInput.value.trim().toLowerCase();
  const filtered = query ? records.filter((record) => recordText(record).includes(query)) : records;

  if (!filtered.length) {
    recordsBody.innerHTML = `<tr><td colspan="11"><div class="empty">还没有匹配的闻香记录</div></td></tr>`;
    return;
  }

  recordsBody.innerHTML = filtered
    .map(
      (record) => `
        <tr>
          <td>${escapeHtml(record.smell_date)}</td>
          <td>
            <strong>${escapeHtml(record.sample_id)}</strong><br />
            ${escapeHtml(record.material_name)}
            <div>${escapeHtml(record.sample_type)} · ${escapeHtml(record.brand_source)}</div>
          </td>
          <td>${escapeHtml(record.primary_category)}<br />${escapeHtml(record.secondary_category)}</td>
          <td>${keywordPills(record.keywords)}</td>
          <td>${escapeHtml(record.intensity)} / 5<br />扩散 ${escapeHtml(record.diffusion)}</td>
          <td>${escapeHtml(record.note_0m)}</td>
          <td>${escapeHtml(record.note_30m)}</td>
          <td>${escapeHtml(record.note_2h)}<br />挥发 ${escapeHtml(record.volatility_speed)}</td>
          <td>${escapeHtml(record.compared_sample)}<br />锚点 ${escapeHtml(record.anchor_name)}</td>
          <td>${escapeHtml(record.difference_desc)}</td>
          <td><button class="secondary" type="button" data-delete="${record.session_key}">删除</button></td>
        </tr>
      `
    )
    .join("");
}

async function deleteRecord(sessionKey) {
  const response = await fetch(`/api/records/${sessionKey}`, { method: "DELETE" });
  const payload = await response.json();
  if (!response.ok) {
    showStatus(payload.error || "删除失败", true);
    return;
  }
  showStatus(`已删除记录 #${sessionKey}`);
  await loadRecords();
}

async function loadRecords() {
  const response = await fetch("/api/records");
  const payload = await response.json();
  records = payload.records || [];
  renderRecords();
}

async function saveRecord(event) {
  event.preventDefault();
  showStatus("保存中...");

  const response = await fetch("/api/records", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formToJson(form)),
  });
  const payload = await response.json();

  if (!response.ok) {
    showStatus(payload.error || "保存失败", true);
    return;
  }

  form.reset();
  form.elements.smell_date.value = today();
  syncRangeOutputs();
  showStatus(`已保存记录 #${payload.session_key}`);
  await loadRecords();
}

function syncRangeOutputs() {
  document.querySelectorAll("output[data-for]").forEach((output) => {
    const input = form.elements[output.dataset.for];
    output.value = input.value;
  });
}

async function toggleModel() {
  if (!modelBox.classList.contains("hidden")) {
    modelBox.classList.add("hidden");
    return;
  }

  const response = await fetch("/api/model");
  const model = await response.json();
  modelBox.innerHTML = Object.entries(model)
    .map(([table, desc]) => `<div><strong>${escapeHtml(table)}</strong>：${escapeHtml(desc)}</div>`)
    .join("");
  modelBox.classList.remove("hidden");
}

form.addEventListener("submit", saveRecord);
form.addEventListener("input", syncRangeOutputs);
form.addEventListener("reset", () => {
  setTimeout(() => {
    form.elements.smell_date.value = today();
    syncRangeOutputs();
    showStatus("");
  });
});
searchInput.addEventListener("input", renderRecords);
modelButton.addEventListener("click", toggleModel);
recordsBody.addEventListener("click", (event) => {
  const button = event.target.closest("[data-delete]");
  if (!button) return;
  deleteRecord(button.dataset.delete);
});

form.elements.smell_date.value = today();
syncRangeOutputs();
loadRecords().catch((error) => showStatus(error.message, true));
