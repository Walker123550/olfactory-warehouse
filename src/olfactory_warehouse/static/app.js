const form = document.querySelector("#recordForm");
const recordsBody = document.querySelector("#recordsBody");
const searchInput = document.querySelector("#searchInput");
const statusEl = document.querySelector("#status");
const modelButton = document.querySelector("#modelButton");
const modelBox = document.querySelector("#modelBox");
const primaryCategory = document.querySelector("#primaryCategory");
const secondaryCategory = document.querySelector("#secondaryCategory");
const secondaryList = document.querySelector("#secondaryList");
const guideSummary = document.querySelector("#guideSummary");
const secondaryChips = document.querySelector("#secondaryChips");
const keywordChips = document.querySelector("#keywordChips");
const compareChips = document.querySelector("#compareChips");
const anchorChips = document.querySelector("#anchorChips");
const stageHintText = document.querySelector("#stageHintText");
const applyGuideButton = document.querySelector("#applyGuideButton");

let records = [];

const ODOR_GUIDE = {
  柑橘: { summary: "柑橘通常属于明亮、挥发快的前调，先判断酸甜、果皮苦、青绿和汁水感。", secondary: ["柠檬", "甜橙", "佛手柑", "葡萄柚", "青柠", "橘子", "苦橙叶"], keywords: ["酸", "甜", "果皮苦", "明亮", "清爽", "多汁", "青绿", "尖锐", "挥发快"], comparisons: ["柠檬", "橙子", "葡萄柚", "佛手柑", "青柠"], anchors: ["柠檬", "橙子", "葡萄柚", "清新前调"], stages: ["0分钟常见：酸、亮、冲击强", "10分钟常见：酸感变柔或甜感浮出", "30分钟常见：果皮苦、青绿或明显变淡", "2小时常见：残留弱或几乎无"] },
  花香: { summary: "花香先判断是真花、水润、粉感、皂感还是甜蜜感，再区分玫瑰、茉莉、铃兰等方向。", secondary: ["玫瑰", "茉莉", "橙花", "薰衣草", "铃兰", "紫罗兰", "依兰", "天竺葵"], keywords: ["花瓣", "粉感", "甜", "水润", "皂感", "青绿", "蜜感", "脂粉", "柔和"], comparisons: ["玫瑰", "茉莉", "橙花", "薰衣草", "天竺葵"], anchors: ["玫瑰", "白花", "粉感花香", "芳香草本"], stages: ["0分钟常见：花瓣、青绿或甜感先出现", "10分钟常见：粉感、皂感或蜜感变清楚", "30分钟常见：花体变圆或转为脂粉", "2小时常见：柔和花粉或皂感残留"] },
  木质: { summary: "木质重点判断干湿、温冷、烟感、铅笔屑、奶感和树脂感，常作为中后调支撑。", secondary: ["雪松", "檀香", "广藿香", "岩兰草", "愈创木", "橡木苔"], keywords: ["干燥", "温暖", "冷感", "铅笔屑", "烟感", "奶感", "土感", "根茎", "持久"], comparisons: ["雪松", "檀香", "广藿香", "岩兰草"], anchors: ["干木质", "奶感木质", "土壤木质", "烟熏木质"], stages: ["0分钟常见：干木、烟感或泥土感", "10分钟常见：木质轮廓变稳定", "30分钟常见：干燥、温暖或根茎感加强", "2小时常见：残留清楚，常比柑橘持久"] },
  草本: { summary: "草本和芳香调常带有叶片、药草、清凉、樟脑或茶感，注意它和青绿花香的区别。", secondary: ["薰衣草", "迷迭香", "鼠尾草", "薄荷", "罗勒", "茶叶", "青草"], keywords: ["草叶", "药草", "清凉", "樟脑", "茶感", "苦", "青绿", "干净", "微辛"], comparisons: ["薰衣草", "迷迭香", "薄荷", "茶叶"], anchors: ["芳香草本", "清凉草本", "茶感", "青草"], stages: ["0分钟常见：青绿、清凉或药感", "10分钟常见：苦感和干草感浮现", "30分钟常见：变干、转茶感或粉感", "2小时常见：弱草本或干净残留"] },
  辛香: { summary: "辛香先分冷暖：冷辛偏胡椒、姜，暖辛偏肉桂、丁香、豆蔻，注意刺激感和甜感。", secondary: ["黑胡椒", "粉红胡椒", "丁香", "肉桂", "豆蔻", "姜", "藏红花"], keywords: ["辛辣", "温暖", "干燥", "刺激", "甜辛", "粉尘感", "药感", "暖感", "锐利"], comparisons: ["黑胡椒", "丁香", "肉桂", "姜"], anchors: ["冷辛香", "暖辛香", "甜辛香", "药感辛香"], stages: ["0分钟常见：刺激、尖锐或暖甜", "10分钟常见：辛辣变圆或药感出现", "30分钟常见：干燥粉尘感", "2小时常见：暖辛或弱药感残留"] },
  树脂: { summary: "树脂、琥珀和香脂方向通常更厚、更甜、更持久，重点判断甜、烟、药、香脂和黏稠感。", secondary: ["乳香", "没药", "安息香", "劳丹脂", "琥珀", "秘鲁香脂"], keywords: ["树脂", "香脂", "甜", "烟感", "药感", "琥珀", "黏稠", "温暖", "持久"], comparisons: ["乳香", "没药", "安息香", "琥珀"], anchors: ["烟熏树脂", "甜树脂", "琥珀", "香脂"], stages: ["0分钟常见：药感、烟感或甜脂", "10分钟常见：香脂感变厚", "30分钟常见：温暖、圆润、黏稠", "2小时常见：残留明显且稳定"] },
  果香: { summary: "果香先判断是鲜果、熟果、糖渍、果酱还是发酵感，再判断酸甜比例。", secondary: ["苹果", "梨", "桃子", "浆果", "黑加仑", "无花果", "热带水果"], keywords: ["多汁", "甜", "酸甜", "熟果", "果酱", "糖渍", "发酵", "青脆", "软糯"], comparisons: ["苹果", "桃子", "浆果", "黑加仑"], anchors: ["鲜果", "熟果", "浆果", "热带果香"], stages: ["0分钟常见：酸甜、多汁或糖感", "10分钟常见：熟果或果酱感变明显", "30分钟常见：甜感留下或变软", "2小时常见：弱甜果香或糖感残留"] },
  动物: { summary: "动物感记录要克制，重点写皮革、麝香、脂肪、汗感、毛皮或脏感的程度。", secondary: ["麝香", "皮革", "龙涎", "海狸香", "灵猫", "脂肪感"], keywords: ["皮革", "麝香", "脂肪", "汗感", "毛皮", "咸", "温热", "脏感", "贴肤"], comparisons: ["麝香", "皮革", "龙涎"], anchors: ["干净麝香", "皮革", "咸龙涎", "脏动物感"], stages: ["0分钟常见：皮革、咸感或温热感", "10分钟常见：贴肤、脂肪或毛皮感", "30分钟常见：变柔但存在感强", "2小时常见：贴肤残留明显"] },
};

