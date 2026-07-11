const dashboardData = {
  generatedAt: "2026-06-26T19:45:00Z",
  apiState: {
    status: "ok",
    request_state: "ok",
    message: "Dashboard sample data follows the Sprint 2 operational API contract."
  },
  assets: [
    {
      asset_id: "PUMP-104",
      asset_status: "critical",
      risk_score: 0.92,
      maintenance_priority: "Immediate",
      updated_at: "2026-06-26T19:40:00Z",
      display_updated: "2m ago",
      recommended_action: "Inspect pump vibration and pressure before the next production cycle."
    },
    {
      asset_id: "MOTOR-207",
      asset_status: "warning",
      risk_score: 0.71,
      maintenance_priority: "High",
      updated_at: "2026-06-26T19:36:00Z",
      display_updated: "6m ago",
      recommended_action: "Review elevated temperature and vibration trend before the next shift."
    },
    {
      asset_id: "FAN-031",
      asset_status: "warning",
      risk_score: 0.64,
      maintenance_priority: "High",
      updated_at: "2026-06-26T19:34:00Z",
      display_updated: "8m ago",
      recommended_action: "Schedule maintenance within 24 hours."
    },
    {
      asset_id: "PUMP-118",
      asset_status: "healthy",
      risk_score: 0.18,
      maintenance_priority: "Routine",
      updated_at: "2026-06-26T19:30:00Z",
      display_updated: "12m ago",
      recommended_action: "Continue scheduled monitoring."
    },
    {
      asset_id: "MOTOR-215",
      asset_status: "healthy",
      risk_score: 0.11,
      maintenance_priority: "Routine",
      updated_at: "2026-06-26T19:27:00Z",
      display_updated: "15m ago",
      recommended_action: "Continue scheduled monitoring."
    }
  ],
  workflows: [
    {
      run_id: "sprint1-0942",
      status: "running",
      label: "Scoring pipeline",
      started_at: "2026-06-26T19:42:00Z",
      duration: "active",
      step: "score_and_persist_predictions",
      error: null
    },
    {
      run_id: "sprint1-0910",
      status: "completed",
      label: "Feature pipeline",
      started_at: "2026-06-26T19:10:00Z",
      duration: "2m 18s",
      step: "score_and_persist_predictions",
      error: null
    },
    {
      run_id: "sprint1-0838",
      status: "completed",
      label: "Telemetry ingest",
      started_at: "2026-06-26T18:38:00Z",
      duration: "1m 04s",
      step: "engineer_and_persist_features",
      error: null
    },
    {
      run_id: "failed-run",
      status: "failed",
      started_at: "2026-06-26T18:22:00Z",
      duration: "35s",
      step: "engineer_and_persist_features",
      error: "Feature processing failed."
    }
  ],
  responseStates: [
    {
      label: "Normal",
      statusCode: 200,
      status: "ok",
      message: "Data is current and available."
    },
    {
      label: "Missing",
      statusCode: 404,
      status: "not_found",
      message: "Requested workflow or prediction record was not found."
    },
    {
      label: "Invalid",
      statusCode: 400,
      status: "error",
      message: "Request identifier or source data failed validation."
    },
    {
      label: "Unavailable",
      statusCode: 503,
      status: "unavailable",
      message: "A required source is unavailable."
    }
  ]
};

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

