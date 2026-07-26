const dashboardData = {
  profiles: [],
  predictions: [],
  assets: [],
  workflows: [],
  demo: null
};

let workflowFilter = "all";
let pendingAssistantAction = null;

const viewTitles = {
  overview: "Fleet Overview",
  assets: "Asset Health",
  workflows: "Workflow Execution",
  assistant: "Operations Assistant"
};

const statusLabels = {
  critical: "Critical",
  warning: "Warning",
  watch: "Watch",
  healthy: "Healthy",
  failed: "Failed",
  running: "Running",
  completed: "Completed",
  ok: "Operational",
  error: "Error"
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function refreshIcons() {
  if (window.lucide) {
    window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
  }
}

function statusPill(status) {
  const normalized = status || "error";
  const label = statusLabels[normalized] || normalized;
  return `<span class="status-pill status-${escapeHtml(normalized)}">${escapeHtml(label)}</span>`;
}

function workflowOutcome(workflow) {
  if (workflow.status !== "completed" || !workflow.result_summary) {
    return {
      status: workflow.status,
      label: statusLabels[workflow.status] || workflow.status
    };
  }
  return {
    status: workflow.result_summary.outcome_status,
    label: workflow.result_summary.outcome_label
  };
}

function workflowStatusPill(workflow) {
  const outcome = workflowOutcome(workflow);
  return `<span class="status-pill status-${escapeHtml(outcome.status)}">${escapeHtml(outcome.label)}</span>`;
}

function workflowSummaryText(workflow) {
  const summary = workflow.result_summary;
  if (!summary) return "";
  const conditions = ["critical", "warning", "watch", "healthy"]
    .filter((status) => summary[status] > 0)
    .map((status) => `${summary[status]} ${status}`)
    .join(" · ");
  const shortestRul = summary.shortest_rul_cycles === null
    ? ""
    : ` · shortest RUL ${Number(summary.shortest_rul_cycles).toFixed(1)} cycles`;
  return `${conditions}${shortestRul}`;
}

function formatDateTime(value) {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not available";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function formatTime(value) {
  if (!value) return "None";
  return new Intl.DateTimeFormat("en", {
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

function formatStepLabel(value) {
  const label = value ? value.replaceAll("_", " ") : "Predictive maintenance";
  return label.charAt(0).toUpperCase() + label.slice(1);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "Not reported";
  const normalized = Number(value) <= 1 ? Number(value) * 100 : Number(value);
  return `${Math.round(normalized)}%`;
}

function formatRul(value) {
  if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) {
    return "Unavailable";
  }
  return `${Number(value).toFixed(1)} cycles`;
}

async function apiFetch(path) {
  const response = await fetch(path);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.message || payload.detail || `Request failed (${response.status}).`);
  }
  return payload.data;
}

async function optionalApiFetch(path) {
  const response = await fetch(path);
  const payload = await response.json();
  if (response.status === 404) return {};
  if (!response.ok) {
    throw new Error(payload.message || payload.detail || `Request failed (${response.status}).`);
  }
  return payload.data;
}

function profileStatus(riskScore) {
  if (riskScore >= 0.6) return "critical";
  if (riskScore >= 0.4) return "warning";
  if (riskScore >= 0.2) return "watch";
  return "healthy";
}

function profilePriority(status) {
  return {
    critical: "Immediate",
    warning: "High",
    watch: "Medium",
    healthy: "Routine"
  }[status];
}

function normalizeAssets(profiles, predictions) {
  const predictionByAsset = new Map(predictions.map((prediction) => [prediction.asset_id, prediction]));
  const profileByAsset = new Map(profiles.map((profile) => [profile.asset_id, profile]));
  const rulAssetIds = predictions
    .filter((prediction) => prediction.prediction_type === "rul")
    .map((prediction) => prediction.asset_id);
  const assetIds = rulAssetIds.length
    ? new Set(rulAssetIds)
    : new Set([...profileByAsset.keys(), ...predictionByAsset.keys()]);

  return [...assetIds].sort().map((assetId) => {
    const profile = profileByAsset.get(assetId) || {};
    const prediction = predictionByAsset.get(assetId);
    const riskScore = Number(prediction?.risk_score ?? profile.failure_risk ?? 0);
    const rulValue = prediction?.prediction_type === "rul"
      && Number.isFinite(Number(prediction.remaining_useful_life_cycles))
      ? Number(prediction.remaining_useful_life_cycles)
      : null;
    const status = prediction?.asset_status || profileStatus(riskScore);
    return {
      ...profile,
      ...prediction,
      asset_id: assetId,
      risk_score: riskScore,
      health_score: prediction?.health_score === "" || prediction?.health_score === undefined
        ? null
        : Number(prediction.health_score),
      remaining_useful_life_cycles: rulValue,
      rul_available: rulValue !== null,
      asset_status: status,
      maintenance_priority: prediction?.maintenance_priority || profilePriority(status),
      recommended_action: prediction?.recommended_action || "Run predictive maintenance to calculate the latest recommendation.",
      display_updated: prediction?.scored_at ? formatDateTime(prediction.scored_at) : "Profile baseline",
      model_confidence: prediction?.model_confidence ?? null
    };
  });
}

function assetCounts(assets) {
  return assets.reduce((counts, asset) => {
    counts[asset.asset_status] = (counts[asset.asset_status] || 0) + 1;
    return counts;
  }, { healthy: 0, watch: 0, warning: 0, critical: 0 });
}

function operationalAlerts(data) {
  const assetAlerts = data.assets
    .filter((asset) => ["critical", "warning"].includes(asset.asset_status))
    .map((asset) => ({
      severity: asset.asset_status,
      title: `${asset.asset_id} is ${asset.asset_status}`,
      detail: asset.recommended_action,
      time: asset.display_updated,
      targetType: "asset",
      targetId: asset.asset_id
    }));
  const workflowAlerts = data.workflows
    .filter((workflow) => workflow.status === "failed")
    .map((workflow) => ({
      severity: "critical",
      title: "Workflow execution failed",
      detail: workflow.error || formatStepLabel(workflow.step),
      time: formatDateTime(workflow.updated_at),
      targetType: "workflow",
      targetId: workflow.run_id
    }));
  return [...assetAlerts, ...workflowAlerts];
}

function renderHeader(data) {
  const alerts = operationalAlerts(data);
  const latestWorkflow = data.workflows[0];
  const systemStatus = alerts.length ? `${alerts.length} issue${alerts.length === 1 ? "" : "s"}` : "Operational";

  document.getElementById("header-system-status").textContent = systemStatus;
  document.getElementById("header-system-status").title = alerts.length
    ? `${alerts.length} active asset or workflow condition${alerts.length === 1 ? "" : "s"} require review.`
    : "No active asset or workflow conditions.";
  document.getElementById("header-last-workflow").textContent = latestWorkflow
    ? `${workflowOutcome(latestWorkflow).label} · ${formatTime(latestWorkflow.updated_at)}`
    : "No runs";
  document.getElementById("last-workflow-button").disabled = !latestWorkflow;
  document.getElementById("notification-count").textContent = String(alerts.length);
  document.getElementById("notification-count").hidden = alerts.length === 0;
  document.getElementById("notification-summary").textContent = `${alerts.length} open`;
  renderNotifications(alerts);
  document.getElementById("sidebar-status-label").textContent = "API connected";
  document.getElementById("sidebar-status-dot").dataset.state = "healthy";
}

function renderNotifications(alerts) {
  document.getElementById("notification-list").innerHTML = alerts.length
    ? alerts.slice(0, 6).map((alert) => `
      <button type="button" class="notification-item" data-notification-type="${alert.targetType}" data-notification-id="${escapeHtml(alert.targetId)}">
        <span class="alert-icon ${alert.severity === "critical" ? "critical" : ""}"><i data-lucide="${alert.severity === "critical" ? "octagon-alert" : "triangle-alert"}"></i></span>
        <span><strong>${escapeHtml(alert.title)}</strong><small>${escapeHtml(alert.detail)}</small><time>${escapeHtml(alert.time)}</time></span>
        <i data-lucide="chevron-right" aria-hidden="true"></i>
      </button>
    `).join("")
    : '<div class="popover-empty"><i data-lucide="circle-check"></i><strong>No active notifications</strong><span>There are no conditions requiring review.</span></div>';
}

function renderSummary(data) {
  const counts = assetCounts(data.assets);
  const alerts = operationalAlerts(data);
  const terminalWorkflows = data.workflows.filter((workflow) => ["completed", "failed"].includes(workflow.status));
  const completedCount = terminalWorkflows.filter((workflow) => workflow.status === "completed").length;
  const successRate = terminalWorkflows.length ? Math.round((completedCount / terminalWorkflows.length) * 100) : null;
  const latestPrediction = [...data.predictions].sort((a, b) => (b.scored_at || "").localeCompare(a.scored_at || ""))[0];

  document.getElementById("total-assets-value").textContent = String(data.assets.length);
  document.getElementById("total-assets-note").textContent = data.assets.length ? "Monitored fleet inventory" : "Awaiting inventory";
  document.getElementById("healthy-assets-value").textContent = String(counts.healthy);
  document.getElementById("healthy-assets-note").textContent = data.assets.length ? `${Math.round((counts.healthy / data.assets.length) * 100)}% of monitored fleet` : "Awaiting predictions";
  document.getElementById("high-risk-assets-value").textContent = String(counts.critical + counts.warning);
  document.getElementById("high-risk-assets-note").textContent = `${counts.critical} critical · ${counts.warning} warning`;
  document.getElementById("active-alerts-value").textContent = String(alerts.length);
  document.getElementById("active-alerts-note").textContent = alerts.length ? "Requires operational review" : "No active alerts";
  document.getElementById("workflow-success-value").textContent = successRate === null ? "—" : `${successRate}%`;
  document.getElementById("workflow-success-note").textContent = terminalWorkflows.length ? `${terminalWorkflows.length} completed or failed runs` : "No execution history";
  document.getElementById("last-prediction-value").textContent = latestPrediction ? formatTime(latestPrediction.scored_at) : "None";
  document.getElementById("last-prediction-note").textContent = latestPrediction ? formatDateTime(latestPrediction.scored_at) : "No scored predictions";
  document.getElementById("overview-data-state").innerHTML = '<span class="status-dot healthy"></span>Live operational data';
  document.getElementById("assistant-asset-count").textContent = String(data.assets.length);
  document.getElementById("assistant-workflow-count").textContent = String(data.workflows.length);
  document.getElementById("asset-count-label").textContent = `${data.assets.length} assets`;
}

function renderFleetHealth(data) {
  const counts = assetCounts(data.assets);
  const maxCount = Math.max(...Object.values(counts), 1);
  const order = ["healthy", "watch", "warning", "critical"];
  document.getElementById("fleet-health-meta").textContent = `${data.assets.length} assets`;
  document.getElementById("fleet-health-chart").innerHTML = order.map((status) => {
    const height = Math.max((counts[status] / maxCount) * 100, counts[status] ? 8 : 2);
    return `<div class="fleet-bar-group"><strong>${counts[status]}</strong><div class="fleet-bar ${status}" style="height:${height}%"></div><span>${statusLabels[status]}</span></div>`;
  }).join("");
  document.getElementById("fleet-health-legend").innerHTML = order.map((status) => `
    <span class="legend-item"><span class="legend-swatch fleet-bar ${status}"></span>${statusLabels[status]} ${counts[status]}</span>
  `).join("");
}

function renderPredictions(data) {
  const counts = assetCounts(data.assets);
  const total = Math.max(data.assets.length, 1);
  const healthyShare = Math.round((counts.healthy / total) * 100);
  const watchShare = Math.round((counts.watch / total) * 100);
  const warningShare = Math.round((counts.warning / total) * 100);
  const criticalShare = Math.max(0, 100 - healthyShare - watchShare - warningShare);
  const reviewCount = counts.watch + counts.warning + counts.critical;
  const donut = document.getElementById("prediction-donut");
  const rulCount = data.predictions.filter((prediction) => prediction.prediction_type === "rul").length;
  const baselineCount = data.predictions.length - rulCount;

  document.getElementById("prediction-count").textContent = data.predictions.length
    ? `${rulCount} RUL · ${baselineCount} risk-only`
    : "Baseline risk profiles";
  document.getElementById("prediction-review-count").textContent = String(reviewCount);
  donut.style.background = data.assets.length
    ? `conic-gradient(var(--color-healthy) 0 ${healthyShare}%, var(--color-info) ${healthyShare}% ${healthyShare + watchShare}%, var(--color-warning) ${healthyShare + watchShare}% ${healthyShare + watchShare + warningShare}%, var(--color-critical) ${healthyShare + watchShare + warningShare}% 100%)`
    : "var(--color-border-strong)";

  const rows = [
    ["healthy", healthyShare],
    ["watch", watchShare],
    ["warning", warningShare],
    ["critical", criticalShare]
  ];
  document.getElementById("prediction-legend").innerHTML = rows.map(([status, share]) => `
    <div class="donut-legend-row"><span class="legend-swatch fleet-bar ${status}"></span><span>${statusLabels[status]}</span><strong>${share}%</strong></div>
  `).join("");
}

function renderOverviewWorkflows(data) {
  const workflows = data.workflows.slice(0, 4);
  document.getElementById("overview-workflow-list").innerHTML = workflows.length
    ? workflows.map((workflow) => `
      <button type="button" class="compact-row interactive-row" data-workflow-detail="${escapeHtml(workflow.run_id)}"><span class="status-dot" data-state="${workflowOutcome(workflow).status === "critical" || workflow.status === "failed" ? "error" : workflowOutcome(workflow).status}"></span><span class="row-copy"><strong>${escapeHtml(formatStepLabel(workflow.step))}</strong><small>${escapeHtml(workflowSummaryText(workflow) || formatDateTime(workflow.updated_at))}</small></span>${workflowStatusPill(workflow)}<i class="row-chevron" data-lucide="chevron-right"></i></button>
    `).join("")
    : '<div class="empty-state"><strong>No workflow history</strong><span>Run predictive maintenance to create the first execution.</span></div>';
}

function renderAlerts(data) {
  const alerts = operationalAlerts(data).slice(0, 5);
  document.getElementById("alert-panel-count").textContent = `${alerts.length} open`;
  document.getElementById("recent-alert-list").innerHTML = alerts.length
    ? alerts.map((alert) => `
      <button type="button" class="alert-row interactive-row" data-notification-type="${alert.targetType}" data-notification-id="${escapeHtml(alert.targetId)}"><span class="alert-icon ${alert.severity === "critical" ? "critical" : ""}"><i data-lucide="${alert.severity === "critical" ? "octagon-alert" : "triangle-alert"}"></i></span><span class="row-copy"><strong>${escapeHtml(alert.title)}</strong><small>${escapeHtml(alert.detail)}</small></span><span class="cell-muted">${escapeHtml(alert.time)}</span><i class="row-chevron" data-lucide="chevron-right"></i></button>
    `).join("")
    : '<div class="empty-state"><i data-lucide="circle-check"></i><strong>No active alerts</strong><span>The fleet has no critical asset or workflow conditions.</span></div>';
}

function assetRow(asset, compact = false) {
  const rul = `<span class="rul-chip${asset.rul_available ? "" : " rul-unavailable"}">${escapeHtml(formatRul(asset.remaining_useful_life_cycles))}</span>`;
  if (compact) {
    return `<tr class="interactive-table-row" data-asset-detail="${escapeHtml(asset.asset_id)}" tabindex="0" role="button" aria-label="View ${escapeHtml(asset.asset_id)} details"><td><div class="asset-identity"><strong>${escapeHtml(asset.asset_id)}</strong><span>${escapeHtml(asset.model_name || "Baseline profile")}</span></div></td><td>${statusPill(asset.asset_status)}</td><td><span class="risk-chip">${asset.risk_score.toFixed(2)}</span></td><td>${rul}</td><td>${escapeHtml(asset.maintenance_priority)}</td><td class="recommendation-cell" title="${escapeHtml(asset.recommended_action)}">${escapeHtml(asset.recommended_action)}</td><td>${escapeHtml(asset.display_updated)}</td></tr>`;
  }
  return `<tr class="interactive-table-row" data-asset-detail="${escapeHtml(asset.asset_id)}" tabindex="0" role="button" aria-label="View ${escapeHtml(asset.asset_id)} details"><td><div class="asset-identity"><strong>${escapeHtml(asset.asset_id)}</strong><span>${escapeHtml(asset.model_name || "Baseline profile")}</span></div></td><td>${statusPill(asset.asset_status)}</td><td><span class="risk-chip">${asset.risk_score.toFixed(2)}</span></td><td>${rul}</td><td>${escapeHtml(asset.maintenance_priority)}</td><td class="recommendation-cell" title="${escapeHtml(asset.recommended_action)}">${escapeHtml(asset.recommended_action)}</td><td>${escapeHtml(asset.display_updated)}</td><td><span class="row-detail-indicator" aria-hidden="true"><i data-lucide="chevron-right"></i></span></td></tr>`;
}

function renderRiskAssets(data) {
  const rows = [...data.assets].sort((a, b) => b.risk_score - a.risk_score).slice(0, 5);
  document.getElementById("risk-asset-table-body").innerHTML = rows.length
    ? rows.map((asset) => assetRow(asset, true)).join("")
    : '<tr><td colspan="7"><div class="empty-state">No asset data available.</div></td></tr>';
}

function filteredAssets(data) {
  const searchValue = document.getElementById("asset-search").value.trim().toLowerCase();
  const statusValue = document.getElementById("asset-status-filter").value;
  const sortValue = document.getElementById("asset-sort").value;
  const rows = data.assets.filter((asset) => {
    const matchesSearch = !searchValue || asset.asset_id.toLowerCase().includes(searchValue);
    const matchesStatus = statusValue === "all" || asset.asset_status === statusValue;
    return matchesSearch && matchesStatus;
  });

  return rows.sort((a, b) => {
    if (sortValue === "rul-asc") {
      if (a.rul_available !== b.rul_available) return a.rul_available ? -1 : 1;
      return a.rul_available
        ? a.remaining_useful_life_cycles - b.remaining_useful_life_cycles
        : a.asset_id.localeCompare(b.asset_id);
    }
    if (sortValue === "risk-asc") return a.risk_score - b.risk_score;
    if (sortValue === "asset-asc") return a.asset_id.localeCompare(b.asset_id);
    if (sortValue === "updated-desc") return (b.scored_at || "").localeCompare(a.scored_at || "");
    return b.risk_score - a.risk_score;
  });
}

function renderAssets(data) {
  const rows = filteredAssets(data);
  document.getElementById("asset-table-body").innerHTML = rows.map((asset) => assetRow(asset)).join("");
  const emptyState = document.getElementById("asset-empty-state");
  emptyState.hidden = rows.length > 0;
  emptyState.innerHTML = data.assets.length
    ? '<i data-lucide="search-x"></i><strong>No assets found</strong><span>Adjust the search or status filter.</span>'
    : '<i data-lucide="activity"></i><strong>No current RUL results</strong><span>Run checkpoint 1 to evaluate the demonstration engines.</span>';
  refreshIcons();
}

function renderWorkflowStates(data) {
  const states = [
    ["running", "loader-circle"],
    ["completed", "circle-check"],
    ["failed", "circle-x"]
  ];
  document.getElementById("workflow-state-row").innerHTML = states.map(([state, icon]) => {
    const count = data.workflows.filter((workflow) => workflow.status === state).length;
    const selected = workflowFilter === state;
    return `<button type="button" class="workflow-state-card" data-workflow-filter="${state}" aria-pressed="${selected}"><i data-lucide="${icon}"></i><span>${statusLabels[state]} runs</span><strong>${count}</strong></button>`;
  }).join("");
}

function renderWorkflows(data) {
  const workflows = workflowFilter === "all"
    ? data.workflows
    : data.workflows.filter((workflow) => workflow.status === workflowFilter);
  const countLabel = `${workflows.length} run${workflows.length === 1 ? "" : "s"}`;
  document.getElementById("workflow-run-count").textContent = `${statusLabels[workflowFilter] || "All"} · ${countLabel}`;
  document.getElementById("workflow-run-count-default").textContent = `${data.workflows.length} runs`;
  document.getElementById("workflow-filter-clear").hidden = workflowFilter === "all";
  document.getElementById("workflow-run-count-default").hidden = workflowFilter !== "all";
  document.getElementById("workflow-list").innerHTML = workflows.length
    ? workflows.map((workflow) => `
      <button type="button" class="workflow-item" data-workflow-detail="${escapeHtml(workflow.run_id)}" aria-label="View workflow run details"><span class="workflow-item-icon"><i data-lucide="git-branch"></i></span><span class="workflow-item-copy"><strong>Predictive maintenance</strong><small>${escapeHtml(workflowSummaryText(workflow) || formatStepLabel(workflow.step))} · ${escapeHtml(formatDateTime(workflow.updated_at))}${workflow.error ? ` · ${escapeHtml(workflow.error)}` : ""}</small></span>${workflowStatusPill(workflow)}<i class="row-chevron" data-lucide="chevron-right"></i></button>
    `).join("")
    : `<div class="empty-state"><i data-lucide="workflow"></i><strong>No ${workflowFilter === "all" ? "workflow" : workflowFilter} runs</strong><span>${workflowFilter === "all" ? "Start predictive maintenance to create execution history." : "Select the active filter again or clear it to view all executions."}</span></div>`;
  renderWorkflowStates(data);
  renderPipelineTimeline(workflows[0]);
  document.getElementById("workflow-timeline-kicker").textContent = workflowFilter === "all" ? "Latest execution" : `Latest ${workflowFilter} execution`;
}

function renderRulDemo(data) {
  const demo = data.demo;
  const runButton = document.getElementById("run-workflow-button");
  const resetButton = document.getElementById("reset-rul-demo-button");
  if (!demo) {
    runButton.disabled = true;
    resetButton.disabled = true;
    return;
  }
  const statusLabels = {
    ready: "Ready",
    in_progress: "In progress",
    running: "Running",
    complete: "Complete"
  };
  document.getElementById("rul-demo-status").textContent = statusLabels[demo.status] || demo.status;
  const next = demo.next_checkpoint;
  document.getElementById("rul-demo-description").textContent = demo.status === "complete"
    ? `All ${demo.total_checkpoints} checkpoints are complete. Reset to replay the same model inputs and results.`
    : `${demo.engine_ids.length} held-out engines · Next: checkpoint ${next.number} of ${demo.total_checkpoints}, ${next.label}.`;
  document.getElementById("rul-demo-progress").innerHTML = demo.checkpoint_labels.map((label, index) => {
    const number = index + 1;
    const state = number <= demo.completed_checkpoints
      ? "complete"
      : number === demo.completed_checkpoints + 1 && demo.status !== "complete"
        ? "next"
        : "pending";
    const stateLabel = state === "complete" ? "Completed" : state === "next" ? "Next run" : "Pending";
    return `<div class="rul-demo-checkpoint ${state}"><strong>${number}. ${escapeHtml(label)}</strong><span>${stateLabel}</span></div>`;
  }).join("");
  runButton.disabled = demo.status === "running" || demo.status === "complete";
  resetButton.disabled = demo.status === "running";
  runButton.querySelector("span").textContent = demo.status === "complete"
    ? "Demo complete"
    : `Run checkpoint ${demo.completed_checkpoints + 1}`;
}

function renderPipelineTimeline(workflow, targetId = "pipeline-timeline") {
  const timeline = document.getElementById(targetId);
  const baselineSteps = [
    ["queued", "Request queued"],
    ["telemetry_and_feature_processing", "Generate telemetry and features"],
    ["score_and_persist_predictions", "Rule-based risk scoring"],
    ["completed", "Publish operational results"]
  ];
  const rulSteps = [
    ["queued", "Request queued"],
    ["simulate_rul_demo_telemetry", "Replay engine telemetry"],
    ["rul_inference_and_persistence", "Random Forest RUL inference"],
    ["completed", "Publish operational results"]
  ];
  const steps = [
    "telemetry_and_feature_processing",
    "score_and_persist_predictions"
  ].includes(workflow?.step) ? baselineSteps : rulSteps;
  if (!workflow) {
    timeline.innerHTML = '<div class="empty-state"><strong>No execution selected</strong><span>The latest run timeline will appear here.</span></div>';
    return;
  }

  const currentIndex = workflow.status === "completed"
    ? steps.length - 1
    : Math.max(steps.findIndex(([key]) => key === workflow.step), 0);
  timeline.innerHTML = steps.map(([, label], index) => {
    let state = index < currentIndex || workflow.status === "completed" ? "complete" : index === currentIndex ? "current" : "pending";
    if (workflow.status === "failed" && index === currentIndex) state = "failed";
    const detail = state === "complete" ? "Completed" : state === "current" ? "Current step" : state === "failed" ? "Failed" : "Pending";
    return `<div class="timeline-step ${state}"><span class="timeline-marker"></span><div><strong>${label}</strong><span>${detail}</span></div></div>`;
  }).join("");
}

function openAssetDetails(assetId) {
  const asset = dashboardData.assets.find((candidate) => candidate.asset_id === assetId);
  if (!asset) return;
  const rulSummary = formatRul(asset.remaining_useful_life_cycles);
  const explanation = asset.rul_available
    ? `The versioned Random Forest model estimates ${rulSummary} for the latest compatible engine cycle. Risk and health are bounded operational indicators derived from that maintenance horizon. This FD001 benchmark estimate supports prioritization and is not a guaranteed failure date.`
    : "RUL is unavailable because no compatible stored remaining-useful-life prediction exists for this asset. The displayed risk is a separate rule-based indicator; SentinelOps does not substitute it for an RUL estimate.";
  const supportingDetails = asset.rul_available
    ? `<section class="detail-section"><h3>Result traceability</h3><dl><div><dt>Workflow run</dt><dd class="run-identifier">${escapeHtml(asset.run_id)}</dd></div><div><dt>Feature contract</dt><dd>${escapeHtml(asset.feature_contract_version || "Not reported")}</dd></div></dl></section>`
    : `<section class="detail-section"><h3>Feature summary</h3><dl><div><dt>Base temperature</dt><dd>${escapeHtml(asset.base_temperature_c ?? "Not available")} °C</dd></div><div><dt>Base vibration</dt><dd>${escapeHtml(asset.base_vibration_mm_s ?? "Not available")} mm/s</dd></div><div><dt>Base pressure</dt><dd>${escapeHtml(asset.base_pressure_kpa ?? "Not available")} kPa</dd></div><div><dt>Runtime</dt><dd>${escapeHtml(asset.runtime_hours ?? "Not available")} hours</dd></div></dl></section>`;
  document.getElementById("asset-dialog-title").textContent = asset.asset_id;
  document.getElementById("asset-dialog-content").innerHTML = `
    <section class="detail-summary"><div class="detail-metric"><span>Condition</span>${statusPill(asset.asset_status)}</div><div class="detail-metric"><span>Risk Score</span><strong>${asset.risk_score.toFixed(2)}</strong></div><div class="detail-metric"><span>RUL</span><strong>${escapeHtml(rulSummary)}</strong></div><div class="detail-metric"><span>Priority</span><strong>${escapeHtml(asset.maintenance_priority)}</strong></div></section>
    <section class="maintenance-callout"><strong>Recommended maintenance</strong>${escapeHtml(asset.recommended_action)}</section>
    <section class="detail-section"><h3>Latest prediction</h3><dl><div><dt>Prediction type</dt><dd>${asset.rul_available ? "Remaining useful life" : "Risk-only baseline"}</dd></div><div><dt>Health score</dt><dd>${escapeHtml(formatPercent(asset.health_score))}</dd></div><div><dt>Model</dt><dd>${escapeHtml(asset.model_name || "Rule-based baseline")}</dd></div><div><dt>Model version</dt><dd>${escapeHtml(asset.model_version || "Baseline")}</dd></div><div><dt>Prediction timestamp</dt><dd>${escapeHtml(asset.display_updated)}</dd></div><div><dt>Dataset</dt><dd>${escapeHtml(asset.dataset_id || "Not applicable")}</dd></div></dl></section>
    ${supportingDetails}
    <section class="detail-section"><h3>Prediction explanation</h3><p class="prediction-explanation">${escapeHtml(explanation)}</p></section>
  `;
  document.getElementById("asset-detail-dialog").showModal();
  refreshIcons();
}

function openWorkflowDetails(runId) {
  const workflow = dashboardData.workflows.find((candidate) => candidate.run_id === runId);
  if (!workflow) return;
  const summary = workflow.result_summary;
  document.getElementById("workflow-dialog-title").textContent = `Predictive maintenance · ${workflowOutcome(workflow).label}`;
  document.getElementById("workflow-dialog-content").innerHTML = `
    <section class="detail-summary workflow-detail-summary"><div class="detail-metric"><span>Execution</span>${statusPill(workflow.status)}</div><div class="detail-metric"><span>Asset outcome</span>${workflowStatusPill(workflow)}</div><div class="detail-metric"><span>Updated</span><strong>${escapeHtml(formatDateTime(workflow.updated_at))}</strong></div></section>
    ${summary ? `<section class="detail-section"><h3>Condition summary</h3><p class="prediction-explanation">${escapeHtml(workflowSummaryText(workflow))}</p><dl><div><dt>Assets evaluated</dt><dd>${summary.asset_count}</dd></div><div><dt>Highest risk</dt><dd>${Number(summary.highest_risk_score).toFixed(2)}</dd></div><div><dt>Shortest RUL</dt><dd>${escapeHtml(summary.shortest_rul_cycles === null ? "Not applicable" : `${Number(summary.shortest_rul_cycles).toFixed(1)} cycles`)}</dd></div></dl></section>` : ""}
    <section class="detail-section"><h3>Execution details</h3><dl><div><dt>Workflow</dt><dd>Predictive maintenance</dd></div><div><dt>Run identifier</dt><dd class="run-identifier">${escapeHtml(workflow.run_id)}</dd></div><div><dt>Execution state</dt><dd>${escapeHtml(statusLabels[workflow.status] || workflow.status)}</dd></div><div><dt>Last activity</dt><dd>${escapeHtml(formatDateTime(workflow.updated_at))}</dd></div></dl></section>
    ${workflow.error ? `<section class="execution-error"><strong>Failure details</strong><p>${escapeHtml(workflow.error)}</p></section>` : ""}
    <section class="detail-section"><h3>Pipeline progress</h3><div class="pipeline-timeline dialog-timeline" id="workflow-dialog-timeline"></div></section>
  `;
  renderPipelineTimeline(workflow, "workflow-dialog-timeline");
  document.getElementById("workflow-detail-dialog").showModal();
  refreshIcons();
}

function renderAll(data) {
  renderHeader(data);
  renderSummary(data);
  renderFleetHealth(data);
  renderPredictions(data);
  renderOverviewWorkflows(data);
  renderAlerts(data);
  renderRiskAssets(data);
  renderAssets(data);
  renderWorkflows(data);
  renderRulDemo(data);
  refreshIcons();
}

function setSystemState(state, message) {
  document.getElementById("sidebar-status-label").textContent = message;
  document.getElementById("sidebar-status-dot").dataset.state = state;
  document.getElementById("overview-data-state").innerHTML = `<span class="status-dot" data-state="${state}"></span>${escapeHtml(message)}`;
}

function showToast(message, state = "info") {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.dataset.state = state;
  toast.innerHTML = `<i data-lucide="${state === "success" ? "circle-check" : state === "error" ? "circle-x" : "info"}"></i><span>${escapeHtml(message)}</span>`;
  document.getElementById("toast-region").appendChild(toast);
  refreshIcons();
  window.setTimeout(() => toast.remove(), 4200);
}

async function refreshDashboard({ announce = true } = {}) {
  const actionStatus = document.getElementById("workflow-action-status");
  const refreshButton = document.querySelector(".refresh-button");
  const refreshLabel = refreshButton.querySelector("span");
  refreshButton.disabled = true;
  refreshButton.classList.add("is-refreshing");
  refreshLabel.textContent = "Refreshing";
  setSystemState("loading", "Refreshing");
  try {
    const [assetData, rulPredictionData, workflowData, demoData] = await Promise.all([
      apiFetch("/api/assets"),
      optionalApiFetch("/api/predictions/rul/latest"),
      apiFetch("/api/workflows"),
      apiFetch("/api/workflows/rul-demo/status")
    ]);
    dashboardData.profiles = assetData.assets || [];
    const currentRulPredictions = rulPredictionData.predictions || [];
    dashboardData.predictions = currentRulPredictions;
    dashboardData.assets = normalizeAssets([], dashboardData.predictions);
    dashboardData.workflows = (workflowData.workflows || []).map((workflow) => ({
      ...workflow,
      label: formatStepLabel(workflow.step)
    }));
    dashboardData.demo = demoData.scenario;
    renderAll(dashboardData);
    document.getElementById("last-refresh-value").textContent = formatDateTime(new Date());
    if (announce) {
      refreshLabel.textContent = "Updated";
    }
    if (announce) showToast("Operational data refreshed.", "success");
  } catch (error) {
    setSystemState("error", "API unavailable");
    actionStatus.textContent = error.message;
    actionStatus.dataset.state = "error";
    if (announce) showToast(error.message, "error");
  } finally {
    refreshButton.classList.remove("is-refreshing");
    window.setTimeout(() => {
      refreshButton.disabled = false;
      refreshLabel.textContent = "Refresh";
    }, announce ? 900 : 0);
  }
}

async function runWorkflow() {
  const button = document.getElementById("run-workflow-button");
  const actionStatus = document.getElementById("workflow-action-status");
  button.disabled = true;
  actionStatus.textContent = "Starting predictive maintenance workflow...";
  actionStatus.dataset.state = "loading";
  try {
    const response = await fetch("/api/workflows", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workflow: "predictive-maintenance",
        inference_mode: "rul",
        model_version: "1.0.0"
      })
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Workflow could not be started.");
    actionStatus.textContent = "RUL workflow accepted. Processing simulated engine telemetry...";
    actionStatus.dataset.state = "loading";
    const workflow = await waitForWorkflowCompletion(payload.data.workflow.run_id);
    if (workflow.status === "failed") {
      throw new Error(workflow.error || "The RUL workflow failed.");
    }
    const summary = workflowSummaryText(workflow);
    actionStatus.textContent = `RUL checkpoint completed: ${summary || "no asset summary was returned"}.`;
    const outcomeStatus = workflow.result_summary?.outcome_status;
    actionStatus.dataset.state = workflow.result_summary?.finding_count
      ? outcomeStatus
      : "success";
    showToast(
      summary || "RUL checkpoint completed.",
      outcomeStatus === "critical" ? "error" : outcomeStatus === "healthy" ? "success" : "info"
    );
    await refreshDashboard({ announce: false });
  } catch (error) {
    actionStatus.textContent = error.message;
    actionStatus.dataset.state = "error";
    showToast(error.message, "error");
  } finally {
    button.disabled = ["running", "complete"].includes(dashboardData.demo?.status);
  }
}