function today() { return new Date().toISOString().slice(0, 10); }
function formToJson(formElement) { return Object.fromEntries(new FormData(formElement).entries()); }
function showStatus(message, isError = false) { statusEl.textContent = message; statusEl.style.color = isError ? "var(--warn)" : "var(--muted)"; }
function escapeHtml(value) { return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;"); }
function appendToken(fieldName, token) { const input = form.elements[fieldName]; const current = input.value.split(/[、,，;；\n]/).map((item) => item.trim()).filter(Boolean); if (!current.includes(token)) current.push(token); input.value = current.join("、"); }
function setIfEmpty(fieldName, value) { if (!form.elements[fieldName].value.trim()) form.elements[fieldName].value = value; }
function chip(label, field, mode = "append") { return `<button class="chip" type="button" data-field="${field}" data-mode="${mode}" data-value="${escapeHtml(label)}">${escapeHtml(label)}</button>`; }
function renderChipList(container, items, field, mode = "append") { container.innerHTML = items.map((item) => chip(item, field, mode)).join(""); }
function selectedGuide() { return ODOR_GUIDE[primaryCategory.value] || null; }

function updateGuide() {
  const guide = selectedGuide();
  if (!guide) {
    guideSummary.textContent = "先选择一级分类，系统会按经典香气家族给出候选词。";
    secondaryList.innerHTML = secondaryChips.innerHTML = keywordChips.innerHTML = compareChips.innerHTML = anchorChips.innerHTML = stageHintText.innerHTML = "";
    return;
  }
  guideSummary.textContent = guide.summary;
  secondaryList.innerHTML = guide.secondary.map((item) => `<option value="${escapeHtml(item)}"></option>`).join("");
  renderChipList(secondaryChips, guide.secondary, "secondary_category", "set");
  renderChipList(keywordChips, guide.keywords, "keywords");
  renderChipList(compareChips, guide.comparisons, "compared_sample", "set");
  renderChipList(anchorChips, guide.anchors, "anchor_name", "set");
  stageHintText.innerHTML = guide.stages.map((item) => `<span>${escapeHtml(item)}</span>`).join("");
}

function applyGuideDefaults() {
  const guide = selectedGuide();
  if (!guide) return;
  setIfEmpty("secondary_category", guide.secondary[0]);
  guide.keywords.slice(0, 4).forEach((keyword) => appendToken("keywords", keyword));
  setIfEmpty("compared_sample", guide.comparisons[0]);
  setIfEmpty("anchor_name", guide.anchors[0]);
  setIfEmpty("note_0m", guide.stages[0].replace("0分钟常见：", ""));
  setIfEmpty("note_10m", guide.stages[1].replace("10分钟常见：", ""));
  setIfEmpty("note_30m", guide.stages[2].replace("30分钟常见：", ""));
  setIfEmpty("note_2h", guide.stages[3].replace("2小时常见：", ""));
}

function keywordPills(value) { if (!value) return ""; return value.split("、").filter(Boolean).map((keyword) => `<span class="pill">${escapeHtml(keyword)}</span>`).join(""); }
function recordText(record) { return Object.values(record).join(" ").toLowerCase(); }

function renderRecords() {
  const query = searchInput.value.trim().toLowerCase();
  const filtered = query ? records.filter((record) => recordText(record).includes(query)) : records;
  if (!filtered.length) { recordsBody.innerHTML = `<tr><td colspan="11"><div class="empty">还没有匹配的闻香记录</div></td></tr>`; return; }
  recordsBody.innerHTML = filtered.map((record) => `
    <tr>
      <td>${escapeHtml(record.smell_date)}</td>
      <td><strong>${escapeHtml(record.sample_id)}</strong><br />${escapeHtml(record.material_name)}<div>${escapeHtml(record.sample_type)} · ${escapeHtml(record.brand_source)}</div></td>
      <td>${escapeHtml(record.primary_category)}<br />${escapeHtml(record.secondary_category)}</td>
      <td>${keywordPills(record.keywords)}</td>
      <td>${escapeHtml(record.intensity)} / 5<br />扩散 ${escapeHtml(record.diffusion)}</td>
      <td>${escapeHtml(record.note_0m)}</td><td>${escapeHtml(record.note_30m)}</td>
      <td>${escapeHtml(record.note_2h)}<br />挥发 ${escapeHtml(record.volatility_speed)}</td>
      <td>${escapeHtml(record.compared_sample)}<br />锚点 ${escapeHtml(record.anchor_name)}</td>
      <td>${escapeHtml(record.difference_desc)}</td>
      <td><button class="secondary" type="button" data-delete="${record.session_key}">删除</button></td>
    </tr>`).join("");
}

async function deleteRecord(sessionKey) { const response = await fetch(`/api/records/${sessionKey}`, { method: "DELETE" }); const payload = await response.json(); if (!response.ok) { showStatus(payload.error || "删除失败", true); return; } showStatus(`已删除记录 #${sessionKey}`); await loadRecords(); }
async function loadRecords() { const response = await fetch("/api/records"); const payload = await response.json(); records = payload.records || []; renderRecords(); }

async function saveRecord(event) {
  event.preventDefault();
  showStatus("保存中...");
  const response = await fetch("/api/records", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(formToJson(form)) });
  const payload = await response.json();
  if (!response.ok) { showStatus(payload.error || "保存失败", true); return; }
  form.reset();
  form.elements.smell_date.value = today();
  syncRangeOutputs();
  updateGuide();
  showStatus(`已保存记录 #${payload.session_key}`);
  await loadRecords();
}

