const dashboardData = { assets: [], predictions: [], workflows: [] };

const statusLabels = {
  critical: "Critical",
  warning: "Warning",
  watch: "Watch",
  healthy: "Healthy",
  failed: "Failed",
  running: "Running",
  completed: "Completed",
  ok: "OK",
  not_found: "Not Found",
  error: "Error",
  unavailable: "Unavailable"
};

function statusPill(status) {
  const label = statusLabels[status] || status;
  return `<span class="status-pill status-${status}">${label}</span>`;
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function formatTime(value) {
  return new Intl.DateTimeFormat("en", {
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

function formatStepLabel(value) {
  const label = value ? value.replaceAll("_", " ") : "Predictive maintenance";
  return label.charAt(0).toUpperCase() + label.slice(1);
}

async function apiFetch(path) {
  const response = await fetch(path);
  const payload = await response.json();
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
  if (predictions.length > 0) {
    return predictions.map((prediction) => ({
      ...prediction,
      risk_score: Number(prediction.risk_score),
      display_updated: formatDateTime(prediction.scored_at)
    }));
  }

  return profiles.map((profile) => {
    const riskScore = Number(profile.failure_risk);
    const status = profileStatus(riskScore);
    return {
      ...profile,
      risk_score: riskScore,
      asset_status: status,
      maintenance_priority: profilePriority(status),
      recommended_action: "Run predictive maintenance to calculate the latest asset risk.",
      display_updated: "Profile baseline"
    };
  });
}

function renderSummary(data) {
  const atRisk = data.assets.filter((asset) =>
    ["critical", "warning", "watch"].includes(asset.asset_status)
  );
  const critical = data.assets.filter((asset) => asset.asset_status === "critical");
  const failedWorkflows = data.workflows.filter((workflow) => workflow.status === "failed");
  const completedWorkflows = data.workflows.filter((workflow) => workflow.status === "completed");

  document.getElementById("assets-at-risk-value").textContent = String(atRisk.length);
  document.getElementById("assets-at-risk-note").textContent = `${data.assets.length} monitored assets`;
  document.getElementById("active-alerts-value").textContent = String(critical.length + failedWorkflows.length);
  document.getElementById("active-alerts-note").textContent = `${critical.length} critical, ${atRisk.length - critical.length} other at risk`;
  document.getElementById("workflow-health-value").textContent = failedWorkflows.length === 0 ? "Healthy" : "Degraded";
  document.getElementById("workflow-health-note").textContent = `${data.workflows.filter((workflow) => workflow.status === "running").length} running, ${failedWorkflows.length} failed`;
  const latestCompleted = completedWorkflows[0];
  document.getElementById("last-scoring-run-value").textContent = latestCompleted?.updated_at
    ? formatTime(latestCompleted.updated_at)
    : "None";
  document.getElementById("last-scoring-run-note").textContent = latestCompleted
    ? `Completed ${formatDateTime(latestCompleted.updated_at)}`
    : "No completed scoring run";
}

function renderAssets(data, filterValue = "all") {
  const rows = data.assets.filter((asset) => (
    filterValue === "all" || asset.asset_status === filterValue
  ));
  const tbody = document.getElementById("asset-table-body");
  const emptyState = document.getElementById("asset-empty-state");

  tbody.innerHTML = rows.map((asset) => `
    <tr>
      <td><strong>${asset.asset_id}</strong></td>
      <td>${statusPill(asset.asset_status)}</td>
      <td>${Number(asset.risk_score).toFixed(2)}</td>
      <td>${asset.maintenance_priority}</td>
      <td>${asset.display_updated || formatDateTime(asset.updated_at)}</td>
    </tr>
  `).join("");

  emptyState.hidden = rows.length > 0;
}

function renderWorkflows(data) {
  document.getElementById("workflow-list").innerHTML = data.workflows.length > 0
    ? data.workflows.map((workflow) => `
    <section class="workflow-item" title="Run ID: ${workflow.run_id}">
      <div>
        <strong>Manual execution</strong>
        <p>${workflow.label} · ${formatDateTime(workflow.updated_at)}</p>
      </div>
      ${statusPill(workflow.status)}
    </section>
  `).join("")
    : '<p class="empty-state">No workflow runs have been recorded.</p>';

  const states = ["running", "completed", "failed"];
  document.getElementById("workflow-state-row").innerHTML = states.map((state) => {
    const count = data.workflows.filter((workflow) => workflow.status === state).length;
    return `<span class="workflow-state-chip status-${state}">${statusLabels[state]} ${count}</span>`;
  }).join("");
}

async function refreshDashboard() {
  const actionStatus = document.getElementById("workflow-action-status");
  actionStatus.textContent = "Loading operational data...";
  actionStatus.dataset.state = "loading";
  try {
    const [assetData, predictionData, workflowData] = await Promise.all([
      apiFetch("/api/assets"),
      apiFetch("/api/predictions/latest"),
      apiFetch("/api/workflows")
    ]);
    dashboardData.predictions = predictionData.predictions || [];
    dashboardData.assets = normalizeAssets(
      assetData.assets || [],
      dashboardData.predictions
    );
    dashboardData.workflows = workflowData.workflows.map((workflow) => ({
      ...workflow,
      label: formatStepLabel(workflow.step),
      duration: workflow.status === "running" ? "active" : "complete"
    }));
    renderSummary(dashboardData);
    renderAssets(dashboardData);
    renderWorkflows(dashboardData);
    renderPredictions(dashboardData);
    document.getElementById("last-refresh-value").textContent = formatDateTime(new Date());
    actionStatus.textContent = "Operational data refreshed.";
    actionStatus.dataset.state = "success";
  } catch (error) {
    actionStatus.textContent = error.message;
    actionStatus.dataset.state = "error";
    renderSummary(dashboardData);
    renderAssets(dashboardData);
    renderWorkflows(dashboardData);
    renderPredictions(dashboardData);
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
      body: JSON.stringify({ workflow: "predictive-maintenance" })
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Workflow could not be started.");
    }
    actionStatus.textContent = "Workflow started. Refreshing status...";
    actionStatus.dataset.state = "success";
    await refreshDashboard();
  } catch (error) {
    actionStatus.textContent = error.message;
    actionStatus.dataset.state = "error";
  } finally {
    button.disabled = false;
  }
}

function groupAssetsByStatus(assets) {
  return assets.reduce((groups, asset) => {
    groups[asset.asset_status] = (groups[asset.asset_status] || 0) + 1;
    return groups;
  }, {});
}

function renderPredictions(data) {
  const distributionBar = document.getElementById("distribution-bar");
  const distributionLegend = document.getElementById("distribution-legend");
  if (data.assets.length === 0) {
    document.getElementById("prediction-count").textContent = "No prediction data available";
    distributionBar.classList.add("is-empty");
    distributionBar.innerHTML = "";
    distributionLegend.innerHTML = '<span class="legend-empty">Run a workflow to calculate asset risk.</span>';
    return;
  }

  const statusCounts = groupAssetsByStatus(data.assets);
  const reviewCount = data.assets.filter((asset) => asset.asset_status !== "healthy").length;
  const total = Math.max(data.assets.length, 1);
  const healthyShare = Math.round(((statusCounts.healthy || 0) / total) * 100);
  const warningShare = Math.round((((statusCounts.warning || 0) + (statusCounts.watch || 0)) / total) * 100);
  const criticalShare = Math.round(((statusCounts.critical || 0) / total) * 100);

  document.getElementById("prediction-count").textContent = `${reviewCount} assets require review`;
  distributionBar.classList.remove("is-empty");
  distributionBar.style.setProperty("--healthy-share", String(Math.max(healthyShare, 1)));
  distributionBar.style.setProperty("--warning-share", String(Math.max(warningShare, 1)));
  distributionBar.style.setProperty("--critical-share", String(Math.max(criticalShare, 1)));
  distributionBar.innerHTML = `
    <span class="distribution-segment healthy"></span>
    <span class="distribution-segment warning"></span>
    <span class="distribution-segment critical"></span>
  `;
  distributionLegend.innerHTML = `
    <span class="legend-healthy">Healthy ${healthyShare}%</span>
    <span class="legend-warning">Warning ${warningShare}%</span>
    <span class="legend-critical">Critical ${criticalShare}%</span>
  `;
}

function showView(viewName) {
  document.querySelectorAll("[data-view]").forEach((view) => {
    view.hidden = view.dataset.view !== viewName;
  });

  document.querySelectorAll("[data-view-target]").forEach((control) => {
    if (control.classList.contains("nav-item")) {
      if (control.dataset.viewTarget === viewName) {
        control.setAttribute("aria-current", "page");
      } else {
        control.removeAttribute("aria-current");
      }
    }
  });
}

function initDashboard() {
  renderSummary(dashboardData);
  renderAssets(dashboardData);
  renderWorkflows(dashboardData);
  renderPredictions(dashboardData);
  showView("overview");

  document.getElementById("asset-status-filter").addEventListener("change", (event) => {
    renderAssets(dashboardData, event.target.value);
  });
  document.getElementById("run-workflow-button").addEventListener("click", runWorkflow);
  document.querySelector(".refresh-button").addEventListener("click", refreshDashboard);

  document.querySelectorAll("[data-view-target]").forEach((control) => {
    control.addEventListener("click", () => {
      showView(control.dataset.viewTarget);
    });
  });

  refreshDashboard();
}

document.addEventListener("DOMContentLoaded", initDashboard);