async function waitForWorkflowCompletion(runId) {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const data = await apiFetch(`/api/workflows/${encodeURIComponent(runId)}`);
    if (["completed", "failed"].includes(data.workflow.status)) return data.workflow;
    await new Promise((resolve) => window.setTimeout(resolve, 250));
  }
  throw new Error("The workflow is still running. Refresh to check its status.");
}

async function resetRulDemo() {
  const button = document.getElementById("reset-rul-demo-button");
  const actionStatus = document.getElementById("workflow-action-status");
  button.disabled = true;
  actionStatus.textContent = "Resetting the RUL lifecycle scenario...";
  actionStatus.dataset.state = "loading";
  try {
    const response = await fetch("/api/workflows/rul-demo/reset", { method: "POST" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The RUL demo could not be reset.");
    dashboardData.demo = payload.data.scenario;
    await refreshDashboard({ announce: false });
    actionStatus.textContent =
      "RUL demo reset. Prior run evidence remains available by direct run URL.";
    actionStatus.dataset.state = "success";
    showToast("RUL demo ready at checkpoint 1.", "success");
  } catch (error) {
    actionStatus.textContent = error.message;
    actionStatus.dataset.state = "error";
    showToast(error.message, "error");
  } finally {
    button.disabled = dashboardData.demo?.status === "running";
  }
}

function assistantResultItems(response) {
  if (!response.items?.length) return "";
  if (["compare_rul", "explain_asset_rul"].includes(response.intent)) {
    return `<div class="assistant-result-list">${response.items.map((item) => `
      <button type="button" data-asset-detail="${escapeHtml(item.asset_id)}"><span><strong>${escapeHtml(item.asset_id)}</strong><small>${escapeHtml(item.maintenance_priority || "Priority unavailable")} · ${escapeHtml(item.recommended_action || "Recommendation unavailable")}</small></span><span class="rul-chip">${escapeHtml(formatRul(item.remaining_useful_life_cycles))}</span><i data-lucide="chevron-right"></i></button>
    `).join("")}</div>`;
  }
  if (["highest_risk_assets", "explain_asset_prediction"].includes(response.intent)) {
    return `<div class="assistant-result-list">${response.items.map((item) => `
      <button type="button" data-asset-detail="${escapeHtml(item.asset_id)}"><span><strong>${escapeHtml(item.asset_id)}</strong><small>${escapeHtml(item.recommended_action || "Prediction result")}</small></span><span class="risk-chip">${Number(item.risk_score || 0).toFixed(2)}</span><i data-lucide="chevron-right"></i></button>
    `).join("")}</div>`;
  }
  if (["workflow_failures", "workflow_summary"].includes(response.intent)) {
    return `<div class="assistant-result-list">${response.items.map((item) => `
      <button type="button" data-workflow-detail="${escapeHtml(item.run_id)}"><span><strong>Predictive maintenance</strong><small>${escapeHtml(formatStepLabel(item.step))} · ${escapeHtml(formatDateTime(item.updated_at))}</small></span>${statusPill(item.status)}<i data-lucide="chevron-right"></i></button>
    `).join("")}</div>`;
  }
  return `<div class="assistant-result-list">${response.items.slice(0, 5).map((item) => `
    <button type="button" data-asset-detail="${escapeHtml(item.asset_id)}"><span><strong>${escapeHtml(item.asset_id)}</strong><small>Monitored asset</small></span><i data-lucide="chevron-right"></i></button>
  `).join("")}</div>`;
}

function assistantActionCard(response) {
  const action = response?.action_request;
  if (!action) return "";
  return `
    <section class="assistant-action-card" data-approval-card="${escapeHtml(action.approval_id)}" data-state="pending" aria-label="Approval required">
      <div class="assistant-action-heading"><span><i data-lucide="shield-alert"></i></span><div><strong>Approval required</strong><small>Review this protected operation before it runs.</small></div></div>
      <div class="assistant-action-impact"><strong>Start predictive maintenance</strong><p>${escapeHtml(action.impact)}</p></div>
      <dl class="assistant-action-details">
        <div><dt>Expires</dt><dd>${escapeHtml(formatDateTime(action.expires_at))}</dd></div>
        <div><dt>Request fingerprint</dt><dd class="approval-fingerprint">${escapeHtml(action.fingerprint)}</dd></div>
      </dl>
      <p class="assistant-action-status" data-approval-status role="status" aria-live="polite">Waiting for your decision.</p>
      <div class="assistant-action-controls">
        <button type="button" class="button button-secondary" data-assistant-decision="denied" data-approval-id="${escapeHtml(action.approval_id)}">Reject</button>
        <button type="button" class="button button-primary" data-assistant-decision="approved" data-approval-id="${escapeHtml(action.approval_id)}"><i data-lucide="play"></i>Approve and run</button>
      </div>
    </section>`;
}

function assistantWorkflowLink(response) {
  const workflow = response?.workflow;
  if (!workflow?.run_id) return "";
  const runId = escapeHtml(workflow.run_id);
  const completed = workflow.status === "completed";
  return `
    <a class="assistant-workflow-link" href="?view=assistant" data-workflow-link="${runId}">
      <span><i data-lucide="${completed ? "circle-check" : "workflow"}"></i></span>
      <span><strong>${completed ? "View completed workflow" : "View workflow run"}</strong><small>${runId}</small></span>
      ${workflowStatusPill(workflow)}
      <i data-lucide="arrow-right"></i>
    </a>`;
}

function appendAssistantMessage(role, content, response = null) {
  const transcript = document.getElementById("assistant-transcript");
  const message = document.createElement("section");
  message.className = `assistant-message assistant-message-${role}`;
  if (role === "user") {
    message.innerHTML = `<span class="assistant-message-icon"><i data-lucide="user"></i></span><div><span class="assistant-message-label">You</span><p>${escapeHtml(content)}</p></div>`;
  } else {
    const model = response?.model
      ? `<span>${escapeHtml(response.provider || "model")} · ${escapeHtml(response.model)}</span>`
      : "";
    const tools = response?.tool_calls?.length
      ? `<div class="assistant-tool-evidence"><i data-lucide="wrench"></i>${model}${response.tool_calls.map((tool) => `<span>${escapeHtml(tool.name)} · ${tool.read_only ? "read only" : "approval required"}</span>`).join("")}</div>`
      : "";
    message.innerHTML = `<span class="assistant-message-icon"><i data-lucide="bot"></i></span><div><span class="assistant-message-label">SentinelOps Assistant</span><p>${escapeHtml(content)}</p>${assistantResultItems(response || {})}${assistantActionCard(response)}${assistantWorkflowLink(response)}${tools}</div>`;
  }
  transcript.appendChild(message);
  transcript.scrollTop = transcript.scrollHeight;
  refreshIcons();
}

function findAssistantApprovalCard(approvalId) {
  return [...document.querySelectorAll("[data-approval-card]")]
    .find((card) => card.dataset.approvalCard === approvalId);
}

async function decideAssistantAction(decision, approvalId) {
  if (!pendingAssistantAction || pendingAssistantAction.approval_id !== approvalId) return;
  const card = findAssistantApprovalCard(approvalId);
  if (!card) return;
  const approveButton = card.querySelector('[data-assistant-decision="approved"]');
  const denyButton = card.querySelector('[data-assistant-decision="denied"]');
  const controls = card.querySelector(".assistant-action-controls");
  const status = card.querySelector("[data-approval-status]");
  approveButton.disabled = true;
  denyButton.disabled = true;
  status.textContent = decision === "approved" ? "Approving and starting the workflow..." : "Rejecting the action...";
  status.dataset.state = "loading";
  try {
    const decisionResponse = await fetch(`/api/assistant/approvals/${encodeURIComponent(pendingAssistantAction.approval_id)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision })
    });
    const decisionPayload = await decisionResponse.json();
    if (!decisionResponse.ok) throw new Error(decisionPayload.detail || "The approval decision could not be recorded.");
    if (decision === "denied") {
      status.textContent = "Action rejected. No workflow was started.";
      status.dataset.state = "success";
      card.dataset.state = "denied";
      controls.hidden = true;
      appendAssistantMessage("assistant", "The workflow action was rejected. No operational change was made.");
      pendingAssistantAction = null;
      return;
    }
    const executionResponse = await fetch("/api/assistant/actions/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        approval_id: pendingAssistantAction.approval_id,
        action: pendingAssistantAction.action,
        arguments: pendingAssistantAction.arguments
      })
    });
    const executionPayload = await executionResponse.json();
    if (!executionResponse.ok) throw new Error(executionPayload.detail || "The approved action could not be executed.");
    const acceptedWorkflow = executionPayload.data.workflow;
    const runId = acceptedWorkflow.run_id;
    const terminalWorkflow = await waitForWorkflowCompletion(runId);
    await refreshDashboard({ announce: false });
    const workflow = dashboardData.workflows.find((candidate) => candidate.run_id === runId) || terminalWorkflow;
    const completed = workflow.status === "completed";
    status.textContent = completed
      ? `Approved. Workflow completed as ${runId}.`
      : `Approved. Workflow started as ${runId}.`;
    status.dataset.state = "success";
    card.dataset.state = "approved";
    controls.hidden = true;
    pendingAssistantAction = null;
    appendAssistantMessage(
      "assistant",
      completed
        ? `The approved workflow execution completed. ${workflowSummaryText(workflow) || "Open the result for details."}`
        : "The approved predictive-maintenance workflow started successfully.",
      { workflow }
    );
    const assistantOutcome = workflow.result_summary?.outcome_status;
    showToast(
      completed ? workflowSummaryText(workflow) || "Approved workflow completed." : "Approved workflow started.",
      assistantOutcome === "critical" ? "error" : assistantOutcome && assistantOutcome !== "healthy" ? "info" : "success"
    );
  } catch (error) {
    status.textContent = error.message;
    status.dataset.state = "error";
    approveButton.disabled = false;
    denyButton.disabled = false;
  }
}

async function submitAssistantQuery(message) {
  const input = document.getElementById("assistant-input");
  const button = document.getElementById("assistant-send-button");
  const query = message.trim();
  if (!query || button.disabled) return;
  appendAssistantMessage("user", query);
  input.value = "";
  input.disabled = true;
  button.disabled = true;
  button.classList.add("is-loading");
  try {
    const response = await fetch("/api/assistant/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: query })
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The operational query could not be completed.");
    document.getElementById("assistant-model-name").textContent = payload.data.response.model;
    if (payload.data.response.action_request) pendingAssistantAction = payload.data.response.action_request;
    appendAssistantMessage("assistant", payload.data.response.answer, payload.data.response);
  } catch (error) {
    appendAssistantMessage("assistant", error.message, { intent: "error", tool_calls: [], items: [] });
  } finally {
    input.disabled = false;
    button.disabled = false;
    button.classList.remove("is-loading");
    input.focus();
  }
}

function showView(viewName) {
  document.querySelectorAll("[data-view]").forEach((view) => {
    view.hidden = view.dataset.view !== viewName;
  });
  document.querySelectorAll("[data-view-target]").forEach((control) => {
    if (control.classList.contains("nav-item")) {
      if (control.dataset.viewTarget === viewName) control.setAttribute("aria-current", "page");
      else control.removeAttribute("aria-current");
    }
  });
  document.getElementById("header-view-title").textContent = viewTitles[viewName] || "Operations Console";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function closeHeaderPopovers(exceptId = null) {
  ["notification-popover", "user-popover"].forEach((id) => {
    if (id === exceptId) return;
    document.getElementById(id).hidden = true;
  });
  document.getElementById("notification-button").setAttribute("aria-expanded", String(exceptId === "notification-popover"));
  document.getElementById("user-menu-button").setAttribute("aria-expanded", String(exceptId === "user-popover"));
}

function toggleHeaderPopover(popoverId, buttonId) {
  const popover = document.getElementById(popoverId);
  const willOpen = popover.hidden;
  closeHeaderPopovers(willOpen ? popoverId : null);
  popover.hidden = !willOpen;
  document.getElementById(buttonId).setAttribute("aria-expanded", String(willOpen));
}

async function initDashboard() {
  renderAll(dashboardData);
  const requestedParameters = new URLSearchParams(window.location.search);
  const requestedView = requestedParameters.get("view");
  showView(Object.hasOwn(viewTitles, requestedView) ? requestedView : "overview");

  document.getElementById("asset-search").addEventListener("input", () => renderAssets(dashboardData));
  document.getElementById("asset-status-filter").addEventListener("change", () => renderAssets(dashboardData));
  document.getElementById("asset-sort").addEventListener("change", () => renderAssets(dashboardData));
  document.getElementById("run-workflow-button").addEventListener("click", runWorkflow);
  document.getElementById("reset-rul-demo-button").addEventListener("click", resetRulDemo);
  document.querySelector(".refresh-button").addEventListener("click", () => refreshDashboard());
  document.getElementById("notification-button").addEventListener("click", () => toggleHeaderPopover("notification-popover", "notification-button"));
  document.getElementById("system-summary-button").addEventListener("click", () => toggleHeaderPopover("notification-popover", "notification-button"));
  document.getElementById("last-workflow-button").addEventListener("click", () => {
    if (!dashboardData.workflows[0]) return;
    openWorkflowDetails(dashboardData.workflows[0].run_id);
  });
  document.getElementById("user-menu-button").addEventListener("click", () => toggleHeaderPopover("user-popover", "user-menu-button"));
  document.getElementById("assistant-form").addEventListener("submit", (event) => {
    event.preventDefault();
    submitAssistantQuery(document.getElementById("assistant-input").value);
  });
  document.querySelectorAll("[data-assistant-prompt]").forEach((button) => {
    button.addEventListener("click", () => submitAssistantQuery(button.dataset.assistantPrompt));
  });
  document.getElementById("workflow-filter-clear").addEventListener("click", () => {
    workflowFilter = "all";
    renderWorkflows(dashboardData);
    refreshIcons();
  });
  document.getElementById("close-asset-dialog").addEventListener("click", () => document.getElementById("asset-detail-dialog").close());
  document.getElementById("asset-detail-dialog").addEventListener("click", (event) => {
    if (event.target === event.currentTarget) event.currentTarget.close();
  });
  document.getElementById("close-workflow-dialog").addEventListener("click", () => document.getElementById("workflow-detail-dialog").close());
  document.getElementById("workflow-detail-dialog").addEventListener("click", (event) => {
    if (event.target === event.currentTarget) event.currentTarget.close();
  });
  document.addEventListener("click", (event) => {
    const viewControl = event.target.closest("[data-view-target]");
    if (viewControl) showView(viewControl.dataset.viewTarget);
    const assetControl = event.target.closest("[data-asset-detail]");
    if (assetControl) openAssetDetails(assetControl.dataset.assetDetail);
    const workflowControl = event.target.closest("[data-workflow-detail]");
    if (workflowControl) openWorkflowDetails(workflowControl.dataset.workflowDetail);
    const workflowLink = event.target.closest("[data-workflow-link]");
    if (workflowLink) {
      event.preventDefault();
      openWorkflowDetails(workflowLink.dataset.workflowLink);
    }
    const actionControl = event.target.closest("[data-assistant-decision]");
    if (actionControl) {
      decideAssistantAction(actionControl.dataset.assistantDecision, actionControl.dataset.approvalId);
    }
    const filterControl = event.target.closest("[data-workflow-filter]");
    if (filterControl) {
      workflowFilter = workflowFilter === filterControl.dataset.workflowFilter ? "all" : filterControl.dataset.workflowFilter;
      renderWorkflows(dashboardData);
      refreshIcons();
    }
    const notificationControl = event.target.closest("[data-notification-type]");
    if (notificationControl) {
      closeHeaderPopovers();
      if (notificationControl.dataset.notificationType === "asset") {
        openAssetDetails(notificationControl.dataset.notificationId);
      } else {
        openWorkflowDetails(notificationControl.dataset.notificationId);
      }
    }
    const accountControl = event.target.closest("[data-account-action]");
    if (accountControl) {
      closeHeaderPopovers();
      const labels = { profile: "Profile management", settings: "Settings", logout: "Sign out" };
      showToast(`${labels[accountControl.dataset.accountAction]} is not connected in this MVP.`, "info");
    }
    if (!event.target.closest(".popover-anchor")) closeHeaderPopovers();
  });
  document.addEventListener("keydown", (event) => {
    if (!event.target.matches(".interactive-table-row")) return;
    if (!["Enter", " "].includes(event.key)) return;
    event.preventDefault();
    openAssetDetails(event.target.dataset.assetDetail);
  });

  refreshIcons();
  await refreshDashboard({ announce: false });
}

document.addEventListener("DOMContentLoaded", initDashboard);
