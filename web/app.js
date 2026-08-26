const views = ["overview", "commission", "systems"];

function $(id) { return document.getElementById(id); }

function showToast(message, error = false) {
  const toast = $("toast");
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3200);
}

function setView(name) {
  if (!views.includes(name)) return;
  document.querySelectorAll(".view").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.toggle("active", el.dataset.view === name));
  $("view-" + name).classList.add("active");
  const titles = { overview: "Overview", commission: "New system", systems: "Systems" };
  $("page-title").textContent = titles[name];
  if (name === "systems") loadSystems();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  let body = null;
  try { body = await response.json(); } catch (_) { body = null; }
  if (!response.ok) {
    const detail = body?.detail || `Request failed (${response.status})`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderSystems(target, systems, compact = false) {
  if (!systems.length) {
    target.className = compact ? "system-list empty-state" : "system-grid empty-state";
    target.textContent = "No commissioned systems saved.";
    return;
  }
  target.className = compact ? "system-list" : "system-grid";
  target.innerHTML = systems.map(system => {
    const resolution = system.observability?.resolution || "Not assessed";
    const source = system.source_mode || "unknown";
    if (compact) {
      return `<div class="system-row"><div><strong>${escapeHtml(system.name)}</strong><span>${escapeHtml(system.system_id)} · ${escapeHtml(source)}</span></div><span class="pill">${escapeHtml(resolution)}</span></div>`;
    }
    const mappingCount = Object.keys(system.mappings || {}).length;
    return `<article class="system-card">
      <p class="eyebrow">${escapeHtml(source)}</p>
      <strong>${escapeHtml(system.name)}</strong>
      <span>${escapeHtml(system.system_id)}</span>
      <div class="meta">
        <span class="meta-chip">${escapeHtml(resolution)} resolution</span>
        <span class="meta-chip">${mappingCount} mapped signals</span>
        <span class="meta-chip">Read-only</span>
      </div>
    </article>`;
  }).join("");
}

async function loadOverview() {
  try {
    const [health, systems] = await Promise.all([api("/health"), api("/v1/systems")]);
    $("api-status").textContent = health.status === "ok" ? "Online" : "Degraded";
    $("system-count").textContent = systems.length;
    renderSystems($("overview-systems"), systems.slice(0, 4), true);
  } catch (error) {
    $("api-status").textContent = "Unavailable";
    showToast(error.message, true);
  }
}

async function loadSystems() {
  try {
    const systems = await api("/v1/systems");
    renderSystems($("systems-list"), systems, false);
  } catch (error) {
    showToast(error.message, true);
  }
}

function metricCard(label, value, note) {
  return `<article class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></article>`;
}

function renderCommissioning(data) {
  const result = $("commissioning-result");
  result.classList.remove("hidden");
  $("result-title").textContent = data.filename ? `${data.filename}` : `${data.system_id} live preview`;

  const readiness = data.readiness || {};
  const observability = data.observability || {};
  const topology = data.topology || {};
  const ready = readiness.ready_for_core_analysis === true;
  $("result-badge").textContent = ready ? "Core analysis ready" : "Review required";

  $("result-metrics").innerHTML = [
    metricCard("Core coverage", `${readiness.core_coverage_pct ?? 0}%`, "Required signals"),
    metricCard("Resolution", observability.resolution || "SKID", "Supported diagnosis"),
    metricCard("Stages", topology.stages_detected ?? 0, "Detected from evidence"),
    metricCard("Vessels", topology.vessels_detected ?? 0, "Detected from evidence"),
  ].join("");

  const proposals = data.proposals || [];
  $("mapping-table").innerHTML = `<table>
    <thead><tr><th>Source</th><th>Proposed signal</th><th>Confidence</th><th>Unit</th><th>Context</th></tr></thead>
    <tbody>${proposals.map(p => `<tr>
      <td>${escapeHtml(p.source_name)}</td>
      <td>${escapeHtml(p.canonical_signal || "Needs review")}</td>
      <td class="confidence">${Math.round((p.confidence || 0) * 100)}%</td>
      <td>${escapeHtml(p.detected_unit || "—")}</td>
      <td>${escapeHtml([p.stage_hint, p.vessel_hint].filter(Boolean).join(" / ") || "—")}</td>
    </tr>`).join("")}</tbody>
  </table>`;

  const supported = observability.supported_capabilities || [];
  const unsupported = observability.unsupported_capabilities || [];
  const recommended = observability.recommended_measurements || [];
  $("observability-panel").innerHTML = `
    <span class="eyebrow">Available resolution</span>
    <strong>${escapeHtml(observability.resolution || "SKID")}</strong>
    <p class="muted">Observability score: ${escapeHtml(observability.score ?? 0)}%</p>
    <h4>Supported</h4>
    <ul class="capability-list">${supported.map(item => `<li>${escapeHtml(item.replaceAll("_", " "))}</li>`).join("") || "<li>Limited by available instrumentation</li>"}</ul>
    ${unsupported.length ? `<h4>Not supported yet</h4><ul class="capability-list">${unsupported.map(item => `<li>${escapeHtml(item.replaceAll("_", " "))}</li>`).join("")}</ul>` : ""}
    ${recommended.length ? `<h4>To improve resolution</h4><ul class="capability-list">${recommended.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : ""}
  `;

  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function inspectUpload() {
  const fileInput = $("process-file");
  const file = fileInput.files?.[0];
  if (!file) {
    showToast("Choose a CSV or Excel process-data file first.", true);
    return;
  }
  const systemId = $("system-id-upload").value.trim() || "MEMBRANE-01";
  const form = new FormData();
  form.append("file", file);
  const button = $("upload-button");
  const old = button.textContent;
  button.disabled = true;
  button.textContent = "Inspecting…";
  try {
    const data = await api(`/v1/commissioning/upload?system_id=${encodeURIComponent(systemId)}`, { method: "POST", body: form });
    renderCommissioning(data);
    showToast("Process data inspected. Review the proposed mapping and diagnostic resolution.");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = old;
  }
}

async function runLiveDemo() {
  const systemId = $("system-id-live").value.trim() || "UF-01";
  const button = $("live-demo-button");
  const old = button.textContent;
  button.disabled = true;
  button.textContent = "Connecting read-only…";
  try {
    const data = await api(`/v1/commissioning/live-demo?system_id=${encodeURIComponent(systemId)}`);
    renderCommissioning(data);
    showToast("Live commissioning path completed using the simulated PLC source.");
  } catch (error) {
    showToast(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = old;
  }
}

document.querySelectorAll(".nav-item").forEach(button => button.addEventListener("click", () => setView(button.dataset.view)));
document.querySelectorAll("[data-go]").forEach(button => button.addEventListener("click", () => setView(button.dataset.go)));
$("new-system-shortcut").addEventListener("click", () => setView("commission"));
$("refresh-overview").addEventListener("click", loadOverview);
$("refresh-systems").addEventListener("click", loadSystems);
$("upload-button").addEventListener("click", inspectUpload);
$("live-demo-button").addEventListener("click", runLiveDemo);
$("process-file").addEventListener("change", event => {
  const file = event.target.files?.[0];
  if (file) event.target.closest("label").querySelector("strong").textContent = file.name;
});

loadOverview();