function syncRangeOutputs() { document.querySelectorAll("output[data-for]").forEach((output) => { output.value = form.elements[output.dataset.for].value; }); }
async function toggleModel() { if (!modelBox.classList.contains("hidden")) { modelBox.classList.add("hidden"); return; } const response = await fetch("/api/model"); const model = await response.json(); modelBox.innerHTML = Object.entries(model).map(([table, desc]) => `<div><strong>${escapeHtml(table)}</strong>：${escapeHtml(desc)}</div>`).join(""); modelBox.classList.remove("hidden"); }
function initializePrimaryOptions() { primaryCategory.innerHTML += Object.keys(ODOR_GUIDE).map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`).join(""); }

form.addEventListener("submit", saveRecord);
form.addEventListener("input", syncRangeOutputs);
form.addEventListener("reset", () => { setTimeout(() => { form.elements.smell_date.value = today(); syncRangeOutputs(); updateGuide(); showStatus(""); }); });
searchInput.addEventListener("input", renderRecords);
modelButton.addEventListener("click", toggleModel);
primaryCategory.addEventListener("change", () => { secondaryCategory.value = ""; updateGuide(); });
applyGuideButton.addEventListener("click", applyGuideDefaults);
document.addEventListener("click", (event) => { const button = event.target.closest("[data-field]"); if (!button) return; const field = button.dataset.field; const value = button.dataset.value; if (button.dataset.mode === "set") form.elements[field].value = value; else appendToken(field, value); });
recordsBody.addEventListener("click", (event) => { const button = event.target.closest("[data-delete]"); if (!button) return; deleteRecord(button.dataset.delete); });

initializePrimaryOptions();
form.elements.smell_date.value = today();
syncRangeOutputs();
updateGuide();
loadRecords().catch((error) => showStatus(error.message, true));