function formatPercent(value) {
  return `${Math.round(value * 100)}%`;
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
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
  document.getElementById("active-alerts-note").textContent = `${critical.length} critical, ${atRisk.length - critical.length} warning`;
  document.getElementById("workflow-health-value").textContent = failedWorkflows.length === 0 ? "Healthy" : "Degraded";
  document.getElementById("workflow-health-note").textContent = `${data.workflows.filter((workflow) => workflow.status === "running").length} running, ${failedWorkflows.length} failed`;
  document.getElementById("last-scoring-run-value").textContent = "09:42";
  document.getElementById("last-scoring-run-note").textContent = `Completed in ${completedWorkflows[0]?.duration || "n/a"}`;
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
      <td>${asset.risk_score.toFixed(2)}</td>
      <td>${asset.maintenance_priority}</td>
      <td>${asset.display_updated || formatDateTime(asset.updated_at)}</td>
    </tr>
  `).join("");

  emptyState.hidden = rows.length > 0;
}

function renderWorkflows(data) {
  document.getElementById("workflow-list").innerHTML = data.workflows.map((workflow) => `
    <section class="workflow-item">
      <div>
        <strong>${workflow.run_id}</strong>
        <p>${workflow.label}</p>
      </div>
      ${statusPill(workflow.status)}
    </section>
  `).join("");

  const states = ["running", "completed", "failed"];
  document.getElementById("workflow-state-row").innerHTML = states.map((state) => {
    const count = data.workflows.filter((workflow) => workflow.status === state).length;
    return `<span class="workflow-state-chip status-${state}">${statusLabels[state]} ${count}</span>`;
  }).join("");
}

async function refreshWorkflows() {
  const actionStatus = document.getElementById("workflow-action-status");
  try {
    const response = await fetch("/api/workflows");
    if (!response.ok) {
      throw new Error(`Workflow status request failed (${response.status}).`);
    }
    const payload = await response.json();
    dashboardData.workflows = payload.data.workflows.map((workflow) => ({
      ...workflow,
      label: workflow.step ? workflow.step.replaceAll("_", " ") : "Predictive maintenance",
      duration: workflow.status === "running" ? "active" : "complete"
    }));
    renderWorkflows(dashboardData);
    renderSummary(dashboardData);
    return dashboardData.workflows;
  } catch (error) {
    actionStatus.textContent = error.message;
    actionStatus.dataset.state = "error";
    return null;
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
    const runId = payload.data.workflow.run_id;
    actionStatus.textContent = `Workflow ${runId} started.`;
    actionStatus.dataset.state = "success";
    await refreshWorkflows();
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
  const statusCounts = groupAssetsByStatus(data.assets);
  const reviewCount = data.assets.filter((asset) => asset.asset_status !== "healthy").length;
  const total = Math.max(data.assets.length, 1);
  const healthyShare = Math.round(((statusCounts.healthy || 0) / total) * 100);
  const warningShare = Math.round((((statusCounts.warning || 0) + (statusCounts.watch || 0)) / total) * 100);
  const criticalShare = Math.round(((statusCounts.critical || 0) / total) * 100);

  document.getElementById("prediction-count").textContent = `${reviewCount} assets require review`;
  document.getElementById("distribution-bar").style.setProperty("--healthy-share", String(Math.max(healthyShare, 1)));
  document.getElementById("distribution-bar").style.setProperty("--warning-share", String(Math.max(warningShare, 1)));
  document.getElementById("distribution-bar").style.setProperty("--critical-share", String(Math.max(criticalShare, 1)));
  document.getElementById("distribution-bar").innerHTML = `
    <span class="distribution-segment healthy"></span>
    <span class="distribution-segment warning"></span>
    <span class="distribution-segment critical"></span>
  `;
  document.getElementById("distribution-legend").innerHTML = `
    <span class="legend-healthy">Healthy ${healthyShare}%</span>
    <span class="legend-warning">Warning ${warningShare}%</span>
    <span class="legend-critical">Critical ${criticalShare}%</span>
  `;
}

function renderStates(data) {
  document.getElementById("state-grid").innerHTML = data.responseStates.map((state) => `
    <section class="state-card">
      <strong>${state.label}</strong>
      <p>${state.message}</p>
      <code>${state.statusCode} / ${state.status}</code>
    </section>
  `).join("");
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
  renderStates(dashboardData);
  showView("overview");

  document.getElementById("asset-status-filter").addEventListener("change", (event) => {
    renderAssets(dashboardData, event.target.value);
  });
  document.getElementById("run-workflow-button").addEventListener("click", runWorkflow);
  document.querySelector(".refresh-button").addEventListener("click", refreshWorkflows);

  document.querySelectorAll("[data-view-target]").forEach((control) => {
    control.addEventListener("click", () => {
      showView(control.dataset.viewTarget);
    });
  });

  refreshWorkflows();
}

document.addEventListener("DOMContentLoaded", initDashboard);
