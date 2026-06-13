const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
const gonka = (value) => `${fmt.format(value)} GONKA`;
const optionLabels = { yes: "Yes", no: "No", abstain: "Abstain", no_with_veto: "No with veto", did_not_vote: "Did not vote" };
const optionColors = { yes: "#79b66a", no: "#d9655f", abstain: "#d7a84f", no_with_veto: "#8f7ad3", did_not_vote: "#6d7682" };
const boundaryColors = { public_owner_proof: "#79b66a", public_identity_signal: "#d7a84f", infrastructure_signal: "#5da9e9", unknown: "#6d7682" };

const state = {
  data: null,
  filteredRecipients: [],
  compensationView: "bar",
  timelineScope: "recipients",
  timelineModel: "all",
  timelineMetric: "weight",
  timelineSort: "maxWeight",
  kimiScaleScenario: "actual",
  kimiScaleLocked: false,
  kimiFixedRawWeight: 400000,
  kimiDipRawWeight: 50000,
  kimiFixedQwenWeight: 300000,
  charts: {},
  chartAddressRows: {},
};

const els = {
  search: document.getElementById("searchInput"),
  status: document.getElementById("statusFilter"),
  vote: document.getElementById("voteFilter"),
  identity: document.getElementById("identityFilter"),
  label: document.getElementById("labelFilter"),
  node: document.getElementById("nodeFilter"),
  top: document.getElementById("topFilter"),
  component: document.getElementById("componentFilter"),
  confidence: document.getElementById("confidenceFilter"),
  sourceType: document.getElementById("sourceTypeFilter"),
  benefitPowerTable: document.getElementById("benefitPowerTable"),
  voterPowerTable: document.getElementById("voterPowerTable"),
  windowPowerTable: document.getElementById("windowPowerTable"),
  publicNameTable: document.getElementById("publicNameTable"),
  rankedTable: document.getElementById("rankedTable"),
  interestClusterTable: document.getElementById("interestClusterTable"),
  attributionTable: document.getElementById("attributionTable"),
  telegramCoverageTable: document.getElementById("telegramCoverageTable"),
  telegramUnlinkedTable: document.getElementById("telegramUnlinkedTable"),
  evidenceTable: document.getElementById("evidenceTable"),
  hypothesisTable: document.getElementById("hypothesisTable"),
  anomalyTable: document.getElementById("anomalyTable"),
  entryExitTable: document.getElementById("entryExitTable"),
  modelCapTable: document.getElementById("modelCapTable"),
  modelCapMechanicsTable: document.getElementById("modelCapMechanicsTable"),
  noAttackFlow: document.getElementById("noAttackFlow"),
  noAttackModelMatrix: document.getElementById("noAttackModelMatrix"),
  noAttackParticipantTable: document.getElementById("noAttackParticipantTable"),
  telegramTable: document.getElementById("telegramTable"),
  labelTable: document.getElementById("labelTable"),
  searchIndex: document.getElementById("searchIndex"),
  epochTable: document.getElementById("epochTable"),
  recipientTable: document.getElementById("recipientTable"),
  voteTable: document.getElementById("voteTable"),
  strictClusterTable: document.getElementById("strictClusterTable"),
  signalClusterTable: document.getElementById("signalClusterTable"),
  recipientCompByWindowTable: document.getElementById("recipientCompByWindowTable"),
  drawer: document.getElementById("drawer"),
  drawerContent: document.getElementById("drawerContent"),
  scrim: document.getElementById("scrim"),
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function escapeRichText(value) {
  return String(value ?? "").replace(/[{}|]/g, " ");
}

function primaryOption(vote) {
  return (vote.finalVoteOptions || []).slice().sort((a, b) => b.weight - a.weight)[0]?.option || vote.primaryOption || vote.voteOption || "unknown";
}

function voteOptionLabel(option) {
  return optionLabels[option] || option || "Unknown";
}

function voteSplitOptions(row) {
  return (row?.finalVoteOptions || [])
    .filter((item) => item && item.option && Number(item.weight || 0) > 0)
    .slice()
    .sort((a, b) => (b.weight || 0) - (a.weight || 0));
}

function voteDisplayText(row) {
  const options = voteSplitOptions(row);
  if (!options.length) return voteOptionLabel(row?.primaryOption || row?.voteOption || "did_not_vote");
  if (options.length === 1 && Math.abs((options[0].weight || 0) - 1) < 0.000001) return voteOptionLabel(options[0].option);
  return options.map((item) => `${voteOptionLabel(item.option)} ${fmt.format((item.weight || 0) * 100)}%`).join(" / ");
}

function voteDisplayHtml(row) {
  const options = voteSplitOptions(row);
  if (!options.length || (options.length === 1 && Math.abs((options[0].weight || 0) - 1) < 0.000001)) {
    const option = options[0]?.option || row?.primaryOption || row?.voteOption || "did_not_vote";
    return `<span class="tag" style="border-color:${optionColors[option] || "#6d7682"}">${escapeHtml(voteOptionLabel(option))}</span>`;
  }
  return options.map((item) => (
    `<span class="tag" style="border-color:${optionColors[item.option] || "#6d7682"}">${escapeHtml(voteOptionLabel(item.option))} ${fmt.format((item.weight || 0) * 100)}%</span>`
  )).join(" ");
}

function voteWeight(row, option) {
  const options = voteSplitOptions(row);
  if (options.length) return options.filter((item) => item.option === option).reduce((total, item) => total + (item.weight || 0), 0);
  return (row?.primaryOption || row?.voteOption || "did_not_vote") === option ? 1 : 0;
}

function voteMatches(row, selectedOption) {
  if (selectedOption === "all") return true;
  const options = voteSplitOptions(row);
  if (options.length) return options.some((item) => item.option === selectedOption);
  return (row?.primaryOption || row?.voteOption || "did_not_vote") === selectedOption;
}

function actorLabel(row) {
  return row?.actorDisplayLabel || row?.label || row?.publicLabel || row?.address || row?.voter || "Unknown public owner";
}

function actorShortLabel(row) {
  return row?.actorShortLabel || actorLabel(row);
}

function shortAddress(address) {
  if (!address) return "";
  return `${address.slice(0, 10)}...${address.slice(-6)}`;
}

function identityBoundary(row) {
  return row?.identityBoundary || row?.evidenceBoundary || "unknown";
}

function attributionTier(row) {
  if (!row) return "context_only";
  if (row.attributionTier) return row.attributionTier;
  if (row.isAttributionProof) return "proof";
  const sourceType = row.sourceType || "";
  if (sourceType.startsWith("telegram_")) return sourceType.includes("self") || sourceType.includes("operator") || sourceType.includes("pool") ? "telegram_signal" : "context_only";
  if (sourceType.startsWith("discord_")) return sourceType.includes("self") || sourceType.includes("operator") || sourceType.includes("pool") ? "discord_signal" : "context_only";
  const category = row.category || "";
  if (category === "infrastructure_signal" || category === "public_infrastructure") return "host_signal";
  if (identityBoundary(row) === "public_owner_proof") return "proof";
  return "context_only";
}

function attributionTierLabel(tier) {
  return {
    proof: "proof",
    telegram_signal: "telegram signal",
    discord_signal: "discord signal",
    host_signal: "host signal",
    public_signal: "public signal",
    context_only: "context only",
  }[tier] || tier || "context only";
}

function attributionTag(value) {
  const tier = typeof value === "string" ? value : attributionTier(value);
  const klass = tier === "proof" ? "good" : tier === "telegram_signal" || tier === "discord_signal" || tier === "context_only" ? "warn" : "";
  return `<span class="tag ${klass}">${escapeHtml(attributionTierLabel(tier))}</span>`;
}

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
}

function chartTooltip(options = {}) {
  return {
    appendToBody: true,
    confine: true,
    renderMode: "html",
    transitionDuration: 0,
    hideDelay: 60,
    enterable: false,
    position: (point, params, dom, rect, size) => {
      const gap = 16;
      const content = size.contentSize || [360, 160];
      const view = size.viewSize || [window.innerWidth, window.innerHeight];
      let x = point[0] + gap;
      let y = point[1] + gap;
      if (x + content[0] + gap > view[0]) x = point[0] - content[0] - gap;
      if (y + content[1] + gap > view[1]) y = point[1] - content[1] - gap;
      return [Math.max(8, x), Math.max(8, y)];
    },
    extraCssText: "max-width:min(440px, calc(100vw - 32px));white-space:normal;overflow-wrap:anywhere;z-index:9999;pointer-events:none;",
    ...options,
  };
}

function getRecentEpochWindow(size = 10) {
  const epochRows = (state.data?.epochs || [])
    .map((row) => Number(row?.epoch))
    .filter((value) => Number.isFinite(value))
    .sort((a, b) => a - b);
  const windowEpochs = epochRows.slice(Math.max(0, epochRows.length - size));
  return {
    windowEpochs,
    windowKeys: windowEpochs.map((epoch) => `e${epoch}`),
  };
}

function copyText(value, button) {
  const text = String(value || "");
  if (!text) return;
  const markCopied = () => {
    if (!button) return;
    const previous = button.textContent;
    button.textContent = "copied";
    button.classList.add("copied");
    window.setTimeout(() => {
      button.textContent = previous;
      button.classList.remove("copied");
    }, 900);
  };
  if (navigator.clipboard?.writeText && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(markCopied).catch(() => fallbackCopyText(text, markCopied));
    return;
  }
  fallbackCopyText(text, markCopied);
}

function fallbackCopyText(text, done) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
  if (done) done();
}

function enhanceAddressActions(root = document) {
  root.querySelectorAll("[data-address]").forEach((button) => {
    if (!button.dataset.addressBound) {
      button.dataset.addressBound = "1";
      button.title = "Open address details";
      button.addEventListener("click", () => openDrawer(button.dataset.address));
    }
    if (button.dataset.copyEnhanced || button.classList.contains("search-index-open")) return;
    button.dataset.copyEnhanced = "1";
    const copy = document.createElement("button");
    copy.type = "button";
    copy.className = "copy-address-button";
    copy.dataset.copyAddress = button.dataset.address;
    copy.textContent = "copy";
    copy.title = "Copy address";
    button.insertAdjacentElement("afterend", copy);
  });
  root.querySelectorAll("[data-copy-address]").forEach((button) => {
    if (button.dataset.copyBound) return;
    button.dataset.copyBound = "1";
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      copyText(button.dataset.copyAddress, button);
    });
  });
}

function normalizeDashboardAddress(value) {
  const text = String(value || "");
  if (text.startsWith("gonkavaloper")) return `gonka${text.slice("gonkavaloper".length)}`;
  return text;
}

function extractAddress(value, depth = 0) {
  if (value == null || depth > 5) return "";
  if (typeof value === "string") {
    const match = value.match(/gonkavaloper1[0-9a-z]{38}|gonka1[0-9a-z]{38}/);
    return match ? normalizeDashboardAddress(match[0]) : "";
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const address = extractAddress(item, depth + 1);
      if (address) return address;
    }
    return "";
  }
  if (typeof value !== "object") return "";
  for (const key of ["address", "voter", "topRecipient"]) {
    const address = extractAddress(value[key], depth + 1);
    if (address) return address;
  }
  if (Array.isArray(value.addresses) && value.addresses.length) {
    const address = extractAddress(value.addresses[0], depth + 1);
    if (address) return address;
  }
  for (const key of ["row", "data", "value", "id", "name"]) {
    const address = extractAddress(value[key], depth + 1);
    if (address) return address;
  }
  return "";
}

function installChartAddressHandlers() {
  Object.entries(state.charts).forEach(([key, chart]) => {
    if (!chart || chart.__addressHandlerInstalled) return;
    chart.__addressHandlerInstalled = true;
    chart.on("click", (params) => {
      const mapped = state.chartAddressRows[key]?.[params?.dataIndex];
      const address = extractAddress(params?.data) || extractAddress(mapped) || extractAddress(params);
      if (address) openDrawer(address);
    });
  });
}

function voteSymbolSize(vote, maxPower) {
  const power = vote?.votingPower || 0;
  if (!power || !maxPower) return 10;
  return 10 + Math.sqrt(power / maxPower) * 22;
}

function boundaryColor(row) {
  return boundaryColors[identityBoundary(row)] || boundaryColors.unknown;
}

async function loadData() {
  if (window.DASHBOARD_DATA) return window.DASHBOARD_DATA;
  const response = await fetch("data/dashboard.json");
  return response.json();
}

function initCharts() {
  for (const [key, id] of Object.entries({
    compensation: "compensationChart",
    attackTimeline: "attackTimelineChart",
    waterfall: "waterfallChart",
    epoch: "epochChart",
    modelCap: "modelCapChart",
    capRecovery: "capRecoveryChart",
    capWaterfall: "capWaterfallChart",
    scaleTimeline: "scaleTimelineChart",
    capPressureHeatmap: "capPressureHeatmapChart",
    heatmap: "heatmapChart",
    matrix: "matrixChart",
    matrixStats: "matrixStats",
    timeline: "timelineChart",
    tally: "tallyChart",
    voterPower: "voterPowerChart",
    windowPower: "windowPowerChart",
    actorGraph: "actorGraphChart",
    entryExit: "entryExitChart",
    recipientCompByWindow: "recipientCompByWindowChart",
  })) {
    state.charts[key] = echarts.init(document.getElementById(id));
  }
  installChartAddressHandlers();
  window.addEventListener("resize", () => Object.values(state.charts).forEach((chart) => chart.resize()));
}

function resizeAllChartsNow() {
  requestAnimationFrame(() => {
    Object.values(state.charts).forEach((chart) => {
      if (chart && typeof chart.resize === "function") {
        chart.resize();
      }
    });
  });
}

function fillSelect(select, values, labels = {}) {
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labels[value] || value.replaceAll("_", " ");
    select.appendChild(option);
  });
}

function setupFilters(data) {
  fillSelect(els.status, [...new Set(data.recipients.map((row) => row.status))].sort());
  fillSelect(els.vote, [...new Set([...data.votes.map(primaryOption), "did_not_vote"])].sort(), optionLabels);
  fillSelect(els.identity, [...new Set([...data.recipients, ...data.votes].map((row) => row.identityType))].sort());
  fillSelect(els.label, buildLabelRows(data).map((row) => row.label));
  fillSelect(els.component, [...new Set(data.recipients.map((row) => row.componentSource))].sort());
  fillSelect(els.confidence, [...new Set([...(data.identityGraph?.edges || []), ...(data.evidenceClaims || [])].map((edge) => edge.confidence))].filter(Boolean).sort());
  fillSelect(els.sourceType, [...new Set([...(data.identityGraph?.edges || []), ...(data.evidenceClaims || [])].map((edge) => edge.sourceType))].filter(Boolean).sort());
  [els.search, els.status, els.vote, els.identity, els.label, els.node, els.top, els.component, els.confidence, els.sourceType].forEach((el) => {
    el.addEventListener("input", applyFilters);
    el.addEventListener("change", applyFilters);
  });
  document.querySelectorAll("[data-comp-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.compensationView = button.dataset.compView;
      document.querySelectorAll("[data-comp-view]").forEach((item) => item.classList.toggle("active", item === button));
      renderCompensationChart();
    });
  });
  document.querySelectorAll("[data-timeline-model]").forEach((button) => {
    button.addEventListener("click", () => {
      state.timelineModel = button.dataset.timelineModel;
      document.querySelectorAll("[data-timeline-model]").forEach((item) => item.classList.toggle("active", item === button));
      renderAttackTimeline();
    });
  });
  document.querySelectorAll("[data-timeline-scope]").forEach((button) => {
    button.addEventListener("click", () => {
      state.timelineScope = button.dataset.timelineScope;
      document.querySelectorAll("[data-timeline-scope]").forEach((item) => item.classList.toggle("active", item === button));
      renderAttackTimeline();
    });
  });
  document.querySelectorAll("[data-timeline-metric]").forEach((button) => {
    button.addEventListener("click", () => {
      state.timelineMetric = button.dataset.timelineMetric;
      document.querySelectorAll("[data-timeline-metric]").forEach((item) => item.classList.toggle("active", item === button));
      renderAttackTimeline();
    });
  });
  document.querySelectorAll("[data-timeline-sort]").forEach((button) => {
    button.addEventListener("click", () => {
      state.timelineSort = button.dataset.timelineSort;
      document.querySelectorAll("[data-timeline-sort]").forEach((item) => item.classList.toggle("active", item === button));
      renderAttackTimeline();
    });
  });
  const kimiScaleLockInput = document.getElementById("kimiScaleLock125");
  const kimiFixedRawInput = document.getElementById("kimiFixedRawWeight");
  const kimiDipRawInput = document.getElementById("kimiDipRawWeight");
  const kimiFixedQwenInput = document.getElementById("kimiFixedQwenWeight");
  const syncKimiScaleLock = () => {
    const inConstantRaw = state.kimiScaleScenario === "constantRaw";
    if (!kimiScaleLockInput) return;
    if (!inConstantRaw) {
      state.kimiScaleLocked = false;
      kimiScaleLockInput.checked = false;
    }
    kimiScaleLockInput.disabled = !inConstantRaw;
    if (kimiFixedRawInput) kimiFixedRawInput.disabled = !inConstantRaw;
    if (kimiDipRawInput) kimiDipRawInput.disabled = !inConstantRaw;
    if (kimiFixedQwenInput) kimiFixedQwenInput.disabled = !inConstantRaw;
  };
  document.querySelectorAll("[data-kimi-scale-scenario]").forEach((button) => {
    button.addEventListener("click", () => {
      state.kimiScaleScenario = button.dataset.kimiScaleScenario || "actual";
      document.querySelectorAll("[data-kimi-scale-scenario]").forEach((item) => item.classList.toggle("active", item === button));
      if (state.kimiScaleScenario !== "constantRaw") {
        state.kimiScaleLocked = false;
        if (kimiScaleLockInput) kimiScaleLockInput.checked = false;
      }
      syncKimiScaleLock();
      renderModelCapMechanics();
    });
  });
  if (kimiScaleLockInput) {
    kimiScaleLockInput.addEventListener("change", () => {
      state.kimiScaleLocked = Boolean(kimiScaleLockInput.checked && state.kimiScaleScenario === "constantRaw");
      renderModelCapMechanics();
    });
  }
  if (kimiFixedRawInput) {
    const normalizeKimiRawInput = () => {
      const parsed = Number(kimiFixedRawInput.value);
      const safe = Number.isFinite(parsed) && parsed > 0 ? parsed : state.kimiFixedRawWeight;
      state.kimiFixedRawWeight = Math.max(0, Math.floor(safe));
      if (!Number.isFinite(parsed) || parsed <= 0) kimiFixedRawInput.value = String(state.kimiFixedRawWeight);
      renderModelCapMechanics();
    };
    kimiFixedRawInput.addEventListener("change", normalizeKimiRawInput);
    kimiFixedRawInput.addEventListener("input", normalizeKimiRawInput);
  }
  if (kimiDipRawInput) {
    const normalizeKimiDipRawInput = () => {
      const parsed = Number(kimiDipRawInput.value);
      const safe = Number.isFinite(parsed) && parsed >= 0 ? parsed : state.kimiDipRawWeight;
      state.kimiDipRawWeight = Math.max(0, Math.floor(safe));
      if (!Number.isFinite(parsed) || parsed < 0) kimiDipRawInput.value = String(state.kimiDipRawWeight);
      renderModelCapMechanics();
    };
    kimiDipRawInput.addEventListener("change", normalizeKimiDipRawInput);
    kimiDipRawInput.addEventListener("input", normalizeKimiDipRawInput);
  }
  if (kimiFixedQwenInput) {
    const normalizeKimiQwenInput = () => {
      const parsed = Number(kimiFixedQwenInput.value);
      const safe = Number.isFinite(parsed) && parsed >= 0 ? parsed : state.kimiFixedQwenWeight;
      state.kimiFixedQwenWeight = Math.max(0, Math.floor(safe));
      if (!Number.isFinite(parsed) || parsed < 0) kimiFixedQwenInput.value = String(state.kimiFixedQwenWeight);
      renderModelCapMechanics();
    };
    kimiFixedQwenInput.addEventListener("change", normalizeKimiQwenInput);
    kimiFixedQwenInput.addEventListener("input", normalizeKimiQwenInput);
  }
  syncKimiScaleLock();
  if (kimiFixedRawInput) {
    const parsed = Number(kimiFixedRawInput.value);
    if (Number.isFinite(parsed) && parsed > 0) state.kimiFixedRawWeight = Math.floor(parsed);
  }
  if (kimiDipRawInput) {
    const parsed = Number(kimiDipRawInput.value);
    if (Number.isFinite(parsed) && parsed >= 0) state.kimiDipRawWeight = Math.floor(parsed);
  }
  if (kimiFixedQwenInput) {
    const parsed = Number(kimiFixedQwenInput.value);
    if (Number.isFinite(parsed) && parsed >= 0) state.kimiFixedQwenWeight = Math.floor(parsed);
  }
}

function textMatch(row, query) {
  if (!query) return true;
  return [
    row.address,
    row.voter,
    actorLabel(row),
    actorShortLabel(row),
    row.publicName,
    row.operatorSignalLabel,
    row.operatorSignalDisplayLabel,
    row.attributionTier,
    row.inferenceUrl,
    row.publicNodeInfo?.inferenceUrl,
    row.publicNodeInfo?.validatorKey,
    row.publicNodeInfo?.matchedValidator?.moniker,
    row.publicNodeInfo?.matchedValidator?.website,
    row.publicNodeInfo?.matchedValidator?.identity,
    row.txHash,
    row.status,
    row.identityType,
    row.strictClusterId,
    row.signalClusterId,
    ...(row.gnsNames || []).map((item) => item.fullName),
  ].filter(Boolean).join(" ").toLowerCase().includes(query);
}

function buildSearchIndexRows(data) {
  const rows = new Map();
  const ensure = (address) => {
    if (!address) return null;
    const normalized = String(address).replace("gonkavaloper", "gonka");
    if (!rows.has(normalized)) {
      rows.set(normalized, {
        address: normalized,
        labels: new Set(),
        roles: new Set(),
        statuses: new Set(),
        votes: new Set(),
        sources: new Set(),
        refs: new Set(),
        totalGonka: 0,
        votingPower: 0,
      });
    }
    return rows.get(normalized);
  };
  const addLabel = (row, value) => {
    if (value) row.labels.add(value);
  };
  const addRef = (row, value) => {
    if (value) row.refs.add(value);
  };

  (data.recipients || []).forEach((item) => {
    const row = ensure(item.address);
    if (!row) return;
    row.roles.add("recipient");
    row.sources.add("recipients");
    addLabel(row, actorLabel(item));
    addRef(row, item.inferenceUrl);
    addRef(row, item.publicNodeInfo?.validatorKey);
    addRef(row, item.publicNodeInfo?.inferenceUrl);
    row.statuses.add(item.status || "unknown");
    row.votes.add(voteDisplayText(item));
    row.totalGonka = Math.max(row.totalGonka, item.totalGonka || 0);
    row.votingPower = Math.max(row.votingPower, item.votingPower || item.governanceVotingPower || 0);
  });

  (data.votes || []).forEach((item) => {
    const row = ensure(item.voter);
    if (!row) return;
    row.roles.add("voter");
    row.sources.add("votes");
    addLabel(row, actorLabel(item));
    addRef(row, item.txHash);
    addRef(row, item.publicNodeInfo?.validatorKey);
    addRef(row, item.publicNodeInfo?.inferenceUrl);
    row.votes.add(voteDisplayText(item));
    row.votingPower = Math.max(row.votingPower, item.votingPower || 0);
  });

  (data.actors || []).forEach((item) => {
    const row = ensure(item.address);
    if (!row) return;
    row.sources.add("actors");
    (item.roles || []).forEach((role) => row.roles.add(role));
    addLabel(row, actorLabel(item));
    addRef(row, item.labelSource);
    addRef(row, item.attributionTier);
    row.totalGonka = Math.max(row.totalGonka, item.totalGonka || 0);
    row.votingPower = Math.max(row.votingPower, item.votingPower || 0);
  });

  [
    ...(data.identityGraph?.strictClusters || []),
    ...(data.identityGraph?.signalClusters || []),
    ...(data.epochEntryExitClusters || []),
    ...(data.rankedParties || []),
  ].forEach((item) => {
    (item.addresses || []).forEach((address) => {
      const row = ensure(address);
      if (!row) return;
      row.sources.add(item.id || "cluster");
      addLabel(row, actorLabel(item));
      addRef(row, item.kind);
    });
  });

  (data.attributionDossiers || []).forEach((item) => {
    (item.addresses || []).forEach((address) => {
      const row = ensure(address);
      if (!row) return;
      row.sources.add("attribution dossier");
      addLabel(row, item.displayLabel || item.candidateLabel);
      addRef(row, item.id);
      addRef(row, item.attributionTier);
      (item.hosts || []).forEach((host) => addRef(row, host));
      (item.topClaims || []).forEach((claim) => {
        addRef(row, claim.sourceType);
        addRef(row, claim.sourceValue);
        addRef(row, claim.sourceUrl);
        addRef(row, claim.telegramMessageId);
        addRef(row, claim.telegramAuthor);
        addRef(row, claim.chatMessageId);
        addRef(row, claim.chatAuthor);
        addRef(row, claim.chatAuthorUsername);
        addRef(row, claim.chatAuthorUserId);
      });
    });
  });

  (data.identityEvidence || []).forEach((item) => {
    const row = ensure(item.address);
    if (!row) return;
    row.sources.add(item.sourceType || "identity evidence");
    addLabel(row, item.publicLabel || item.sourceValue);
    addRef(row, item.sourceValue);
  });

  (data.evidenceClaims || []).forEach((item) => {
    const row = ensure(item.address);
    if (!row) return;
    row.sources.add(item.sourceType || "evidence claim");
    addLabel(row, item.subject || item.sourceValue);
    addRef(row, item.sourceValue);
    addRef(row, item.sourceUrl);
    addRef(row, item.telegramMessageId);
    addRef(row, item.telegramAuthor);
    addRef(row, item.telegramChat);
    addRef(row, item.chatMessageId);
    addRef(row, item.chatAuthor);
    addRef(row, item.chatAuthorUsername);
    addRef(row, item.chatAuthorUserId);
    addRef(row, item.chatName);
  });

  (data.identityGraph?.edges || []).forEach((edge) => {
    [edge.source, edge.target].forEach((value) => {
      const address = String(value || "").startsWith("address:") ? String(value).slice(8) : "";
      const row = ensure(address);
      if (!row) return;
      row.sources.add(edge.sourceType || "graph edge");
      addLabel(row, edge.sourceValue || edge.target);
      addRef(row, edge.sourceValue);
    });
  });

  (data.telegramEvidence || []).forEach((item) => {
    (item.addresses || []).forEach((address) => {
      const row = ensure(address);
      if (!row) return;
      row.sources.add("telegram evidence");
      addLabel(row, item.author || item.chat);
      addRef(row, item.messageId);
      addRef(row, item.sourceFile);
      (item.urls || []).forEach((url) => addRef(row, url));
      (item.usernames || []).forEach((username) => addRef(row, username));
    });
  });

  (data.discordEvidence || []).forEach((item) => {
    (item.addresses || []).forEach((address) => {
      const row = ensure(address);
      if (!row) return;
      row.sources.add("discord evidence");
      addLabel(row, item.author || item.authorUsername || item.chat);
      addRef(row, item.messageId);
      addRef(row, item.authorUserId);
      addRef(row, item.authorUsername);
      addRef(row, item.sourceFile);
      (item.urls || []).forEach((url) => addRef(row, url));
      (item.ips || []).forEach((ip) => addRef(row, ip));
    });
  });

  ((data.discordCoverage || {}).unlinkedAddressRows || []).forEach((item) => {
    (item.addresses || []).forEach((address) => {
      const row = ensure(address);
      if (!row) return;
      row.sources.add("discord unlinked lead");
      addLabel(row, item.author || item.authorUsername || item.chat);
      addRef(row, item.messageId);
      addRef(row, item.authorUserId);
      addRef(row, item.authorUsername);
      addRef(row, item.sourceFile);
      (item.urls || []).forEach((url) => addRef(row, url));
      (item.ips || []).forEach((ip) => addRef(row, ip));
    });
  });

  return [...rows.values()].sort((a, b) => b.totalGonka - a.totalGonka || b.votingPower - a.votingPower || a.address.localeCompare(b.address));
}

function renderSearchIndex() {
  const query = els.search.value.trim().toLowerCase();
  const rows = buildSearchIndexRows(state.data).filter((row) => {
    if (!query) return true;
    return [
      row.address,
      ...row.labels,
      ...row.roles,
      ...row.statuses,
      ...row.votes,
      ...row.sources,
      ...row.refs,
    ].join(" ").toLowerCase().includes(query);
  });
  document.getElementById("searchIndexRows").textContent = `${rows.length} searchable addresses`;
  els.searchIndex.innerHTML = rows.map((row) => `
    <div class="search-index-row">
      <span class="mono search-index-address">${escapeHtml(row.address)}<button class="copy-address-button" type="button" data-copy-address="${escapeHtml(row.address)}">copy</button></span>
      <span class="search-index-meta">${escapeHtml([...row.labels].filter(Boolean).slice(0, 3).join(" | ") || "Unknown public owner")}</span>
      <span class="search-index-tags">${[...row.roles].sort().map((role) => `<span class="tag">${escapeHtml(role)}</span>`).join(" ")}</span>
      <span class="search-index-stats">${row.totalGonka ? gonka(row.totalGonka) : ""}${row.votingPower ? ` · power ${fmt.format(row.votingPower)}` : ""}</span>
      <button class="row-button search-index-open" data-address="${escapeHtml(row.address)}">Open</button>
    </div>
  `).join("");
  enhanceAddressActions(els.searchIndex);
}

function applyFilters() {
  const query = els.search.value.trim().toLowerCase();
  const label = els.label.value;
  state.filteredRecipients = state.data.recipients.filter((row) => {
    if (!textMatch(row, query)) return false;
    if (els.status.value !== "all" && row.status !== els.status.value) return false;
    if (!voteMatches(row, els.vote.value)) return false;
    if (els.identity.value !== "all" && row.identityType !== els.identity.value) return false;
    if (label !== "all" && row.label !== label) return false;
    if (els.node.value === "active" && !row.activeNode) return false;
    if (els.node.value === "inactive" && row.activeNode) return false;
    if (els.top.value !== "all" && row.rank > Number(els.top.value)) return false;
    if (els.component.value !== "all" && row.componentSource !== els.component.value) return false;
    return true;
  });
  renderAll();
}

function renderOverview(data) {
  document.getElementById("proposalStatus").textContent = data.metadata.status.replace("PROPOSAL_STATUS_", "");
  document.getElementById("totalCompensation").textContent = gonka(data.summary.totalCompensationGonka);
  document.getElementById("recipientCount").textContent = `${data.summary.recipientsCount} non-zero recipients`;
  document.getElementById("finalTally").textContent = `Yes ${fmt.format(data.summary.finalTally.yes)} / Veto ${fmt.format(data.summary.finalTally.no_with_veto)}`;
  document.getElementById("recipientVoters").textContent = `${data.summary.recipientVotersCount} of ${data.summary.uniqueVotersCount}`;
}

function renderCompensationChart() {
  const filtered = new Set(state.filteredRecipients.map((row) => row.address));
  const voteOrder = { no_with_veto: 0, yes: 1, did_not_vote: 2, abstain: 3, no: 4 };
  const voteOptions = ["no_with_veto", "yes", "abstain", "no", "did_not_vote"];
  const rows = (state.data.chartData?.compensationComponents || state.filteredRecipients)
    .filter((row) => filtered.has(row.address))
    .sort((a, b) => (voteOrder[a.voteOption] ?? 99) - (voteOrder[b.voteOption] ?? 99) || (b.totalGonka || 0) - (a.totalGonka || 0))
    .slice(0, 30);
  if (state.compensationView === "tree") {
    const treeRows = (state.data.chartData?.compensationComponents || state.filteredRecipients)
      .filter((row) => filtered.has(row.address))
      .map((row) => {
        const splitOptions = voteOptions
          .map((option) => ({ option, weight: voteWeight(row, option) }))
          .filter((item) => item.weight > 0);
        const children = splitOptions.length > 1 ? splitOptions.map((item) => ({
          name: `${voteOptionLabel(item.option)} ${fmt.format(item.weight * 100)}%`,
          value: (row.totalGonka || 0) * item.weight,
          address: row.address,
          identityBoundary: identityBoundary(row),
          voteOption: item.option,
          finalVoteOptions: row.finalVoteOptions || [],
          votingPower: (row.votingPower || 0) * item.weight,
          itemStyle: { color: optionColors[item.option] || optionColors.did_not_vote },
        })) : null;
        return {
          name: actorShortLabel(row),
          value: row.totalGonka,
          address: row.address,
          identityBoundary: identityBoundary(row),
          voteOption: row.voteOption,
          finalVoteOptions: row.finalVoteOptions || [],
          votingPower: row.votingPower || 0,
          itemStyle: { color: optionColors[row.voteOption] || optionColors.did_not_vote },
          children,
        };
      });
    state.charts.compensation.setOption({
      tooltip: chartTooltip({ formatter: (p) => `${p.name}<br>${gonka(p.value)}<br>vote ${escapeHtml(voteDisplayText(p.data))}<br>power ${fmt.format(p.data.votingPower || 0)}<br>${escapeHtml(p.data.identityBoundary || "")}` }),
      series: [{
        type: "treemap",
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: { color: "#eef0f2", formatter: "{b}" },
        itemStyle: { borderColor: "#101114", borderWidth: 2 },
        data: treeRows,
      }],
    }, true);
    return;
  }
  const maxPower = Math.max(...rows.map((row) => row.votingPower || 0), 0);
  state.chartAddressRows.compensation = rows;
  const rowLabel = (row) => `${actorShortLabel(row)} #${row.rank}  ${shortAddress(row.address)}`;
  state.charts.compensation.setOption({
    legend: { top: 4, data: voteOptions.map((option) => optionLabels[option]), textStyle: { color: "#a7afba" } },
    grid: { left: 238, right: 72, top: 42, bottom: 32 },
    tooltip: chartTooltip({
      trigger: "axis",
      formatter: (params) => {
        const row = rows[params[0].dataIndex];
        return `<strong>${escapeHtml(actorLabel(row))}</strong><br>attack ${gonka(row.attackE265E266Gonka || 0)}<br>cap ${gonka(row.capE267E276Gonka || 0)}<br>total ${gonka(row.totalGonka || 0)}<br>vote ${escapeHtml(voteDisplayText(row))} · power ${fmt.format(row.votingPower || 0)}`;
      },
    }),
    xAxis: { type: "value", axisLabel: { color: "#a7afba", formatter: (v) => compact.format(v) } },
    yAxis: { type: "category", inverse: true, data: rows.map(rowLabel), axisLabel: { align: "left", margin: 232, color: "#a7afba", width: 220, overflow: "truncate" } },
    series: [
      ...voteOptions.map((option) => ({
        name: optionLabels[option],
        type: "bar",
        stack: "vote",
        data: rows.map((row) => (row.totalGonka || 0) * voteWeight(row, option)),
        itemStyle: { color: optionColors[option] || optionColors.did_not_vote },
        label: { show: true, position: "right", color: "#eef0f2", formatter: (p) => p.value ? compact.format(p.value) : "" },
      })),
      {
        name: "vote power",
        type: "scatter",
        data: rows.map((row, index) => [row.totalGonka || 0, index, row.votingPower || 0]),
        symbolSize: (value) => voteSymbolSize({ votingPower: value[2] }, maxPower),
        itemStyle: { color: "#101114", borderColor: (p) => optionColors[rows[p.dataIndex]?.voteOption] || optionColors.did_not_vote, borderWidth: 2 },
      },
    ],
  }, true);
}

function renderWaterfall() {
  const summary = state.data.summary;
  const epochById = new Map((state.data.epochs || []).map((row) => [row.epoch, row]));
  const components = [
    { epoch: 265, name: "e265 attack", value: epochById.get(265)?.totalGonka || summary.visibleDamageE265Gonka || 0, color: "#d9655f", description: "Direct attack/damage epoch" },
    { epoch: 266, name: "e266 excluded", value: epochById.get(266)?.totalGonka || 0, color: "#e78f61", description: "Attacked participants could not enter the next epoch" },
    ...(state.data.epochs || [])
      .filter((row) => row.epoch >= 267 && row.epoch <= 276)
      .map((row) => ({
        epoch: row.epoch,
        name: `e${row.epoch}`,
        value: row.totalGonka || 0,
        recipientsCount: row.recipientsCount || 0,
        color: "#d7a84f",
        description: "Capped compensation epoch",
      })),
  ];
  state.charts.waterfall.setOption({
    grid: { left: 70, right: 24, top: 28, bottom: 86 },
    tooltip: chartTooltip({
      trigger: "item",
      formatter: (p) => {
        const total = summary.totalCompensationGonka || 1;
        const row = components[p.dataIndex] || {};
        const recipients = row.recipientsCount ? `<br>${fmt.format(row.recipientsCount)} recipients` : "";
        return `<strong>${escapeHtml(row.name || p.name)}</strong><br>${escapeHtml(row.description || "")}<br>${gonka(row.value || 0)}${recipients}<br>${fmt.format(((row.value || 0) / total) * 100)}% of final payout<br>final total ${gonka(summary.totalCompensationGonka || 0)}`;
      },
    }),
    xAxis: { type: "category", data: components.map((row) => row.name), axisLabel: { color: "#a7afba", interval: 0, rotate: 32 } },
    yAxis: { type: "value", axisLabel: { color: "#a7afba", formatter: (v) => compact.format(v) }, name: "GONKA paid", nameTextStyle: { color: "#a7afba" } },
    series: [{
      type: "bar",
      data: components.map((row) => ({ value: row.value, itemStyle: { color: row.color } })),
      barMaxWidth: 58,
      label: { show: true, position: "top", color: "#eef0f2", formatter: (p) => compact.format(p.value) },
    }],
  }, true);
}

function renderEpochChart() {
  const epochs = state.data.epochs || [];
  state.charts.epoch.setOption({
    grid: { left: 70, right: 20, top: 24, bottom: 44 },
    tooltip: chartTooltip({
      trigger: "axis",
      formatter: (params) => {
        const row = epochs[params[0].dataIndex];
        return `Epoch ${row.epoch}<br>${gonka(row.totalGonka)}<br>${row.recipientsCount} recipients`;
      },
    }),
    xAxis: { type: "category", data: epochs.map((row) => `e${row.epoch}`), axisLabel: { color: "#a7afba" } },
    yAxis: [
      { type: "value", axisLabel: { color: "#a7afba", formatter: (v) => compact.format(v) } },
      { type: "value", axisLabel: { color: "#a7afba" }, splitLine: { show: false } },
    ],
    series: [
      {
        name: "total",
        type: "bar",
        data: epochs.map((row) => row.totalGonka),
        itemStyle: { color: (p) => epochs[p.dataIndex]?.componentSource === "attack_e265_e266" ? "#d9655f" : "#d7a84f" },
      },
      {
        name: "recipients",
        type: "line",
        yAxisIndex: 1,
        data: epochs.map((row) => row.recipientsCount),
        symbolSize: 8,
        itemStyle: { color: "#5da9e9" },
        lineStyle: { color: "#5da9e9" },
      },
    ],
  }, true);
}

function modelCapColor(label, index = 0) {
  const value = String(label || "").toLowerCase();
  if (value.includes("kimi")) return "#d9655f";
  if (value.includes("qwen")) return "#5da9e9";
  if (value.includes("minimax")) return "#d7a84f";
  return ["#79b66a", "#8f7ad3", "#e78f61"][index % 3];
}

function modelCapStatusLabel(status) {
  return {
    capped: "Capped",
    under_cap: "Under cap",
    initial_exempt: "Initial model exempt",
    sole_group_uncapped: "Sole group uncapped",
    cap_reference_missing: "Cap reference missing",
    missing_subgroup: "Missing subgroup",
  }[status] || status || "Unknown";
}

function noAttackStatusLabel(status) {
  return {
    excluded_in_e266_restored: "Restored in e266",
    weight_reduced_in_e266_restored: "Weight restored",
    kept_in_e266: "Kept in e266",
    actual_e266_without_entry_commit: "Actual only",
    not_in_e266: "Not in e266",
    returned_in_e267: "Returned in e267",
    carried_into_e267: "Carried into e267",
    new_in_e267: "New in e267",
    missing_in_e267: "Missing in e267",
  }[status] || status || "Unknown";
}

function noAttackStatusClass(status) {
  if (["carried_into_e267", "returned_in_e267", "kept_in_e266"].includes(status)) return "good";
  if (["excluded_in_e266_restored", "weight_reduced_in_e266_restored"].includes(status)) return "warn";
  if (["missing_in_e267"].includes(status)) return "bad";
  return "";
}

function renderNoAttackEvidence(payload) {
  const scenario = payload.noAttackE266Scenario || { summary: {}, participantRows: [] };
  const summary = scenario.summary || {};
  const byModel = summary.participantSummaryByModel || [];
  const participantRows = scenario.participantRows || [];
  const modelSummary = (label) => byModel.find((row) => (row.modelLabel || "").toLowerCase() === label.toLowerCase()) || {};
  const kimi = modelSummary("Kimi");
  const qwen = modelSummary("Qwen");
  const entryTotal = byModel.reduce((sum, row) => sum + (row.entryScaledWeight || 0), 0);
  const restoredTotal = byModel.reduce((sum, row) => sum + (row.e266RestoredScaledWeight || 0), 0);
  const carriedTotal = byModel.reduce((sum, row) => sum + (row.e267CarryScaledWeight || 0), 0);
  const carriedRows = byModel.reduce((sum, row) => sum + (row.carriedRows || 0), 0);
  const entrySource = summary.entrySource || {};
  const maxModelWeight = Math.max(
    1,
    ...byModel.flatMap((row) => [
      row.entryScaledWeight || 0,
      row.e266ActualScaledWeight || 0,
      row.e267ActualScaledWeight || 0,
      (row.e267ActualScaledWeight || 0) + (row.e267CarryScaledWeight || 0),
    ]),
  );
  const barWidth = (value) => `${Math.max(2, Math.min(100, ((value || 0) / maxModelWeight) * 100))}%`;
  const modelRows = byModel
    .slice()
    .sort((a, b) => (a.modelLabel || "").localeCompare(b.modelLabel || ""));

  if (els.noAttackFlow) {
    els.noAttackFlow.innerHTML = [
      {
        title: "e266 with attack",
        metric: fmt.format(summary.e266ActualRootTotalWeight || 0),
        text: "actual end-of-epoch total_weight after the attack",
      },
      {
        title: "e266 no attack",
        metric: fmt.format(summary.e266SimulatedRootTotalWeight || 0),
        text: `counted after cap from reconstructed entry weight`,
      },
      {
        title: "e267 actual basis",
        metric: fmt.format(summary.e267ActualCapBasis || 0),
        text: "actual e266 collapse became the normal e267 cap basis",
      },
      {
        title: "e267 no-attack carry",
        metric: fmt.format(carriedTotal),
        text: `${fmt.format(carriedRows)} participant/model rows carried into e267`,
      },
    ].map((card) => `
      <div class="no-attack-card">
        <strong>${escapeHtml(card.title)}</strong>
        <div class="metric">${escapeHtml(card.metric)}</div>
        <span class="muted">${escapeHtml(card.text)}</span>
      </div>
    `).join("");
  }

  if (els.noAttackModelMatrix) {
    els.noAttackModelMatrix.innerHTML = `
      <div class="no-attack-matrix-head">
        <div>Model</div>
        <div>Epoch 266: with attack -> no attack</div>
        <div>Epoch 267: actual -> simulated</div>
      </div>
      ${modelRows.map((row) => {
        const color = modelCapColor(row.modelLabel);
        const e266Actual = row.e266ActualScaledWeight || 0;
        const e266NoAttack = row.entryScaledWeight || 0;
        const e266Delta = e266NoAttack - e266Actual;
        const e267Actual = row.e267ActualScaledWeight || 0;
        const e267NoAttack = e267Actual + (row.e267CarryScaledWeight || 0);
        return `
          <div class="no-attack-matrix-row">
            <div class="no-attack-model-name">
              <span class="tag" style="border-color:${color}">${escapeHtml(row.modelLabel || row.modelId)}</span>
              <span class="muted">${fmt.format(row.entryRows || 0)} entry rows</span>
            </div>
            <div class="no-attack-epoch-cell">
              <div class="bar-compare">
                <span class="bar-label">with attack</span>
                <span class="bar-track"><i style="width:${barWidth(e266Actual)}; background:${color}; opacity:.38"></i></span>
                <strong>${fmt.format(e266Actual)}</strong>
              </div>
              <div class="bar-compare">
                <span class="bar-label">no attack</span>
                <span class="bar-track"><i style="width:${barWidth(e266NoAttack)}; background:${color}"></i></span>
                <strong>${fmt.format(e266NoAttack)}</strong>
              </div>
              <div class="matrix-note ${e266Delta >= 0 ? "warn-text" : "muted"}">
                restored lost participant/model weight ${fmt.format(row.e266RestoredScaledWeight || 0)}
                ${e266Delta < 0 ? `; aggregate no-attack is ${fmt.format(Math.abs(e266Delta))} lower because actual e266 includes rows without entry commits` : ""}
              </div>
            </div>
            <div class="no-attack-epoch-cell">
              <div class="bar-compare">
                <span class="bar-label">actual e267</span>
                <span class="bar-track"><i style="width:${barWidth(e267Actual)}; background:${color}; opacity:.38"></i></span>
                <strong>${fmt.format(e267Actual)}</strong>
              </div>
              <div class="bar-compare">
                <span class="bar-label">simulated</span>
                <span class="bar-track"><i style="width:${barWidth(e267NoAttack)}; background:${color}"></i></span>
                <strong>${fmt.format(e267NoAttack)}</strong>
              </div>
              <div class="matrix-note ${row.e267CarryScaledWeight ? "good-text" : "muted"}">
                ${fmt.format(row.carriedRows || 0)} not-entered rows carried, weight ${fmt.format(row.e267CarryScaledWeight || 0)}
              </div>
            </div>
          </div>
        `;
      }).join("")}
      <div class="no-attack-source-note">
        Entry reconstruction source: ${escapeHtml(entrySource.measure || "unknown")} from ${escapeHtml(entrySource.source || "unknown")}. Reconstructed entry before cap: ${fmt.format(entryTotal)}; restored e266 participant/model loss: ${fmt.format(restoredTotal)}.
      </div>
    `;
  }

  if (els.noAttackParticipantTable) {
    els.noAttackParticipantTable.innerHTML = participantRows
      .slice()
      .sort((a, b) => (b.e266RestoredScaledWeight || 0) - (a.e266RestoredScaledWeight || 0) || (b.e267CarryScaledWeight || 0) - (a.e267CarryScaledWeight || 0) || (a.modelLabel || "").localeCompare(b.modelLabel || "") || (a.address || "").localeCompare(b.address || ""))
      .map((row) => {
        const status = row.e267Status === "carried_into_e267" ? row.e267Status : row.e266Status;
        const nodes = (row.nodes || []).length ? `<div class="muted">${escapeHtml((row.nodes || []).join(", "))}${row.nodeCount > (row.nodes || []).length ? ` +${fmt.format(row.nodeCount - row.nodes.length)} nodes` : ""}</div>` : "";
        return `
          <tr>
            <td><button class="row-button mono" data-address="${escapeHtml(row.address)}">${escapeHtml(row.address)}</button>${nodes}</td>
            <td><span class="tag" style="border-color:${modelCapColor(row.modelLabel)}">${escapeHtml(row.modelLabel || row.modelId)}</span><br><span class="muted">${fmt.format(row.entryCommitRows || 0)} entry commits</span></td>
            <td class="num">${fmt.format(row.entryRawWeight || 0)}</td>
            <td class="num">${fmt.format(row.entryScaledWeight || 0)}<br><span class="muted">scale ${fmt.format(row.weightScaleFactorE266 || 0)}x</span></td>
            <td class="num">${fmt.format(row.e266ActualScaledWeight || 0)}<br><span class="muted">raw ${fmt.format(row.e266ActualRawWeight || 0)}</span></td>
            <td class="num">${fmt.format(row.e266RestoredScaledWeight || 0)}</td>
            <td class="num">${fmt.format(row.e267ActualScaledWeight || 0)}<br><span class="muted">raw ${fmt.format(row.e267ActualRawWeight || 0)}</span></td>
            <td class="num">${fmt.format(row.e267SimulatedScaledWeight || 0)}${row.e267CarryScaledWeight ? `<br><span class="muted">carry ${fmt.format(row.e267CarryScaledWeight)}</span>` : ""}</td>
            <td><span class="status-chip ${noAttackStatusClass(status)}">${escapeHtml(noAttackStatusLabel(status))}</span><br><span class="muted">${escapeHtml(noAttackStatusLabel(row.e267Status))}</span></td>
          </tr>
        `;
      }).join("");
    enhanceAddressActions(els.noAttackParticipantTable);
  }
}

function renderModelCapChart() {
  const payload = state.data.chartData?.modelCapFactors || { rows: [], summary: {} };
  const rows = (payload.rows || []).filter((row) => row.epoch && row.modelId && row.status !== "missing_subgroup");
  const epochs = [...new Set(rows.map((row) => row.epoch))].sort((a, b) => a - b);
  const labels = [...new Set(rows.map((row) => row.modelLabel || row.modelId))].sort();
  const byKey = new Map(rows.map((row) => [`${row.epoch}|${row.modelLabel || row.modelId}`, row]));
  const rowCount = document.getElementById("modelCapRows");
  if (rowCount) rowCount.textContent = `${rows.length} rows`;

  if (!rows.length) {
    state.charts.modelCap.setOption({
      title: { text: "Model cap archive data is not loaded", left: "center", top: "middle", textStyle: { color: "#a7afba", fontSize: 13, fontWeight: 400 } },
      xAxis: { show: false },
      yAxis: { show: false },
      series: [],
    }, true);
    if (els.modelCapTable) els.modelCapTable.innerHTML = "";
    return;
  }

  const statusRows = rows
    .slice()
    .sort((a, b) => a.epoch - b.epoch || (a.modelLabel || "").localeCompare(b.modelLabel || ""))
    .map((row) => {
      const cap = row.capWeight == null ? "exempt" : fmt.format(row.capWeight || 0);
      const statusClass = row.status === "capped" ? "warn" : row.status === "initial_exempt" ? "good" : "";
      const scale = row.appliedScale == null ? "-" : `${fmt.format((row.appliedScale || 0) * 100)}%`;
      return `
        <tr>
          <td class="num">e${row.epoch}</td>
          <td title="${escapeHtml(row.modelId)}">${escapeHtml(row.modelLabel || row.modelId)}</td>
          <td><span class="tag ${statusClass}">${escapeHtml(modelCapStatusLabel(row.status))}</span></td>
          <td class="num">${scale}</td>
          <td class="num">${fmt.format(row.rawConsensusWeight || 0)}</td>
          <td class="num">${cap}</td>
          <td class="num">${row.pressureRatio ? `${fmt.format(row.pressureRatio)}x` : "-"}</td>
        </tr>
      `;
    }).join("");
  if (els.modelCapTable) els.modelCapTable.innerHTML = statusRows;

  state.charts.modelCap.setOption({
    grid: { left: 72, right: 32, top: 36, bottom: 54 },
    legend: { top: 6, textStyle: { color: "#a7afba" } },
    tooltip: chartTooltip({
      trigger: "axis",
      formatter: (params) => {
        const epoch = epochs[params[0]?.dataIndex] || "";
        const lines = [`<strong>Epoch ${epoch}</strong>`];
        for (const item of params) {
          const row = byKey.get(`${epoch}|${item.seriesName}`);
          if (!row) continue;
          const cap = row.capWeight == null ? "exempt" : fmt.format(row.capWeight || 0);
          const scale = row.appliedScale == null ? "-" : `${fmt.format((row.appliedScale || 0) * 100)}% scale`;
          lines.push(
            `<span style="color:${item.color}">●</span> ${escapeHtml(row.modelLabel || row.modelId)}: ${scale}`,
            `${escapeHtml(modelCapStatusLabel(row.status))}`,
            `raw consensus ${fmt.format(row.rawConsensusWeight || 0)} · cap ${cap}`,
            `raw subgroup ${fmt.format(row.subgroupRawWeight || 0)} · coeff ${fmt.format(row.weightScaleFactor || 0)}`,
            `pressure ${row.pressureRatio ? `${fmt.format(row.pressureRatio)}x` : "-"} · participants ${fmt.format(row.participantCount || 0)} · nodes ${fmt.format(row.nodeCount || 0)}`,
            `height ${fmt.format(row.height || 0)} · source ${escapeHtml(row.source || "")} · params ${escapeHtml(row.paramsSource || "")}`
          );
        }
        return lines.join("<br>");
      },
    }),
    xAxis: { type: "category", data: epochs.map((epoch) => `e${epoch}`), axisLabel: { color: "#a7afba" } },
    yAxis: {
      type: "value",
      min: 0,
      max: 1.05,
      axisLabel: { color: "#a7afba", formatter: (v) => `${Math.round(v * 100)}%` },
      name: "applied scale",
      nameTextStyle: { color: "#a7afba" },
    },
    series: [
      {
        name: "100% reference",
        type: "line",
        data: epochs.map(() => 1),
        symbol: "none",
        lineStyle: { color: "#6d7682", type: "dashed", width: 1 },
        tooltip: { show: false },
        markArea: {
          silent: true,
          itemStyle: { color: "rgba(217, 101, 95, 0.08)" },
          data: [[{ xAxis: "e265", name: "attack" }, { xAxis: "e265" }], [{ xAxis: "e266", name: "N-1 collapse" }, { xAxis: "e266" }]],
        },
      },
      ...labels.map((label, index) => ({
        name: label,
        type: "line",
        data: epochs.map((epoch) => byKey.get(`${epoch}|${label}`)?.appliedScale ?? null),
        connectNulls: false,
        symbolSize: 8,
        lineStyle: { width: 3, color: modelCapColor(label, index) },
        itemStyle: { color: modelCapColor(label, index) },
        areaStyle: { color: modelCapColor(label, index), opacity: 0.06 },
      })),
    ],
  }, true);
}

function renderModelCapMechanics() {
  const payload = state.data.chartData?.modelCapFactors || { rows: [], paramModelRows: [], summary: {} };
  const rows = (payload.rows || []).filter((row) => row.epoch && row.modelId && row.status !== "missing_subgroup");
  const kimiRows = rows.filter((row) => (row.modelLabel || "").toLowerCase() === "kimi").sort((a, b) => a.epoch - b.epoch);
  const epochs = [...new Set(rows.map((row) => row.epoch))].sort((a, b) => a - b);
  const labels = [...new Set(rows.map((row) => row.modelLabel || row.modelId))].sort();
  const byKey = new Map(rows.map((row) => [`${row.epoch}|${row.modelLabel || row.modelId}`, row]));
  const summary = payload.summary || {};
  const summaryEl = document.getElementById("modelCapMechanicsSummary");
  if (summaryEl) {
    summaryEl.textContent = `${fmt.format(summary.cappedRowCount || 0)} capped · ${fmt.format(summary.totalClippedWeight || 0)} clipped`;
  }

  if (!rows.length) {
    for (const chart of [state.charts.capRecovery, state.charts.capWaterfall, state.charts.scaleTimeline, state.charts.capPressureHeatmap]) {
      chart.setOption({ title: { text: "Model cap mechanics data is not loaded", left: "center", top: "middle", textStyle: { color: "#a7afba", fontSize: 13, fontWeight: 400 } }, xAxis: { show: false }, yAxis: { show: false }, series: [] }, true);
    }
    if (els.modelCapMechanicsTable) els.modelCapMechanicsTable.innerHTML = "";
    return;
  }

  if (els.modelCapMechanicsTable) {
    els.modelCapMechanicsTable.innerHTML = rows
      .slice()
      .sort((a, b) => a.epoch - b.epoch || (a.modelLabel || "").localeCompare(b.modelLabel || ""))
      .map((row) => {
        const cap = row.capWeight == null ? "exempt" : fmt.format(row.capWeight || 0);
        const clipped = row.clippedWeight ? fmt.format(row.clippedWeight) : "-";
        const headroom = row.capHeadroom == null ? "-" : fmt.format(row.capHeadroom || 0);
        return `
          <tr>
            <td class="num">e${row.epoch}</td>
            <td title="${escapeHtml(row.modelId)}">${escapeHtml(row.modelLabel || row.modelId)}</td>
            <td class="num">${fmt.format(row.subgroupRawWeight || 0)}</td>
            <td class="num">${fmt.format(row.weightScaleFactor || 0)}x</td>
            <td class="num">${fmt.format(row.rawConsensusWeight || 0)}</td>
            <td class="num">${cap}</td>
            <td class="num">${fmt.format(row.countedWeight || row.cappedConsensusWeight || 0)}</td>
            <td class="num">${clipped}</td>
            <td class="num">${headroom}</td>
          </tr>
        `;
      }).join("");
  }

  const frozenScaleByModel = new Map();
  for (const row of kimiRows) {
    const label = row.modelLabel || row.modelId;
    if (!frozenScaleByModel.has(label) && row.weightScaleFactor != null) {
      frozenScaleByModel.set(label, row.weightScaleFactor);
    }
  }
  const isFrozenScale = state.kimiScaleScenario === "frozen" || state.kimiScaleScenario === "frozenScale";
  const isConstantRaw = state.kimiScaleScenario === "constantRaw";
  const isNoAttackE266 = state.kimiScaleScenario === "noAttackE266";
  const isLegacyFixedScale = state.kimiScaleScenario === "fixedScale125";
  const isScaleLocked = isConstantRaw && state.kimiScaleLocked;
  const beforeScaleLabel = isNoAttackE266 ? "rebuilt/actual raw" : isConstantRaw ? "shock raw" : "actual raw";
  const beforeScaleSeriesName = `Before scale (${beforeScaleLabel})`;
  const afterScaleSeriesName = isFrozenScale
    ? "After fixed scale (raw consensus)"
    : isNoAttackE266
      ? "After scale (no e266 attack)"
    : isConstantRaw
      ? isScaleLocked || isLegacyFixedScale
        ? "After shock raw (1.25 scale)"
        : "After shock raw (actual scale)"
      : isLegacyFixedScale
      ? "After fixed scale 1.25"
      : "After scale (raw consensus)";
  const finalCountSeriesName = isFrozenScale
    ? "Final counted (fixed scale)"
    : isNoAttackE266
      ? "Final counted (no e266 attack)"
    : isConstantRaw
      ? isScaleLocked || isLegacyFixedScale
        ? "Final counted (shock raw + 1.25 scale)"
        : "Final counted (shock raw)"
      : isLegacyFixedScale
      ? "Final counted (fixed scale 1.25)"
      : "Final counted (after cap)";
  const resolveScenarioScale = (row) => {
    if (isScaleLocked || isLegacyFixedScale) return 1.25;
    if (!isFrozenScale) return row.weightScaleFactor || 0;
    const label = row.modelLabel || row.modelId;
    return frozenScaleByModel.get(label) ?? (row.weightScaleFactor || 0);
  };
  const fixedRaw = Math.max(0, Math.floor(state.kimiFixedRawWeight || 0));
  const dipRaw = Math.max(0, Math.floor(state.kimiDipRawWeight || 0));
  const fixedQwen = Math.max(0, Math.floor(state.kimiFixedQwenWeight || 0));
  const baselineRaw = fixedRaw > 0 ? fixedRaw : (kimiRows[0]?.subgroupRawWeight || 0);
  const simulatedRawForEpoch = (epoch) => (epoch === 266 ? dipRaw : baselineRaw);
  const isSimulatedCap = isConstantRaw;
  const noAttackScenario = payload.noAttackE266Scenario || { rows: [], summary: {} };
  const noAttackRows = noAttackScenario.rows || [];
  renderNoAttackEvidence(payload);
  const noAttackByEpochModel = new Map(noAttackRows.map((row) => [`${row.epoch}|${row.modelLabel || row.modelId}`, row]));
  const actualKimiByEpoch = new Map(kimiRows.map((row) => [row.epoch, row]));
  const preSimRows = isNoAttackE266 ? noAttackRows
    .filter((row) => (row.modelLabel || "").toLowerCase() === "kimi")
    .sort((a, b) => a.epoch - b.epoch)
    .map((scenarioRow) => {
      const actualRow = actualKimiByEpoch.get(scenarioRow.epoch) || {};
      const actualScaled = actualRow.rawConsensusWeight || 0;
      const actualFinal = actualRow.countedWeight ?? actualRow.cappedConsensusWeight ?? actualScaled;
      return {
        row: { ...actualRow, epoch: scenarioRow.epoch, capFactor: scenarioRow.capFactor, status: scenarioRow.status },
        epochLabel: `e${scenarioRow.epoch}`,
        preScale: scenarioRow.rawWeight || 0,
        rawMode: scenarioRow.rawSource === "reconstructed_from_e266_entry_commits"
          ? "e266 entry commits"
          : scenarioRow.rawSource === "actual_e267_plus_e266_entry_carry"
            ? "actual e267 + e266 entry carry"
            : "actual raw",
        rawBaseValue: scenarioRow.rawWeight || 0,
        scenario: state.kimiScaleScenario,
        scaled: scenarioRow.scaledWeight || 0,
        actualScaled,
        actualFinal,
        actualScale: actualRow.weightScaleFactor || scenarioRow.weightScaleFactor || 0,
        status: scenarioRow.status,
        scaleLocked: false,
        capUtilization: scenarioRow.capLimit ? (scenarioRow.scaledWeight || 0) / scenarioRow.capLimit : 0,
        previousEpochRootTotalWeight: scenarioRow.actualPreviousEpochRootTotalWeight || 0,
        rootTotalWeight: scenarioRow.actualRootTotalWeight || 0,
        capFactor: scenarioRow.capFactor || 0,
        scaleDelta: (scenarioRow.scaledWeight || 0) - (scenarioRow.rawWeight || 0),
        clippedActual: actualFinal < actualScaled ? actualScaled - actualFinal : 0,
        capLimit: scenarioRow.capLimit,
        capLimitBasis: scenarioRow.capBasis,
        capLimitSource: "noAttackE266",
        simulatedRootTotalWeight: scenarioRow.simulatedRootTotalWeight || 0,
        final: scenarioRow.countedWeight || 0,
        clipped: scenarioRow.clippedWeight || 0,
      };
    }) : kimiRows.map((row) => {
    const scenarioScale = resolveScenarioScale(row);
    const rowRaw = isConstantRaw ? simulatedRawForEpoch(row.epoch) : (row.subgroupRawWeight || 0);
    const scenarioScaled = Math.floor((rowRaw || 0) * scenarioScale);
    const actualScale = row.weightScaleFactor || 0;
    const actualScaled = Math.floor((row.subgroupRawWeight || 0) * actualScale);
    const actualFinal = row.capWeight == null ? actualScaled : (row.countedWeight ?? row.cappedConsensusWeight ?? Math.min(actualScaled, row.capWeight || 0));
    return {
      row,
      epochLabel: `e${row.epoch}`,
      preScale: rowRaw,
      rawMode: beforeScaleLabel,
      rawBaseValue: rowRaw,
      scenario: state.kimiScaleScenario,
      scaled: scenarioScaled,
      actualScaled,
      actualFinal,
      actualScale,
      status: row.status,
      scaleLocked: isScaleLocked || isLegacyFixedScale,
      capUtilization: row.capUtilization || 0,
      previousEpochRootTotalWeight: row.previousEpochRootTotalWeight || 0,
      rootTotalWeight: row.rootTotalWeight || 0,
      capFactor: row.capFactor || 0,
      scaleDelta: scenarioScaled - (rowRaw || 0),
      clippedActual: actualFinal < actualScaled ? actualScaled - actualFinal : 0,
    };
  });
  // Chain cap uses previous epoch final total_weight, so simulations must pass forward final counted weight.
  const simulatedRootByEpoch = new Map();
  const capRecoveryRows = isNoAttackE266 ? preSimRows : preSimRows.map((entry) => {
    const { row, scaled } = entry;
    const canApplyCap = row.capWeight != null && row.capApplies !== false;
    const previousEpochRoot = row.previousEpochRootTotalWeight || 0;
    const previousSimulatedRoot = simulatedRootByEpoch.get(row.epoch - 1);
    const previousEpochRootSimulated = isSimulatedCap
      ? (previousSimulatedRoot ?? previousEpochRoot)
      : previousEpochRoot;
    const capLimit = canApplyCap && isSimulatedCap
      ? Math.floor((row.capFactor || 0) * previousEpochRootSimulated)
      : (row.capWeight == null ? null : row.capWeight);
    const final = capLimit == null ? scaled : Math.min(scaled, capLimit);
    const simulatedRootTotalWeight = isSimulatedCap
      ? fixedQwen + final
      : (row.rootTotalWeight || 0);
    simulatedRootByEpoch.set(row.epoch, simulatedRootTotalWeight);
    return {
      ...entry,
      capLimit,
      capLimitBasis: previousEpochRootSimulated,
      capLimitSource: isSimulatedCap ? "simulated" : "actual",
      simulatedRootTotalWeight,
      final,
      clipped: capLimit == null ? 0 : Math.max(0, scaled - final),
    };
  });
  const capCompositionRows = capRecoveryRows.map((entry) => {
    const epoch = entry.row.epoch;
    if (isNoAttackE266) {
      const epochScenarioRows = noAttackRows.filter((row) => row.epoch === epoch);
      const qwen = noAttackByEpochModel.get(`${epoch}|Qwen`)?.countedWeight || 0;
      const kimi = entry.final || 0;
      const other = epochScenarioRows
        .filter((row) => !["Kimi", "Qwen"].includes(row.modelLabel || row.modelId))
        .reduce((sum, row) => sum + (row.countedWeight || 0), 0);
      const modelTotal = qwen + kimi + other;
      const rootTotal = entry.simulatedRootTotalWeight || modelTotal;
      return { epoch, qwen, kimi, other, modelTotal, rootTotal };
    }
    const qwenRow = byKey.get(`${epoch}|Qwen`);
    const qwenActual = qwenRow ? (qwenRow.countedWeight ?? qwenRow.cappedConsensusWeight ?? qwenRow.rawConsensusWeight ?? 0) : 0;
    const qwen = isSimulatedCap ? fixedQwen : qwenActual;
    const kimi = entry.final || 0;
    const other = isSimulatedCap
      ? 0
      : rows
        .filter((row) => row.epoch === epoch && !["Kimi", "Qwen"].includes(row.modelLabel || row.modelId))
        .reduce((sum, row) => sum + (row.countedWeight ?? row.cappedConsensusWeight ?? row.rawConsensusWeight ?? 0), 0);
    const modelTotal = qwen + kimi + other;
    const rootTotal = isSimulatedCap ? entry.simulatedRootTotalWeight : (entry.row.rootTotalWeight || modelTotal);
    return { epoch, qwen, kimi, other, modelTotal, rootTotal };
  });

  state.charts.capRecovery.setOption({
    grid: { left: 78, right: 36, top: 44, bottom: 56 },
    tooltip: chartTooltip({
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        if (!params?.length) return "";
        const index = params[0]?.dataIndex;
        const row = capRecoveryRows[index];
        if (!row) return "";
        const clipped = row.scaled > row.final ? row.scaled - row.final : 0;
        const clippedActual = row.actualScaled > row.actualFinal ? row.actualScaled - row.actualFinal : 0;
        const clippedPct = row.scaled ? (clipped / row.scaled) * 100 : 0;
        const capLimitBasis = row.capLimitBasis == null ? row.previousEpochRootTotalWeight : row.capLimitBasis;
        const capLimitTag = row.capLimitSource === "simulated"
          ? "simulated"
          : row.capLimitSource === "noAttackE266"
            ? "no-attack simulation"
            : "actual";
        const rootBasisText = row.capLimitSource === "simulated"
          ? `   Chain-style basis: simulated e${row.row.epoch - 1} total_weight <strong>${fmt.format(capLimitBasis)}</strong>`
          : row.capLimitSource === "noAttackE266"
            ? row.row.epoch === 266
              ? `   No-attack basis: actual e265 total_weight <strong>${fmt.format(capLimitBasis)}</strong>`
              : `   No-attack basis: simulated e${row.row.epoch - 1} total_weight <strong>${fmt.format(capLimitBasis)}</strong>`
            : `   Chain-style basis: actual e${row.row.epoch - 1} total_weight <strong>${fmt.format(capLimitBasis)}</strong>`;
        const scaleStepLabel = row.scenario === "frozen" || row.scenario === "frozenScale"
          ? "After fixed scale (raw consensus)"
          : row.scenario === "noAttackE266"
            ? "After scale (no e266 attack)"
            : row.scenario === "constantRaw"
              ? row.scaleLocked ? "After shock raw (1.25 scale)" : "After shock raw (raw × actual scale)"
              : row.scenario === "fixedScale125"
                ? "After fixed scale 1.25"
                : "After scale (raw consensus)";
        const finalStepLabel = row.scenario === "frozen" || row.scenario === "frozenScale"
          ? "Final counted under fixed scale (after cap)"
          : row.scenario === "noAttackE266"
            ? "Final counted in no-attack simulation (after cap)"
            : row.scenario === "constantRaw"
              ? row.scaleLocked ? "Final counted (shock raw + 1.25 scale)" : "Final counted (shock raw, after cap)"
              : row.scenario === "fixedScale125"
                ? "Final counted (fixed scale 1.25)"
                : "Final counted (after cap)";
        const noAttackNote = row.scenario === "noAttackE266"
          ? row.row.epoch === 266
            ? "No-attack mode: e266 is rebuilt from entry commits multiplied by the model scale factor."
            : row.row.epoch === 267
              ? "No-attack mode: actual e267 model rows are kept, and missing e266 entry rows are carried forward."
              : "No-attack mode: actual raw model weights are kept; the cap basis comes from the simulated previous epoch."
          : "";
        const lines = [
          `<strong>${row.epochLabel} (Kimi) recovery path</strong>`,
          `1) Before scale (${row.rawMode}): <strong>${fmt.format(row.preScale)}</strong>`,
          noAttackNote,
          `2) ${scaleStepLabel}`,
          `   <strong>${fmt.format(row.scaled)}</strong>${row.scaleDelta ? `  (${row.scaleDelta > 0 ? "+" : ""}${fmt.format(row.scaleDelta)} by model scale)` : ""}`,
          row.scenario === "frozen" || row.scenario === "frozenScale" ? `   Baseline scale for this model is <strong>${fmt.format(row.actualScale)}x</strong>` : "",
          `3) Cap ceiling: ${row.capLimit == null ? "<i>not set</i>" : `<strong>${fmt.format(row.capLimit)}</strong> (${fmt.format(capLimitBasis)} × ${fmt.format(row.capFactor)} · ${capLimitTag})`}`,
          row.capLimit == null ? "" : rootBasisText,
          `4) ${finalStepLabel}`,
          `<strong>${fmt.format(row.final)}</strong>`,
          clipped > 0 ? `Clipped by cap: <strong>${fmt.format(clipped)}</strong> (${fmt.format(clippedPct)}%)` : "Clipped by cap: <strong>0</strong>",
          row.capLimitSource === "simulated" ? `Simulated total_weight passed forward: <strong>${fmt.format(row.simulatedRootTotalWeight || 0)}</strong> (${fmt.format(state.kimiFixedQwenWeight || 0)} Qwen + ${fmt.format(row.final || 0)} Kimi)` : "",
          row.capLimitSource === "noAttackE266" ? `No-attack total_weight passed forward: <strong>${fmt.format(row.simulatedRootTotalWeight || 0)}</strong>` : "",
          capCompositionRows[index] && row.capLimitSource === "simulated" ? `Simulated total composition: Qwen <strong>${fmt.format(capCompositionRows[index].qwen)}</strong> + Kimi <strong>${fmt.format(capCompositionRows[index].kimi)}</strong> = <strong>${fmt.format(capCompositionRows[index].rootTotal)}</strong>` : "",
          capCompositionRows[index] && row.capLimitSource !== "simulated" ? `Model weights after cap: Qwen <strong>${fmt.format(capCompositionRows[index].qwen)}</strong> + Kimi <strong>${fmt.format(capCompositionRows[index].kimi)}</strong>${capCompositionRows[index].other ? ` + Other <strong>${fmt.format(capCompositionRows[index].other)}</strong>` : ""} = <strong>${fmt.format(capCompositionRows[index].modelTotal)}</strong><br>Root total_weight: <strong>${fmt.format(capCompositionRows[index].rootTotal)}</strong>` : "",
          row.scenario === "frozen" || row.scenario === "frozenScale" || row.scenario === "constantRaw" || row.scenario === "fixedScale125" || row.scenario === "noAttackE266" ? `Actual trajectory would be ${fmt.format(row.actualScaled)} → <strong>${fmt.format(row.actualFinal)}</strong> (${fmt.format(clippedActual)} clipped)` : "",
          `Status: ${escapeHtml(modelCapStatusLabel(row.status))}`,
          row.capUtilization ? `Utilization: <strong>${fmt.format(row.capUtilization)}x</strong>` : "",
        ];
        return lines.filter(Boolean).join("<br>");
      },
    }),
    legend: {
      top: 6,
      textStyle: { color: "#a7afba" },
      selected: {
        "After-cap stack: Qwen": true,
        "After-cap stack: Kimi": true,
        "After-cap stack: Other": capCompositionRows.some((row) => row.other > 0),
        [beforeScaleSeriesName]: true,
        [afterScaleSeriesName]: true,
        "Prev total weight (cap basis)": true,
        "Cap limit (prev epoch × factor)": true,
        [finalCountSeriesName]: true,
      },
    },
    xAxis: {
      type: "category",
      data: capRecoveryRows.map((row) => row.epochLabel),
      axisLabel: { color: "#a7afba" },
      splitLine: { show: true, lineStyle: { color: "rgba(128, 140, 154, 0.25)" } },
    },
    yAxis: {
      type: "value",
      min: 0,
      axisLabel: { color: "#a7afba", formatter: (value) => compact.format(value) },
      name: "weight",
      nameTextStyle: { color: "#a7afba" },
      splitLine: { lineStyle: { color: "rgba(128, 140, 154, 0.2)" } },
    },
    series: [
      {
        name: "After-cap stack: Qwen",
        type: "bar",
        stack: "cap-total-composition",
        data: capCompositionRows.map((row) => row.qwen),
        barWidth: 18,
        itemStyle: { color: "rgba(93, 169, 233, 0.28)" },
        emphasis: { itemStyle: { color: "rgba(93, 169, 233, 0.42)" } },
        z: 0,
      },
      {
        name: "After-cap stack: Kimi",
        type: "bar",
        stack: "cap-total-composition",
        data: capCompositionRows.map((row) => row.kimi),
        barWidth: 18,
        itemStyle: { color: "rgba(121, 182, 106, 0.3)" },
        emphasis: { itemStyle: { color: "rgba(121, 182, 106, 0.46)" } },
        z: 0,
      },
      {
        name: "After-cap stack: Other",
        type: "bar",
        stack: "cap-total-composition",
        data: capCompositionRows.map((row) => row.other || null),
        barWidth: 18,
        itemStyle: { color: "rgba(143, 122, 211, 0.24)" },
        emphasis: { itemStyle: { color: "rgba(143, 122, 211, 0.4)" } },
        z: 0,
      },
      {
        name: beforeScaleSeriesName,
        type: "line",
        data: capRecoveryRows.map((row) => row.preScale),
        symbolSize: 7,
        lineStyle: { color: "#7a8793", width: 2, type: "dotted" },
        itemStyle: { color: "#7a8793" },
        showSymbol: true,
      },
      {
        name: afterScaleSeriesName,
        type: "line",
        data: capRecoveryRows.map((row) => row.scaled),
        symbolSize: 8,
        lineStyle: { color: "#d9655f", width: 3 },
        itemStyle: { color: "#d9655f" },
        showSymbol: false,
      },
      {
        name: "Prev total weight (cap basis)",
        type: "line",
        data: capRecoveryRows.map((row) => row.capLimit == null ? null : row.capLimitBasis),
        symbolSize: 7,
        symbol: "triangle",
        lineStyle: { color: "#5da9e9", width: 2, type: "dotted" },
        itemStyle: { color: "#5da9e9" },
        showSymbol: true,
      },
      {
        name: "Cap limit (prev epoch × factor)",
        type: "line",
        data: capRecoveryRows.map((row) => row.capLimit),
        symbolSize: 8,
        symbol: "circle",
        lineStyle: { color: "#d7a84f", width: 2, type: "dashed" },
        itemStyle: { color: "#d7a84f" },
        showSymbol: true,
      },
      {
        name: finalCountSeriesName,
        type: "line",
        data: capRecoveryRows.map((row) => row.final),
        symbol: "diamond",
        symbolSize: 8,
        lineStyle: { color: "#79b66a", width: 3.5 },
        itemStyle: { color: "#79b66a" },
      },
    ],
  }, true);

  const waterfallEpochs = epochs.filter((epoch) => epoch >= 265);
  const packageEpochSet = new Set(((state.data.epochs || [])
    .filter((row) => row.componentSource === "cap_e267_e276")
    .map((row) => Number(row.epoch))
  ));
  if (packageEpochSet.size === 0) {
    for (let e = 267; e <= 276; e += 1) packageEpochSet.add(e);
  }
  const buildRanges = (values, maxGap = 1) => {
    const sorted = [...new Set(values)].map(Number).sort((a, b) => a - b);
    if (!sorted.length) return [];
    const ranges = [];
    let start = sorted[0];
    let end = sorted[0];
    for (let i = 1; i < sorted.length; i += 1) {
      const value = sorted[i];
      if (value <= end + maxGap) {
        end = value;
      } else {
        ranges.push([start, end]);
        start = end = value;
      }
    }
    ranges.push([start, end]);
    return ranges;
  };
  const compensationRanges = buildRanges([...packageEpochSet]);
  const compensationMarkAreas = compensationRanges
    .filter((range) => range[0] <= range[1])
    .map(([start, end]) => [
      { name: "Compensation package", xAxis: `e${start}`, yAxis: "min" },
      { xAxis: `e${end}`, yAxis: "max" },
    ]);
  const kimiCutRows = waterfallEpochs.map((epoch) => {
    const row = byKey.get(`${epoch}|Kimi`);
    if (!row) return { epoch, missing: true };
    const raw = row.subgroupRawWeight || 0;
    const afterScale = row.rawConsensusWeight || 0;
    const final = row.countedWeight ?? row.cappedConsensusWeight ?? afterScale;
    const clipped = Math.max(0, afterScale - final);
    const cap = row.capWeight == null ? null : row.capWeight;
    const previousRoot = row.previousEpochRootTotalWeight || 0;
    const clippedPct = afterScale ? (clipped / afterScale) * 100 : 0;
    const requiredPreviousRoot = row.capFactor ? Math.ceil(afterScale / row.capFactor) : 0;
    return {
      epoch,
      raw,
      afterScale,
      final,
      clipped,
      cap,
      previousRoot,
      capFactor: row.capFactor || 0,
      scale: row.weightScaleFactor || 0,
      clippedPct,
      requiredPreviousRoot,
      missingPreviousRoot: Math.max(0, requiredPreviousRoot - previousRoot),
      status: row.status,
      participantCount: row.participantCount || 0,
      nodeCount: row.nodeCount || 0,
    };
  });
  state.charts.capWaterfall.setOption({
    grid: { left: 80, right: 28, top: 52, bottom: 84 },
    legend: {
      top: 6,
      textStyle: { color: "#a7afba" },
      selectedMode: true,
    },
    tooltip: chartTooltip({
      trigger: "axis",
      formatter: (params) => {
        const epoch = waterfallEpochs[params[0]?.dataIndex];
        const row = kimiCutRows[params[0]?.dataIndex];
        if (!row || row.missing) return `<strong>Epoch ${epoch}</strong><br>No Kimi cap row`;
        const isCompensationEpoch = packageEpochSet.has(epoch);
        const lines = [
          `<strong>Epoch ${epoch} Kimi cap cut</strong>${isCompensationEpoch ? " · <b>compensation package</b>" : ""}`,
          `Raw Kimi: <strong>${fmt.format(row.raw)}</strong>`,
          `After scale: <strong>${fmt.format(row.afterScale)}</strong> (${fmt.format(row.scale)}x)`,
          `Cap limit: ${row.cap == null ? "<i>not set</i>" : `<strong>${fmt.format(row.cap)}</strong> = ${fmt.format(row.previousRoot)} × ${fmt.format(row.capFactor)}`}`,
          `Final after cap: <strong>${fmt.format(row.final)}</strong>`,
          `Clipped: <strong>${fmt.format(row.clipped)}</strong> (${fmt.format(row.clippedPct)}%)`,
          row.missingPreviousRoot ? `Previous total needed to avoid cap: <strong>${fmt.format(row.requiredPreviousRoot)}</strong> · missing ${fmt.format(row.missingPreviousRoot)}` : "",
          `Participants ${fmt.format(row.participantCount)} · nodes ${fmt.format(row.nodeCount)} · ${escapeHtml(modelCapStatusLabel(row.status))}`,
        ];
        return lines.join("<br>");
      },
    }),
    xAxis: {
      type: "category",
      data: kimiCutRows.map((row) => `e${row.epoch}`),
      axisLabel: { color: "#a7afba" },
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(128, 140, 154, 0.28)" },
      },
      name: "epoch",
      nameTextStyle: { color: "#a7afba" },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#a7afba", formatter: (value) => compact.format(value) },
      name: "weight",
      nameTextStyle: { color: "#a7afba" },
    },
    series: [
      {
        name: "Kimi final after cap",
        type: "bar",
        stack: "kimi-cap-cut",
        data: kimiCutRows.map((row) => row.missing ? null : row.final),
        barWidth: 24,
        itemStyle: { color: "#79b66a" },
      },
      {
        name: "Kimi clipped by cap",
        type: "bar",
        stack: "kimi-cap-cut",
        data: kimiCutRows.map((row) => row.missing ? null : row.clipped || 0),
        barWidth: 24,
        itemStyle: { color: "#d9655f" },
      },
      {
        name: "Kimi after scale",
        type: "line",
        data: kimiCutRows.map((row) => row.missing ? null : row.afterScale),
        symbolSize: 8,
        lineStyle: { color: "#f0ede5", width: 2 },
        itemStyle: { color: "#f0ede5" },
      },
      {
        name: "Cap limit",
        type: "line",
        data: kimiCutRows.map((row) => row.missing ? null : row.cap),
        symbol: "circle",
        symbolSize: 8,
        lineStyle: { color: "#d7a84f", width: 2.5, type: "dashed" },
        itemStyle: { color: "#d7a84f" },
      },
    ],
    markArea: {
      silent: true,
      itemStyle: { color: "rgba(217, 101, 95, 0.08)" },
      data: compensationMarkAreas,
    },
  }, true);

  const paramRows = (payload.paramModelRows || []).filter((row) => row.position === "start" || row.position === "change" || row.position === "end");
  const paramEpochs = [...new Set(paramRows.map((row) => `${row.epoch}:${row.position}`))].sort((a, b) => {
    const [epochA, posA] = a.split(":");
    const [epochB, posB] = b.split(":");
    const order = { start: 0, change: 1, end: 2 };
    return Number(epochA) - Number(epochB) || (order[posA] || 0) - (order[posB] || 0);
  });
  const paramLabels = paramEpochs.map((key) => {
    const [epoch, position] = key.split(":");
    return position === "end" ? `e${epoch}` : `e${epoch} ${position}`;
  });
  const paramModels = [...new Set(paramRows.map((row) => row.modelLabel || row.modelId))].sort();
  const paramByKey = new Map(paramRows.map((row) => [`${row.epoch}:${row.position}|${row.modelLabel || row.modelId}`, row]));
  state.charts.scaleTimeline.setOption({
    grid: { left: 62, right: 24, top: 42, bottom: 62 },
    legend: { top: 6, textStyle: { color: "#a7afba" } },
    tooltip: chartTooltip({
      trigger: "axis",
      formatter: (params) => {
        const key = paramEpochs[params[0]?.dataIndex] || "";
        const lines = [`<strong>${escapeHtml(paramLabels[params[0]?.dataIndex] || "")}</strong>`];
        for (const item of params) {
          const row = paramByKey.get(`${key}|${item.seriesName}`);
          if (!row) continue;
          lines.push(`<span style="color:${item.color}">●</span> ${escapeHtml(row.modelLabel || row.modelId)}: ${fmt.format(row.weightScaleFactor || 0)}x`, `height ${fmt.format(row.height || 0)} · cap ${fmt.format(row.capFactor || 0)} · initial ${escapeHtml(row.initialModelLabel || "")}`);
        }
        return lines.join("<br>");
      },
    }),
    xAxis: { type: "category", data: paramLabels, axisLabel: { color: "#a7afba", rotate: 30 } },
    yAxis: { type: "value", axisLabel: { color: "#a7afba" }, name: "scale factor", nameTextStyle: { color: "#a7afba" } },
    series: paramModels.map((label, index) => ({
      name: label,
      type: "line",
      step: "end",
      connectNulls: true,
      symbolSize: 7,
      data: paramEpochs.map((key) => paramByKey.get(`${key}|${label}`)?.weightScaleFactor ?? null),
      lineStyle: { width: 3, color: modelCapColor(label, index) },
      itemStyle: { color: modelCapColor(label, index) },
    })),
  }, true);

  const kimiPressureRows = kimiRows
    .filter((row) => row.previousEpochRootTotalWeight)
    .map((row) => {
      const previousTotal = row.previousEpochRootTotalWeight || 0;
      const raw = row.rawConsensusWeight || 0;
      const counted = row.countedWeight ?? row.cappedConsensusWeight ?? raw;
      const clipped = row.clippedWeight || 0;
      const capPct = (row.capFactor || 0.75) * 100;
      return {
        ...row,
        rawPct: previousTotal ? (raw / previousTotal) * 100 : 0,
        countedPct: previousTotal ? (counted / previousTotal) * 100 : 0,
        clippedPct: previousTotal ? (clipped / previousTotal) * 100 : 0,
        capPct,
      };
    });
  state.charts.capPressureHeatmap.setOption({
    grid: { left: 68, right: 76, top: 58, bottom: 58 },
    legend: { top: 8, textStyle: { color: "#a7afba" } },
    tooltip: chartTooltip({
      trigger: "axis",
      formatter: (params) => {
        const row = kimiPressureRows[params[0]?.dataIndex];
        if (!row) return "";
        const capped = row.clippedWeight ? "cap clipped the excess" : "under cap";
        return [
          `<strong>e${row.epoch} Kimi</strong>`,
          `${escapeHtml(capped)} · ${escapeHtml(modelCapStatusLabel(row.status))}`,
          `wanted raw ${fmt.format(row.rawPct)}% of previous network weight`,
          `allowed cap ${fmt.format(row.capPct)}% = ${fmt.format(row.capWeight || 0)} weight`,
          `counted ${fmt.format(row.countedPct)}% = ${fmt.format(row.countedWeight || row.cappedConsensusWeight || 0)} weight`,
          row.clippedWeight ? `clipped excess ${fmt.format(row.clippedPct)}% = ${fmt.format(row.clippedWeight || 0)} weight` : "",
          `previous epoch total ${fmt.format(row.previousEpochRootTotalWeight || 0)}`,
          `scale factor ${fmt.format(row.weightScaleFactor || 0)}x · participants ${fmt.format(row.participantCount || 0)} · nodes ${fmt.format(row.nodeCount || 0)}`,
        ].filter(Boolean).join("<br>");
      },
    }),
    xAxis: {
      type: "category",
      data: kimiPressureRows.map((row) => `e${row.epoch}`),
      axisLabel: { color: "#a7afba", interval: 0 },
      splitLine: {
        show: true,
        lineStyle: { color: "rgba(128, 140, 154, 0.25)" },
      },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: Math.max(100, Math.ceil(Math.max(...kimiPressureRows.map((row) => row.rawPct || 0), 75) / 25) * 25),
      axisLabel: { color: "#a7afba", formatter: (value) => `${fmt.format(value)}%` },
      name: "share of previous epoch total weight",
      nameTextStyle: { color: "#a7afba" },
      splitLine: { lineStyle: { color: "rgba(128, 140, 154, 0.16)" } },
    },
    series: [
      {
        name: "Kimi counted",
        type: "bar",
        stack: "kimi-pressure",
        data: kimiPressureRows.map((row) => row.countedPct),
        barMaxWidth: 42,
        itemStyle: { color: "#79b66a" },
        label: {
          show: true,
          position: "inside",
          color: "#071311",
          fontWeight: 700,
          formatter: (item) => item.value >= 10 ? `${fmt.format(item.value)}%` : "",
        },
      },
      {
        name: "Clipped excess",
        type: "bar",
        stack: "kimi-pressure",
        data: kimiPressureRows.map((row) => row.clippedPct),
        barMaxWidth: 42,
        itemStyle: { color: "#d9655f" },
        label: {
          show: true,
          position: "top",
          color: "#f4f0e8",
          formatter: (item) => item.value > 0 ? `cut ${fmt.format(item.value)}%` : "",
        },
      },
      {
        name: "Kimi wanted raw",
        type: "line",
        data: kimiPressureRows.map((row) => row.rawPct),
        symbolSize: 8,
        lineStyle: { color: "#f0ede5", width: 2.5 },
        itemStyle: { color: "#f0ede5" },
      },
      {
        name: "75% cap",
        type: "line",
        data: kimiPressureRows.map((row) => row.capPct || 75),
        symbol: "none",
        lineStyle: { color: "#d7a84f", width: 2.5, type: "dashed" },
        markArea: {
          silent: true,
          itemStyle: { color: "rgba(121, 182, 106, 0.06)" },
          data: [[{ yAxis: 0 }, { yAxis: 75 }]],
        },
      },
    ],
  }, true);
}

function renderHeatmap() {
  const timelineRows = new Map((state.data.chartData?.participantEpochTimeline?.rows || []).map((row) => [row.address, row]));
  const maxTimelineWeight = (address) => {
    const timelineRow = timelineRows.get(address);
    if (!timelineRow) return 0;
    return Math.max(0, ...timelineRow.cells.map((cell) => cell.weight || cell.startWeight || cell.confirmationWeight || 0));
  };
  const rows = state.filteredRecipients
    .slice()
    .sort((a, b) => maxTimelineWeight(b.address) - maxTimelineWeight(a.address) || (b.totalGonka || 0) - (a.totalGonka || 0) || actorLabel(a).localeCompare(actorLabel(b)))
    .slice(0, 30);
  const epochs = Array.from({ length: 12 }, (_, i) => `e${265 + i}`);
  const epochByKey = new Map((state.data.epochs || []).map((row) => [row.key, row]));
  const values = [];
  rows.forEach((row, y) => epochs.forEach((epoch, x) => {
    const raw = row.perEpoch[epoch] || 0;
    const reward = row.claimedRewardByEpoch?.[epoch] || {};
    const claimedReward = reward.rewardedGonka || 0;
    const share = row.totalGonka ? (raw / row.totalGonka) * 100 : 0;
    const compensationRatio = raw > 0 && claimedReward > 0 ? Math.min(1.5, raw / claimedReward) : 0;
    values.push([x, y, compensationRatio, raw, row.address, claimedReward, reward.claimed ? 1 : 0, reward.earnedGonka || 0, share]);
  }));
  state.charts.heatmap.setOption({
    tooltip: chartTooltip({ formatter: (p) => {
      const row = rows[p.value[1]];
      const raw = p.value[3] || 0;
      const claimedReward = p.value[5] || 0;
      const rewardClaimed = Boolean(p.value[6]);
      const earnedReward = p.value[7] || 0;
      const share = p.value[8] || 0;
      const ratio = p.value[2] || 0;
      const epoch = epochByKey.get(epochs[p.value[0]]) || {};
      const epochShare = epoch.totalGonka ? (raw / epoch.totalGonka) * 100 : 0;
      const rewardDelta = claimedReward - raw;
      return `<strong>${escapeHtml(actorLabel(row))}</strong><br>${escapeHtml(row.address)}<br>max observed weight ${fmt.format(maxTimelineWeight(row.address))}<br>${epochs[p.value[0]]}<br>compensation ${gonka(raw)}<br>claimed reward ${gonka(claimedReward)} · ${rewardClaimed ? "claimed" : "not claimed / no summary"}<br>compensation / claimed reward ${fmt.format(ratio * 100)}%<br>earned reward ${gonka(earnedReward)}<br>claimed minus compensation ${gonka(rewardDelta)}<br>${fmt.format(share)}% of this recipient total<br>${fmt.format(epochShare)}% of epoch total<br>recipient total ${gonka(row?.totalGonka || 0)}`;
    } }),
    grid: { left: 250, right: 24, top: 24, bottom: 42 },
    xAxis: { type: "category", data: epochs, axisLabel: { color: "#a7afba" } },
    yAxis: {
      type: "category",
      inverse: true,
      data: rows.map((row) => `${shortAddress(row.address)}  ${actorShortLabel(row)}`),
      axisLabel: { align: "left", margin: 242, color: "#a7afba", width: 230, overflow: "truncate" },
    },
    visualMap: {
      min: 0,
      max: 1,
      dimension: 2,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 4,
      text: [">= claimed reward", "0"],
      textStyle: { color: "#a7afba" },
      inRange: { color: ["#222831", "#355c7d", "#4db7a8", "#d7a84f", "#d9655f"] },
    },
    series: [{
      type: "heatmap",
      data: values,
      encode: { x: 0, y: 1, value: 2 },
      itemStyle: {
        borderColor: (p) => {
          const compensation = p.value[3] || 0;
          const claimedReward = p.value[5] || 0;
          if (!compensation) return "#101114";
          if (!claimedReward) return "#6d7682";
          return compensation / claimedReward >= 0.5 ? "#eef0f2" : "#38404a";
        },
        borderWidth: (p) => {
          const compensation = p.value[3] || 0;
          const claimedReward = p.value[5] || 0;
          if (!compensation || !claimedReward) return 1;
          return compensation / claimedReward >= 0.5 ? 2 : 1;
        },
      },
    }],
  }, true);
}

function renderRecipientCompByWindow() {
  const panel = document.querySelector(".recipient-reward-history-panel");
  if (panel?.classList.contains("is-collapsed")) {
    document.getElementById("recipientCompByWindowEpochs").textContent = "Calculations in progress";
    document.getElementById("recipientCompByWindowRows").textContent = "collapsed";
    state.chartAddressRows.recipientCompByWindow = [];
    if (els.recipientCompByWindowTable) els.recipientCompByWindowTable.innerHTML = "";
    return;
  }
  const payload = state.data.chartData?.recipientRewardHistory || { rows: [], historyEpochs: [], compensationEpochs: [], summary: {} };
  const filteredAddresses = new Set(state.filteredRecipients.map((row) => row.address));
  const rows = (payload.rows || [])
    .filter((row) => filteredAddresses.has(row.address))
    .sort((a, b) => (b.maxObservedWeight || 0) - (a.maxObservedWeight || 0) || (b.compensationGonka || 0) - (a.compensationGonka || 0));
  const historyEpochs = payload.historyEpochs || [];
  const compensationEpochs = payload.compensationEpochs || [];
  const xLabels = [
    ...historyEpochs.map((epoch) => `e${epoch}`),
    ...compensationEpochs.map((epoch) => (epoch === 265 ? "e265 attack" : epoch === 266 ? "e266 excluded" : `e${epoch} cap`)),
  ];
  const maxReward = Math.max(
    payload.summary?.maxPreviousRewardGonka || 0,
    ...rows.flatMap((row) => [...(row.rewardCells || []), ...(row.compensationCells || [])].map((cell) => cell.rewardedGonka || 0)),
    1
  );
  const maxCompensation = Math.max(payload.summary?.maxCompensationGonka || 0, ...rows.map((row) => row.compensationGonka || 0), 1);
  const maxWeight = Math.max(payload.summary?.maxObservedWeight || 0, ...rows.map((row) => row.maxObservedWeight || 0), 1);
  const heatmapRows = [];
  const colorWithAlpha = (rgb, value, max) => {
    const alpha = value > 0 ? Math.max(0.24, Math.min(0.95, 0.18 + Math.sqrt(value / max) * 0.77)) : 0.16;
    return `rgba(${rgb}, ${alpha})`;
  };

  rows.forEach((row, y) => {
    (row.rewardCells || []).forEach((cell, x) => {
      const reward = cell.rewardedGonka || 0;
      const missing = !cell.hasData;
      heatmapRows.push({
        value: [x, y, reward],
        address: row.address,
        row,
        cell,
        phase: missing ? "missing_history" : "previous_reward",
        itemStyle: { color: missing ? "rgba(56, 64, 74, 0.14)" : reward > 0 ? colorWithAlpha("215, 168, 79", reward, maxReward) : "rgba(56, 64, 74, 0.32)" },
      });
    });
    (row.compensationCells || []).forEach((cell, index) => {
      const x = historyEpochs.length + index;
      const compensation = cell.compensationGonka || 0;
      const reward = cell.rewardedGonka || 0;
      const phase = cell.epoch <= 266 ? "attack_or_excluded" : "cap_compensation";
      const color = compensation > 0
        ? colorWithAlpha("121, 182, 106", compensation, maxCompensation)
        : reward > 0
          ? colorWithAlpha("215, 168, 79", reward, maxReward)
          : phase === "attack_or_excluded"
            ? "rgba(217, 101, 95, 0.26)"
            : "rgba(56, 64, 74, 0.28)";
      heatmapRows.push({
        value: [x, y, compensation || reward],
        address: row.address,
        row,
        cell,
        phase,
        itemStyle: { color },
      });
    });
  });

  const historyLabel = historyEpochs.length ? `e${historyEpochs[0]}–e${historyEpochs[historyEpochs.length - 1]}` : "n/a";
  const compensationLabel = compensationEpochs.length ? `e${compensationEpochs[0]}–e${compensationEpochs[compensationEpochs.length - 1]}` : "n/a";
  document.getElementById("recipientCompByWindowEpochs").textContent = `Rewards ${historyLabel} · compensation ${compensationLabel}`;
  document.getElementById("recipientCompByWindowRows").textContent = `${rows.length} shown`;
  state.chartAddressRows.recipientCompByWindow = heatmapRows;

  const chartEl = document.getElementById("recipientCompByWindowChart");
  if (chartEl) chartEl.style.height = `${Math.max(560, rows.length * 27 + 120)}px`;
  if (!rows.length || !xLabels.length) {
    state.charts.recipientCompByWindow.setOption({
      title: { text: "No reward history rows for current filters", left: "center", textStyle: { color: "#6d7682" } },
      xAxis: { show: false },
      yAxis: { show: false },
      series: [],
    }, true);
  } else {
    state.charts.recipientCompByWindow.resize();
    state.charts.recipientCompByWindow.setOption({
      tooltip: chartTooltip({
        formatter: (item) => {
          const data = item.data || {};
          const row = data.row || {};
          const cell = data.cell || {};
          const compensation = cell.compensationGonka || 0;
          const reward = cell.rewardedGonka || 0;
          const phase = {
            previous_reward: "previous reward history",
            missing_history: "reward history not fetched",
            attack_or_excluded: "attack / excluded epoch",
            cap_compensation: "cap compensation epoch",
          }[data.phase] || data.phase;
          const dataLine = data.phase === "missing_history" ? "<br>source data missing for this epoch/address" : "";
          return `<strong>${escapeHtml(row.actorDisplayLabel || row.actorShortLabel || row.address)}</strong><br>${escapeHtml(row.address || "")}<br>epoch e${cell.epoch}<br>${escapeHtml(phase)}${dataLine}<br>reward ${gonka(reward)}<br>compensation ${gonka(compensation)}<br>claimed ${cell.claimed ? "yes" : "no"}<br>inferences ${fmt.format(cell.inferenceCount || 0)}<br>max observed weight ${fmt.format(row.maxObservedWeight || 0)}<br>previous 10 rewards ${gonka(row.previousRewardGonka || 0)}<br>total received ${gonka(row.totalReceivedGonka || 0)}`;
        },
      }),
      grid: { left: 250, right: 28, top: 72, bottom: 48 },
      xAxis: {
        type: "category",
        data: xLabels,
        axisLabel: {
          color: (value) => value.includes("attack") || value.includes("excluded") ? "#d9655f" : value.includes("cap") ? "#79b66a" : "#d7a84f",
          interval: 0,
          rotate: 32,
        },
        splitLine: { show: true, lineStyle: { color: "rgba(128, 140, 154, 0.22)" } },
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: rows.map((row) => `${row.actorShortLabel || row.actorDisplayLabel || shortAddress(row.address)}  ${shortAddress(row.address)}`),
        axisLabel: { align: "left", margin: 244, color: "#a7afba", width: 236, overflow: "truncate" },
      },
      series: [{
        type: "heatmap",
        data: heatmapRows,
        label: {
          show: true,
          color: "#f4f0e8",
          formatter: (item) => {
            const cell = item.data?.cell || {};
            const compensation = cell.compensationGonka || 0;
            const reward = cell.rewardedGonka || 0;
            if (compensation > maxCompensation * 0.025) return compact.format(compensation);
            if (reward > maxReward * 0.06) return compact.format(reward);
            return "";
          },
        },
        itemStyle: { borderColor: "#101114", borderWidth: 1 },
        emphasis: { itemStyle: { borderColor: "#f4f0e8", borderWidth: 1.5 } },
      }],
      graphic: [{
        type: "line",
        shape: { x1: 250 + (historyEpochs.length / Math.max(xLabels.length, 1)) * (state.charts.recipientCompByWindow.getWidth() - 278), y1: 56, x2: 250 + (historyEpochs.length / Math.max(xLabels.length, 1)) * (state.charts.recipientCompByWindow.getWidth() - 278), y2: state.charts.recipientCompByWindow.getHeight() - 48 },
        style: { stroke: "rgba(244, 240, 232, 0.45)", lineWidth: 2, lineDash: [5, 5] },
        silent: true,
      }],
    }, true);
  }

  els.recipientCompByWindowTable.innerHTML = rows.map((row) => {
    const weightPct = Math.max(3, Math.min(100, ((row.maxObservedWeight || 0) / maxWeight) * 100));
    const ratio = row.compensationToPreviousRewardRatio == null ? "n/a" : `${fmt.format(row.compensationToPreviousRewardRatio)}x`;
    return `
      <tr>
        <td><button class="row-button mono" data-address="${escapeHtml(row.address)}">${escapeHtml(row.actorDisplayLabel || row.actorShortLabel || row.address)}</button><div class="muted">${shortAddress(row.address)}</div><div class="weight-rail" title="Max observed weight ${fmt.format(row.maxObservedWeight || 0)}"><span style="width:${weightPct}%"></span></div></td>
        <td class="num">${fmt.format(row.maxObservedWeight || 0)}</td>
        <td class="num">${gonka(row.previousRewardGonka || 0)}</td>
        <td class="num">${gonka(row.compensationPeriodRewardGonka || 0)}</td>
        <td class="num">${gonka(row.compensationGonka || 0)}</td>
        <td class="num">${gonka(row.totalReceivedGonka || 0)}</td>
        <td class="num">${ratio}</td>
      </tr>
    `;
  }).join("");
}

function renderMatrix() {
  const rows = state.data.chartData?.voteMatrixPower || [];
  const byKey = new Map(rows.map((row) => [`${row.recipientStatus}:${row.voteOption}`, row]));
  const emptyRow = { addressCount: 0, totalCompensationGonka: 0, votingPower: 0 };
  const getRow = (recipientStatus, voteOption) => byKey.get(`${recipientStatus}:${voteOption}`) || emptyRow;
  const rewardFlows = [
    { voteOption: "yes", source: "Yes", target: "Received reward", color: optionColors.yes, row: getRow("recipient", "yes") },
    { voteOption: "no_with_veto", source: "No with veto", target: "Received reward", color: optionColors.no_with_veto, row: getRow("recipient", "no_with_veto") },
    { voteOption: "did_not_vote", source: "Did not vote", target: "Received reward", color: optionColors.did_not_vote, row: getRow("recipient", "did_not_vote") },
  ];
  const powerFlows = [
    { voteOption: "yes", source: "Received reward", target: "Yes", color: optionColors.yes, row: getRow("recipient", "yes") },
    { voteOption: "no_with_veto", source: "Received reward", target: "No with veto", color: optionColors.no_with_veto, row: getRow("recipient", "no_with_veto") },
    { voteOption: "yes", source: "No reward", target: "Yes", color: optionColors.yes, row: getRow("non_recipient", "yes") },
    { voteOption: "no_with_veto", source: "No reward", target: "No with veto", color: optionColors.no_with_veto, row: getRow("non_recipient", "no_with_veto") },
  ];
  state.charts.matrix.setOption({
    title: { text: "Reward amount", left: 8, top: 2, textStyle: { color: "#a7afba", fontSize: 12, fontWeight: 600 } },
    tooltip: chartTooltip({
      trigger: "item",
      formatter: (item) => {
        const row = item.data?.row || {};
        if (item.dataType === "edge") {
          return `<strong>${escapeHtml(item.data.source)} -> ${escapeHtml(item.data.target)}</strong><br>${gonka(item.data.value || 0)} reward amount<br>${fmt.format(row.addressCount || 0)} addresses<br>${fmt.format(row.votingPower || 0)} governance voting power`;
        }
        return `<strong>${escapeHtml(item.name)}</strong><br>Flow width = received GONKA`;
      },
    }),
    series: [{
      type: "sankey",
      left: 8,
      right: 18,
      top: 24,
      bottom: 24,
      nodeWidth: 16,
      nodeGap: 16,
      draggable: false,
      emphasis: { focus: "adjacency" },
      label: { color: "#eef0f2", fontSize: 12 },
      itemStyle: { borderColor: "#101114", borderWidth: 1 },
      lineStyle: { color: "source", opacity: 0.5, curveness: 0.45 },
      data: [
        { name: "Yes", itemStyle: { color: optionColors.yes } },
        { name: "No with veto", itemStyle: { color: optionColors.no_with_veto } },
        { name: "Did not vote", itemStyle: { color: optionColors.did_not_vote } },
        { name: "Received reward", itemStyle: { color: "#d7a84f" } },
      ],
      links: rewardFlows
        .filter((flow) => (flow.row.totalCompensationGonka || 0) > 0)
        .map((flow) => ({
          source: flow.source,
          target: flow.target,
          value: flow.row.totalCompensationGonka || 0,
          row: flow.row,
        })),
    }],
  }, true);
  state.charts.matrixStats.setOption({
    title: { text: "Governance voting power", right: 8, top: 2, textStyle: { color: "#a7afba", fontSize: 12, fontWeight: 600 } },
    tooltip: chartTooltip({
      trigger: "item",
      formatter: (item) => {
        const row = item.data?.row || {};
        if (item.dataType === "edge") {
          return `<strong>${escapeHtml(item.data.source)} -> ${escapeHtml(item.data.target)}</strong><br>${fmt.format(item.data.value || 0)} governance voting power<br>${fmt.format(row.addressCount || 0)} addresses<br>${gonka(row.totalCompensationGonka || 0)} reward amount`;
        }
        return `<strong>${escapeHtml(item.name)}</strong><br>Flow width = governance voting power`;
      },
    }),
    series: [{
      type: "sankey",
      left: 18,
      right: 8,
      top: 24,
      bottom: 24,
      nodeWidth: 16,
      nodeGap: 16,
      draggable: false,
      emphasis: { focus: "adjacency" },
      label: { color: "#eef0f2", fontSize: 12 },
      itemStyle: { borderColor: "#101114", borderWidth: 1 },
      lineStyle: { color: "target", opacity: 0.5, curveness: 0.45 },
      data: [
        { name: "Received reward", itemStyle: { color: "#d7a84f" } },
        { name: "No reward", itemStyle: { color: "#6d7682" } },
        { name: "Yes", itemStyle: { color: optionColors.yes } },
        { name: "No with veto", itemStyle: { color: optionColors.no_with_veto } },
      ],
      links: powerFlows
        .filter((flow) => (flow.row.votingPower || 0) > 0)
        .map((flow) => ({
          source: flow.source,
          target: flow.target,
          value: flow.row.votingPower || 0,
          row: flow.row,
        })),
    }],
  }, true);
}

function renderTimeline() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const votes = state.data.votes
    .filter((vote) => {
      if (selectedLabel !== "all" && vote.label !== selectedLabel) return false;
      if (!voteMatches(vote, els.vote.value)) return false;
      if (!query) return true;
      return textMatch({ ...vote, address: vote.voter }, query);
    })
    .sort((a, b) => a.height - b.height || actorLabel(a).localeCompare(actorLabel(b)));
  const values = votes.map((vote, i) => [Date.parse(vote.blockTime || ""), i, vote.height]);
  const maxPower = Math.max(...votes.map((vote) => vote.votingPower || 0), 0);
  state.chartAddressRows.timeline = votes;
  state.charts.timeline.setOption({
    grid: { left: 150, right: 42, top: 20, bottom: 42 },
    tooltip: chartTooltip({
      formatter: (p) => {
        const vote = votes[p.dataIndex];
        return `<strong>${escapeHtml(actorLabel(vote))}</strong><br>${escapeHtml(vote.voter)}<br>${escapeHtml(voteDisplayText(vote))}<br>${escapeHtml(formatTime(vote.blockTime))}<br>height ${vote.height}<br>governance power ${vote.votingPower == null ? "unknown" : fmt.format(vote.votingPower)}`;
      },
    }),
    xAxis: {
      type: "time",
      axisLabel: { color: "#a7afba", formatter: (value) => formatTime(value).slice(5, 16) },
      name: "Vote block time",
      nameTextStyle: { color: "#a7afba" },
    },
    yAxis: { type: "category", data: votes.map(actorShortLabel), axisLabel: { color: "#a7afba", width: 140, overflow: "truncate" } },
    series: [{
      type: "scatter",
      symbolSize: (value, params) => voteSymbolSize(votes[params.dataIndex], maxPower),
      data: values,
      itemStyle: { color: (p) => optionColors[votes[p.dataIndex].primaryOption] },
      label: {
        show: votes.length <= 8,
        formatter: (p) => String(actorShortLabel(votes[p.dataIndex]) || "").slice(0, 34),
        position: "right",
        color: "#eef0f2",
      },
    }],
  }, true);
}

function renderTally() {
  const rows = state.data.chartData?.tallyByOption || Object.entries(state.data.summary.finalTally).map(([voteOption, votingPower]) => ({ voteOption, votingPower, addressCount: 0 }));
  state.charts.tally.setOption({
    grid: { left: 68, right: 18, top: 18, bottom: 42 },
    tooltip: chartTooltip({ formatter: (p) => {
      const row = rows[p.dataIndex];
      return `${voteOptionLabel(row.voteOption)}<br>${fmt.format(row.votingPower)} voting power<br>${row.addressCount} final voters<br>${fmt.format(row.recipientVotingPower || 0)} recipient-voter power`;
    } }),
    xAxis: { type: "category", data: rows.map((row) => voteOptionLabel(row.voteOption)), axisLabel: { color: "#a7afba", interval: 0, rotate: 15 } },
    yAxis: { type: "value", axisLabel: { color: "#a7afba", formatter: (value) => compact.format(value) } },
    series: [{
      type: "bar",
      data: rows.map((row) => row.votingPower),
      itemStyle: { color: (p) => optionColors[rows[p.dataIndex]?.voteOption] || "#4db7a8" },
      label: { show: true, position: "top", color: "#eef0f2", formatter: (p) => compact.format(p.value) },
    }],
  }, true);
}

function voterDisplayLabel(row) {
  return actorShortLabel(row);
}

function voterAxisLabel(row) {
  const address = row.address || row.voter || "";
  return `${shortAddress(address)}  ${actorShortLabel(row)}`;
}

function renderVoterPowerChart() {
  const rows = (state.data.benefitPowerMatrix || [])
    .filter((row) => row.isVoter)
    .sort((a, b) => (b.votingPower || 0) - (a.votingPower || 0) || actorLabel(a).localeCompare(actorLabel(b)));
  state.chartAddressRows.voterPower = rows;
  state.charts.voterPower.setOption({
    grid: { left: 282, right: 44, top: 24, bottom: 42 },
    tooltip: chartTooltip({
      formatter: (p) => {
        const row = rows[p.dataIndex];
        const roles = [
          row.isRecipient ? "recipient" : "",
          row.isVoter ? "voter" : "",
        ].filter(Boolean).join(" + ");
        return `<strong>${escapeHtml(actorLabel(row))}</strong><br>${escapeHtml(row.address)}<br>${escapeHtml(roles)}<br>vote ${escapeHtml(voteDisplayText(row))}<br>governance power ${fmt.format(row.votingPower || 0)}<br>compensation ${gonka(row.totalCompensationGonka || 0)}<br>${escapeHtml(identityBoundary(row))}`;
      },
    }),
    xAxis: { type: "value", axisLabel: { color: "#a7afba" }, name: "Archive governance voting power", nameTextStyle: { color: "#a7afba" } },
    yAxis: { type: "category", data: rows.map(voterAxisLabel), axisLabel: { align: "left", margin: 274, color: "#a7afba", width: 260, overflow: "truncate" } },
    series: [{
      type: "bar",
      data: rows.map((row) => row.votingPower || 0),
      itemStyle: { color: (p) => optionColors[rows[p.dataIndex]?.voteOption] || "#4db7a8" },
      label: { show: true, position: "right", color: "#eef0f2", formatter: (p) => fmt.format(p.value) },
    }],
  }, true);
  els.voterPowerTable.innerHTML = rows.map((row) => `
    <tr>
      <td>${escapeHtml(voterDisplayLabel(row))}<br><span class="muted">${escapeHtml(actorLabel(row))}</span></td>
      <td><button class="row-button mono" data-address="${row.address}">${escapeHtml(row.address)}</button></td>
      <td>${voteDisplayHtml(row)}</td>
      <td class="num">${fmt.format(row.votingPower || 0)}</td>
      <td><span class="tag ${identityBoundary(row) === "public_owner_proof" ? "good" : ""}">${escapeHtml(identityBoundary(row))}</span><br><span class="muted">proof ${row.proofCount}; high ${row.highConfidenceClaimCount}</span></td>
    </tr>
  `).join("");
}

function windowStatusLabel(status) {
  return {
    zero_at_start_and_end: "Zero at start and end",
    power_at_start_only: "Power at start only",
    power_at_end_only: "Power at end only",
    power_at_start_and_end: "Power at start and end",
    unchanged: "Stable",
    changed: "Changed",
  }[status] || status || "Unknown";
}

function renderWindowPowerChart() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const votingEpochWeights = state.data.votingWindowEpochWeights?.rows || {};
  const epochWeight = (address, epoch) => votingEpochWeights[address]?.[`e${epoch}`] || 0;
  const e285Weight = (address) => epochWeight(address, 285);
  const e286Weight = (address) => epochWeight(address, 286);
  const e287Weight = (address) => epochWeight(address, 287);
  const rows = ((state.data.votingPowerWindow || {}).rows || [])
    .filter((row) => {
      if (selectedLabel !== "all" && row.label !== selectedLabel) return false;
      if (!voteMatches(row, els.vote.value)) return false;
      if (!query) return true;
      return textMatch({ ...row, address: row.voter, status: row.windowPowerStatus }, query);
    })
    .sort((a, b) => Date.parse(a.blockTime || "") - Date.parse(b.blockTime || "") || a.height - b.height || actorLabel(a).localeCompare(actorLabel(b)));
  document.getElementById("windowPowerRows").textContent = `${rows.length} shown`;
  state.chartAddressRows.windowPower = rows;
  const maxPower = Math.max(
    1,
    ...rows.flatMap((row) => [row.startVotingPower || 0, row.endVotingPower || 0, e285Weight(row.voter), e286Weight(row.voter), e287Weight(row.voter)]),
  );
  const markerSize = (value) => Math.max(7, Math.min(26, 6 + Math.sqrt((value?.[2] || 0) / maxPower) * 22));
  const votePoint = (row, index, value) => [Date.parse(row.blockTime || "") || row.height, index, value || 0];
  const formatPointTooltip = (p, label, value) => {
    const row = p.data?.row || rows[p.dataIndex] || {};
    const e285 = e285Weight(row.voter);
    const e286 = e286Weight(row.voter);
    const e287 = e287Weight(row.voter);
    return `<strong>${escapeHtml(actorLabel(row))}</strong><br>${escapeHtml(row.voter || "")}<br>vote ${escapeHtml(voteDisplayText(row))}<br>${escapeHtml(formatTime(row.blockTime || ""))}<br>height ${fmt.format(row.height || 0)}<br>${label} ${fmt.format(value || 0)}<br>start gov power ${fmt.format(row.startVotingPower || 0)}<br>end gov power ${fmt.format(row.endVotingPower || 0)}<br>e285 inference weight ${fmt.format(e285)}<br>e286 inference weight ${fmt.format(e286)}<br>e287 inference weight ${fmt.format(e287)}<br>e287 - e285 ${fmt.format(e287 - e285)}<br>${escapeHtml(windowStatusLabel(row.windowPowerStatus))}`;
  };
  state.charts.windowPower.setOption({
    grid: { left: 282, right: 44, top: 34, bottom: 52 },
    legend: { top: 4, data: ["E285 weight", "E286 weight", "E287 weight", "Start gov power", "End gov power"], textStyle: { color: "#a7afba" } },
    tooltip: chartTooltip({
      formatter: (p) => {
        const value = Array.isArray(p.value) ? p.value[2] : 0;
        return formatPointTooltip(p, p.seriesName, value);
      },
    }),
    xAxis: {
      type: "time",
      axisLabel: { color: "#a7afba", formatter: (value) => formatTime(value).slice(5, 16) },
      name: "Vote block time",
      nameTextStyle: { color: "#a7afba" },
    },
    yAxis: { type: "category", data: rows.map(voterAxisLabel), axisLabel: { align: "left", margin: 274, color: "#a7afba", width: 260, overflow: "truncate" } },
    series: [
      {
        name: "E285 weight",
        type: "scatter",
        data: rows.map((row, index) => ({ value: votePoint(row, index, e285Weight(row.voter)), row })),
        symbol: "rect",
        symbolSize: markerSize,
        symbolOffset: [-32, 0],
        itemStyle: { color: "#d7a84f", borderColor: "#101114", borderWidth: 1 },
      },
      {
        name: "E286 weight",
        type: "scatter",
        data: rows.map((row, index) => ({ value: votePoint(row, index, e286Weight(row.voter)), row })),
        symbol: "rect",
        symbolSize: markerSize,
        symbolOffset: [-16, 0],
        itemStyle: { color: "#e78f61", borderColor: "#101114", borderWidth: 1 },
      },
      {
        name: "E287 weight",
        type: "scatter",
        data: rows.map((row, index) => ({ value: votePoint(row, index, e287Weight(row.voter)), row })),
        symbol: "rect",
        symbolSize: markerSize,
        itemStyle: { color: "#d9655f", borderColor: "#101114", borderWidth: 1 },
      },
      {
        name: "Start gov power",
        type: "scatter",
        data: rows.map((row, index) => ({ value: votePoint(row, index, row.startVotingPower || 0), row })),
        symbol: "circle",
        symbolSize: markerSize,
        symbolOffset: [16, 0],
        itemStyle: { color: "#5da9e9", borderColor: "#101114", borderWidth: 1 },
      },
      {
        name: "End gov power",
        type: "scatter",
        data: rows.map((row, index) => ({ value: votePoint(row, index, row.endVotingPower || 0), row })),
        symbol: "diamond",
        symbolSize: markerSize,
        symbolOffset: [32, 0],
        itemStyle: { color: (p) => optionColors[rows[p.dataIndex]?.primaryOption] || "#4db7a8", borderColor: "#eef0f2", borderWidth: 1 },
        label: {
          show: rows.length <= 26,
          position: "right",
          color: "#eef0f2",
          formatter: (p) => compact.format(p.value[2] || 0),
        },
      },
    ],
  }, true);
  els.windowPowerTable.innerHTML = rows.map((row) => `
    <tr>
      <td>${escapeHtml(voterDisplayLabel(row))}<br><button class="row-button mono" data-address="${row.voter}">${escapeHtml(row.voter)}</button></td>
      <td>${voteDisplayHtml(row)}<br><span class="muted">${escapeHtml(formatTime(row.blockTime || ""))}</span><br><span class="muted">tx height ${fmt.format(row.height || 0)}</span></td>
      <td class="num">${fmt.format(e285Weight(row.voter))}</td>
      <td class="num">${fmt.format(e286Weight(row.voter))}</td>
      <td class="num">${fmt.format(e287Weight(row.voter))}<br><span class="muted">delta ${fmt.format(e287Weight(row.voter) - e285Weight(row.voter))}</span></td>
      <td class="num">${fmt.format(row.startVotingPower || 0)}<br><span class="muted">${escapeHtml(row.startVotingPowerSource || "")}</span></td>
      <td class="num">${fmt.format(row.endVotingPower || 0)}<br><span class="muted">${escapeHtml(row.endVotingPowerSource || "")}</span></td>
      <td><span class="tag ${row.windowPowerStatus === "zero_at_start_and_end" ? "" : "warn"}">${escapeHtml(windowStatusLabel(row.windowPowerStatus))}</span><br><span class="muted">delegations ${fmt.format(row.startDelegationCount || 0)} -> ${fmt.format(row.endDelegationCount || 0)}</span></td>
    </tr>
  `).join("");
}

function renderAttackTimeline() {
  const timeline = state.data.chartData?.participantEpochTimeline;
  if (!timeline) return;
  const query = els.search.value.trim().toLowerCase();
  const filtered = new Set(state.filteredRecipients.map((row) => row.address));
  const hasModelActivity = (row, model) => row.cells.some((cell) => model === "qwen" ? cell.qwenCount > 0 : cell.kimiCount > 0);
  const maxRowWeight = (row) => Math.max(0, ...row.cells.map((cell) => cell.weight || cell.startWeight || cell.confirmationWeight || 0));
  const rows = timeline.rows.filter((row) => {
    if (state.timelineScope === "recipients" && !filtered.has(row.address)) return false;
    if (!voteMatches(row, els.vote.value)) return false;
    if (state.timelineModel === "qwen" && !hasModelActivity(row, "qwen")) return false;
    if (state.timelineModel === "kimi" && !hasModelActivity(row, "kimi")) return false;
    if (!query) return true;
    return textMatch(row, query);
  }).sort((a, b) => {
    if (state.timelineSort !== "maxWeight") return 0;
    return maxRowWeight(b) - maxRowWeight(a) || (b.totalCompensationGonka || 0) - (a.totalCompensationGonka || 0) || actorLabel(a).localeCompare(actorLabel(b));
  });
  const columns = timeline.columns || [];
  const weightRailRows = rows.map((row, index) => ({ value: [maxRowWeight(row), index], row }));
  const maxRailWeight = Math.max(1, ...weightRailRows.map((item) => item.value[0]));
  const weightBar = (weight) => {
    const filled = Math.max(0, Math.min(10, Math.round((weight / maxRailWeight) * 10)));
    return `${"=".repeat(filled)}${"-".repeat(10 - filled)}`;
  };
  const yLabels = rows.map((row) => {
    const weight = maxRowWeight(row);
    return `${row.rank ? `#${row.rank}` : "not paid"} ${actorShortLabel(row)}\nmax weight ${compact.format(weight)} [${weightBar(weight)}]`;
  });
  const visibleRows = Math.max(0, Math.min(rows.length - 1, 27));
  const maxMetric = Math.max(
    1,
    ...rows.flatMap((row) => row.cells.map((cell) => state.timelineMetric === "reward" ? (cell.rewardGonka || 0) : (cell.weight || 0))),
  );
  const metricValue = (cell) => state.timelineMetric === "reward" ? (cell.rewardGonka || 0) : (cell.weight || 0);
  const cellColor = (cell) => {
    if (cell.columnType === "cpoc") {
      if (cell.state === "snapshot_missing") return "rgba(58, 63, 71, 0.72)";
      if (cell.state === "confirmed") return "rgba(121, 182, 106, 0.82)";
      if (cell.state === "cpoc_degraded") return "rgba(215, 168, 79, 0.84)";
      if (cell.state === "cpoc_failed") return "rgba(217, 101, 95, 0.9)";
      return "rgba(34, 40, 49, 0.78)";
    }
    const strength = Math.sqrt(metricValue(cell) / maxMetric);
    const alpha = Math.max(0.2, Math.min(0.92, 0.22 + strength * 0.7));
    if (cell.state === "dropped") return "rgba(217, 101, 95, 0.86)";
    if (cell.state === "missing_after_active") return "rgba(217, 101, 95, 0.28)";
    if (cell.state === "returned") return `rgba(215, 168, 79, ${alpha})`;
    if (cell.state === "active") return `rgba(77, 183, 168, ${alpha})`;
    return "rgba(34, 40, 49, 0.78)";
  };
  const heatmapData = rows.flatMap((row, y) => row.cells.map((cell, x) => ({
    value: [x, y, metricValue(cell)],
    row,
    cell,
    itemStyle: {
      color: cellColor(cell),
      borderColor: cell.columnType === "weight" && cell.rewardWithoutWeight ? "#d7a84f" : "#101114",
      borderWidth: cell.columnType === "weight" && cell.rewardWithoutWeight ? 2 : 1,
    },
  })));
  const markerData = (model) => rows.flatMap((row, y) => row.cells.map((cell, x) => {
    const count = model === "qwen" ? cell.qwenCount : cell.kimiCount;
    if (!count) return null;
    return { value: [x, y, count], row, cell, model };
  }).filter(Boolean));
  const rewardMarkerData = rows.flatMap((row, y) => row.cells.map((cell, x) => {
    if (cell.columnType !== "weight" || !cell.rewardWithoutWeight) return null;
    return { value: [x, y, cell.rewardGonka || 0], row, cell };
  }).filter(Boolean));
  const epochBoundaries = columns
    .map((column, index) => columns[index + 1] && columns[index + 1].epoch !== column.epoch ? [index, 0] : null)
    .filter(Boolean);
  const epochBands = [];
  const epochRanges = new Map();
  columns.forEach((column, index) => {
    if (index > 0 && columns[index - 1].epoch === column.epoch) return;
    let endIndex = index;
    while (columns[endIndex + 1] && columns[endIndex + 1].epoch === column.epoch) endIndex += 1;
    epochRanges.set(column.epoch, { start: index, end: endIndex });
    if (epochBands.length % 2 === 1) epochBands.push([index, endIndex]);
    else epochBands.push(null);
  });
  const visibleEpochBands = epochBands.filter(Boolean);
  const compensationData = rows.flatMap((row, y) => {
    const seen = new Set();
    return row.cells.map((cell) => {
      if (seen.has(cell.epoch) || !(cell.rewardGonka > 0)) return null;
      seen.add(cell.epoch);
      const range = epochRanges.get(cell.epoch);
      if (!range) return null;
      return { value: [range.start, range.end, y, cell.rewardGonka], row, cell };
    }).filter(Boolean);
  });
  const showQwen = state.timelineModel === "all" || state.timelineModel === "qwen";
  const showKimi = state.timelineModel === "all" || state.timelineModel === "kimi";
  state.charts.attackTimeline.setOption({
    legend: { top: 4, data: ["epoch weight/reward state", "Compensated epoch", "Reward while inactive", "Qwen commits", "Kimi commits"], textStyle: { color: "#a7afba" } },
    grid: { left: 340, right: 28, top: 44, bottom: 54 },
    tooltip: chartTooltip({
      formatter: (p) => {
        const row = p.data?.row || {};
        const cell = p.data?.cell || {};
        const modelText = p.data?.model ? `<br>${p.data.model.toUpperCase()} commits ${fmt.format(p.value[2] || 0)}` : "";
        const compensationText = row.compensationStatus === "not_compensated" ? "<br><span class=\"warn-text\">not compensated</span>" : "";
        const heightText = cell.height ? `<br>height ${fmt.format(cell.height)}` : "";
        const blockTimeText = cell.blockTime ? `<br>${escapeHtml(cell.blockTime)}` : "";
        const fallbackText = cell.fallback ? "<br><span class=\"warn-text\">snapshot missing, CPoC event only</span>" : "";
        const deltaText = cell.cpocDeltaConfirmation !== null && cell.cpocDeltaConfirmation !== undefined
          ? `<br>confirmation delta ${fmt.format(cell.cpocDeltaConfirmation)}`
          : "";
        const rewardFlag = cell.rewardWithoutWeight
          ? "<br><span class=\"warn-text\">reward paid while epoch start weight is zero</span>"
          : cell.rewardWithoutConfirmation
            ? "<br><span class=\"warn-text\">reward paid while CPoC confirmation is zero</span>"
            : "";
        return `<strong>${escapeHtml(actorLabel(row))}</strong><br>${escapeHtml(row.address || "")}${compensationText}<br>max observed weight ${fmt.format(maxRowWeight(row))}<br>epoch ${escapeHtml(cell.epoch || "")} · ${escapeHtml(cell.snapshot || "")} · ${escapeHtml(cell.state || "")}${heightText}${blockTimeText}${fallbackText}<br>weight ${fmt.format(cell.weight || 0)}<br>start weight ${fmt.format(cell.startWeight || 0)}<br>confirmation weight ${fmt.format(cell.confirmationWeight || 0)}${deltaText}<br>confirmation ratio ${fmt.format((cell.confirmationRatio || 0) * 100)}%<br>reward ${gonka(cell.rewardGonka || 0)}${rewardFlag}<br>Qwen commits ${fmt.format(cell.qwenCount || 0)} · Kimi commits ${fmt.format(cell.kimiCount || 0)}${modelText}<br>vote ${escapeHtml(voteDisplayText(row))} · gov power ${fmt.format(row.governanceVotingPower || 0)}`;
      },
    }),
    xAxis: { type: "category", data: columns.map((column) => column.label), axisLabel: { color: "#a7afba", interval: 0, rotate: 28 } },
    yAxis: {
      type: "category",
      inverse: true,
      data: yLabels,
      axisLabel: {
        align: "left",
        margin: 330,
        width: 315,
        overflow: "truncate",
        lineHeight: 14,
        formatter: (value) => {
          const [name, meta = ""] = String(value).split("\n");
          return `{timelineName|${escapeRichText(name)}}\n{timelineMeta|${escapeRichText(meta)}}`;
        },
        rich: {
          timelineName: { width: 315, align: "left", color: "#e8edf2", fontWeight: 600, overflow: "truncate", lineHeight: 16 },
          timelineMeta: { width: 315, align: "left", color: "#7f8a96", overflow: "truncate", lineHeight: 14 },
        },
      },
    },
    dataZoom: [
      { type: "inside", yAxisIndex: 0, filterMode: "none", startValue: 0, endValue: visibleRows },
      { type: "slider", yAxisIndex: 0, right: 4, width: 14, filterMode: "none", startValue: 0, endValue: visibleRows, textStyle: { color: "#a7afba" } },
    ],
    series: [
      {
        name: "epoch band",
        type: "custom",
        silent: true,
        tooltip: { show: false },
        data: visibleEpochBands,
        renderItem: (params, api) => {
          const start = api.coord([api.value(0), 0]);
          const end = api.coord([api.value(1), 0]);
          const cellWidth = api.size([1, 0])[0];
          return {
            type: "rect",
            shape: {
              x: start[0] - cellWidth / 2,
              y: params.coordSys.y,
              width: end[0] - start[0] + cellWidth,
              height: params.coordSys.height,
            },
            style: { fill: "rgba(255, 255, 255, 0.025)" },
          };
        },
      },
      {
        name: "epoch weight/reward state",
        type: "heatmap",
        data: heatmapData,
        label: { show: false },
      },
      {
        name: "Compensated epoch",
        type: "custom",
        data: compensationData,
        tooltip: { show: true },
        renderItem: (params, api) => {
          const start = api.coord([api.value(0), api.value(2)]);
          const end = api.coord([api.value(1), api.value(2)]);
          const cellWidth = api.size([1, 0])[0];
          const cellHeight = api.size([0, 1])[1];
          const barHeight = Math.max(3, Math.min(7, cellHeight * 0.18));
          return {
            type: "rect",
            shape: {
              x: start[0] - cellWidth / 2 + 2,
              y: start[1] + cellHeight * 0.28,
              width: end[0] - start[0] + cellWidth - 4,
              height: barHeight,
            },
            style: {
              fill: "#d7a84f",
              opacity: Math.max(0.55, Math.min(0.95, 0.52 + Math.sqrt(api.value(3) || 0) / 280)),
            },
          };
        },
      },
      {
        name: "Reward while inactive",
        type: "scatter",
        symbol: "pin",
        symbolSize: (value) => Math.max(12, Math.min(24, 10 + Math.sqrt(value[2] || 0) / 8)),
        symbolOffset: [0, -4],
        data: rewardMarkerData,
        itemStyle: { color: "#d7a84f", borderColor: "#101114", borderWidth: 1 },
      },
      {
        name: "epoch separator",
        type: "custom",
        silent: true,
        tooltip: { show: false },
        data: epochBoundaries,
        renderItem: (params, api) => {
          const point = api.coord([api.value(0), 0]);
          const cellWidth = api.size([1, 0])[0];
          const x = point[0] + cellWidth / 2;
          return {
            type: "line",
            shape: { x1: x, y1: params.coordSys.y, x2: x, y2: params.coordSys.y + params.coordSys.height },
            style: { stroke: "#eef0f2", lineWidth: 1, opacity: 0.28 },
          };
        },
      },
      showQwen && {
        name: "Qwen commits",
        type: "scatter",
        symbol: "circle",
        symbolSize: (value) => Math.max(5, Math.min(18, 4 + Math.sqrt(value[2] || 0) / 70)),
        symbolOffset: showKimi ? [-7, 0] : [0, 0],
        data: markerData("qwen"),
        itemStyle: { color: "#5da9e9", borderColor: "#101114", borderWidth: 1 },
      },
      showKimi && {
        name: "Kimi commits",
        type: "scatter",
        symbol: "diamond",
        symbolSize: (value) => Math.max(5, Math.min(18, 4 + Math.sqrt(value[2] || 0) / 70)),
        symbolOffset: showQwen ? [7, 0] : [0, 0],
        data: markerData("kimi"),
        itemStyle: { color: "#8f7ad3", borderColor: "#101114", borderWidth: 1 },
      },
    ].filter(Boolean),
  }, true);
}

function renderHypotheses() {
  const query = els.search.value.trim().toLowerCase();
  const rows = (state.data.hypotheses || []).filter((row) => {
    if (!query) return true;
    return [row.id, row.title, row.status, row.summary, row.nextCheck].join(" ").toLowerCase().includes(query);
  });
  document.getElementById("hypothesisRows").textContent = `${rows.length} shown`;
  els.hypothesisTable.innerHTML = rows.map((row) => `
    <tr>
      <td><span class="tag ${row.status === "confirmed" ? "good" : row.status === "partially_supported" ? "warn" : ""}">${escapeHtml(row.status)}</span></td>
      <td>${escapeHtml(row.title)}<br><span class="mono muted">${escapeHtml(row.id)}</span></td>
      <td>${escapeHtml(row.summary)}</td>
      <td>${escapeHtml(row.nextCheck || "")}</td>
    </tr>
  `).join("");
}

function renderAnomalyTable() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const rows = (state.data.epochAnomalies || []).filter((row) => {
    if (selectedLabel !== "all" && row.label !== selectedLabel) return false;
    if (!voteMatches(row, els.vote.value)) return false;
    if (!query) return true;
    return [row.address, row.label, row.voteOption, row.status, row.caveat].join(" ").toLowerCase().includes(query);
  });
  document.getElementById("anomalyRows").textContent = `${rows.length} shown`;
  els.anomalyTable.innerHTML = rows.map((row) => `
    <tr>
      <td class="num">${fmt.format(row.anomalyScore)}</td>
      <td><button class="row-button mono" data-address="${row.address}">${escapeHtml(row.address)}</button></td>
      <td>${escapeHtml(actorLabel(row))}</td>
      <td class="num">${fmt.format(row.e287Weight)}</td>
      <td class="num">${fmt.format(row.prevMaxWeight)}</td>
      <td class="num">${fmt.format(row.nextMaxWeight)}</td>
      <td>${voteDisplayHtml(row)}${row.voteHeight ? `<br><span class="mono muted">${row.voteHeight}</span>` : ""}${row.voteBlockTime ? `<br><span class="muted">${escapeHtml(row.voteBlockTime)}</span>` : ""}</td>
      <td class="num">${fmt.format(row.governanceVotingPower || 0)}<br><span class="muted">${escapeHtml(row.governanceVotingPowerSource || "")}</span></td>
      <td><span class="tag ${row.status === "operational_enter_vote_exit_signal" ? "warn" : row.status === "partial_operational_timing_signal" ? "warn" : ""}">${escapeHtml(row.status)}</span><br><span class="muted">${escapeHtml(row.caveat || "")}</span></td>
    </tr>
  `).join("");
}

function entryExitClusterMatches(row, query) {
  if (els.label.value !== "all" && row.label !== els.label.value) return false;
  if (els.vote.value !== "all" && !Object.keys(row.voteCounts || {}).includes(els.vote.value)) return false;
  if (els.confidence.value !== "all" && !(row.topEvidence || []).some((item) => item.confidence === els.confidence.value)) return false;
  if (els.sourceType.value !== "all" && !(row.topEvidence || []).some((item) => item.sourceType === els.sourceType.value)) return false;
  if (!query) return true;
  return [
    row.id,
    row.kind,
    row.label,
    ...(row.addresses || []),
    ...(row.caveats || []),
    ...(row.addressRows || []).map((item) => [item.address, item.label, item.inferenceUrl, item.txHash, item.status].join(" ")),
    ...(row.topEvidence || []).map((item) => [item.sourceType, item.sourceValue, item.confidence].join(" ")),
  ].join(" ").toLowerCase().includes(query);
}

function renderEntryExitChart() {
  const query = els.search.value.trim().toLowerCase();
  const clusterRows = (state.data.epochEntryExitClusters || []).filter((row) => entryExitClusterMatches(row, query)).slice(0, 16);
  const rows = clusterRows.length
    ? clusterRows
    : (state.data.chartData?.timingLeads || []).filter((row) => entryExitClusterMatches({ ...row, addresses: [row.address], addressRows: [row] }, query)).slice(0, 16);
  const maxPower = Math.max(...rows.map((row) => row.governanceVotingPower || row.totalGovernanceVotingPower || 0), 0);
  state.chartAddressRows.entryExit = rows;
  state.charts.entryExit.setOption({
    grid: { left: 170, right: 24, top: 24, bottom: 42 },
    tooltip: chartTooltip({
      formatter: (params) => {
        const row = rows[params.dataIndex];
        if (clusterRows.length) {
          return `${escapeHtml(actorLabel(row))}<br>${escapeHtml(row.kind)}<br>e287 inference weight ${fmt.format(row.totalE287Weight)}<br>exact gov power ${fmt.format(row.totalGovernanceVotingPower || 0)}<br>${row.confirmedEnterVoteExitWithPowerCount || 0} full enter/vote/exit with power`;
        }
        return `${escapeHtml(actorLabel(row))}<br>prev ${fmt.format(row.prevMaxWeight || 0)} · e287 ${fmt.format(row.e287Weight || 0)} · next ${fmt.format(row.nextMaxWeight || 0)}<br>vote ${escapeHtml(voteDisplayText(row))}${row.voteHeight ? ` at ${row.voteHeight}` : ""}<br>exact gov power ${fmt.format(row.governanceVotingPower || 0)}<br>${escapeHtml(row.caveat || "")}`;
      },
    }),
    xAxis: { type: "value", axisLabel: { color: "#a7afba", formatter: (v) => compact.format(v) } },
    yAxis: { type: "category", data: rows.map((row, index) => `#${row.rank || index + 1} ${actorShortLabel(row)}`), axisLabel: { color: "#a7afba", width: 160, overflow: "truncate" } },
    series: clusterRows.length ? [{
      type: "bar",
      data: rows.map((row) => row.totalE287Weight),
      itemStyle: { color: (p) => rows[p.dataIndex]?.kind === "strict_identity" ? "#79b66a" : rows[p.dataIndex]?.kind === "signal_cluster" ? "#d7a84f" : "#4db7a8" },
    }] : [
      { name: "prev max", type: "scatter", data: rows.map((row, index) => [row.prevMaxWeight || 0, index]), symbolSize: 8, itemStyle: { color: "#6d7682" } },
      { name: "e287", type: "scatter", data: rows.map((row, index) => [row.e287Weight || 0, index]), symbolSize: (value, p) => voteSymbolSize({ votingPower: rows[p.dataIndex]?.governanceVotingPower || 0 }, maxPower), itemStyle: { color: (p) => optionColors[rows[p.dataIndex]?.voteOption] || "#4db7a8", borderColor: (p) => boundaryColor(rows[p.dataIndex]), borderWidth: 2 } },
      { name: "next max", type: "scatter", data: rows.map((row, index) => [row.nextMaxWeight || 0, index]), symbolSize: 8, itemStyle: { color: "#5da9e9" } },
    ],
  }, true);
}

function renderEntryExitTable() {
  const query = els.search.value.trim().toLowerCase();
  const rows = (state.data.epochEntryExitClusters || []).filter((row) => entryExitClusterMatches(row, query));
  document.getElementById("entryExitRows").textContent = `${rows.length} shown`;
  els.entryExitTable.innerHTML = rows.map((row) => {
    const voteText = Object.entries(row.voteCounts || {}).map(([option, count]) => `${optionLabels[option] || option}: ${count}`).join("<br>") || "-";
    const powerText = Object.entries(row.votePowerByOption || {}).map(([option, power]) => `${optionLabels[option] || option}: ${fmt.format(power)}`).join("<br>") || "-";
    const topEvidence = (row.topEvidence || []).slice(0, 3).map((item) => `${escapeHtml(item.sourceType)} <span class="tag ${item.isAttributionProof ? "good" : ""}">${item.isAttributionProof ? "proof" : "signal"}</span> <span class="tag">${escapeHtml(item.confidence)}</span>`).join("<br>");
    const addressRows = (row.addressRows || []).slice(0, 8).map((item) => {
      const flags = [
        item.enteredE287 ? "enter" : "",
        item.votedDuringE287 ? "vote" : "",
        item.exitedAfterE287 ? "exit" : "",
      ].filter(Boolean).join("/");
      return `<button class="row-button mono" data-address="${item.address}">${escapeHtml(item.address)}</button><br><span class="muted">${escapeHtml(flags || item.status)} e287 ${fmt.format(item.e287Weight)}</span>`;
    }).join("<br>");
    return `
      <tr>
        <td class="num">${row.rank}<br><span class="muted">${fmt.format(row.priorityScore)}</span></td>
        <td>${escapeHtml(actorLabel(row))}<br><span class="tag">${escapeHtml(row.kind)}</span><br><span class="mono muted">${escapeHtml(row.id)}</span></td>
        <td>${addressRows}</td>
        <td class="num">${fmt.format(row.totalE287Weight)}<br><span class="muted">max ${fmt.format(row.maxE287Weight)}; not gov power</span></td>
        <td>${row.enteredCount}/${row.votedDuringCount}/${row.exitedCount}<br><span class="muted">${row.confirmedEnterVoteExitCount} operational full path; ${row.confirmedEnterVoteExitWithPowerCount || 0} with power</span></td>
        <td>${voteText}</td>
        <td class="num">${fmt.format(row.totalGovernanceVotingPower || 0)}<br><span class="muted">${powerText}</span></td>
        <td class="num">${gonka(row.totalCompensationGonka)}<br><span class="muted">${row.recipientCount} recipients</span></td>
        <td>${topEvidence || "<span class=\"muted\">no public owner proof</span>"}<br><span class="muted">${escapeHtml((row.caveats || []).join(" "))}</span></td>
      </tr>
    `;
  }).join("");
}

function attributionDossierMatches(row, query) {
  if (!query) return true;
  return [
    row.id,
    row.candidateLabel,
    row.displayLabel,
    row.attributionTier,
    row.identityBoundary,
    ...(row.addresses || []),
    ...(row.hosts || []),
    ...(row.roles || []),
    ...(row.caveats || []),
    ...(row.topClaims || []).map((item) => [
      item.subject,
      item.sourceType,
      item.sourceValue,
      item.sourceUrl,
      item.telegramMessageId,
      item.telegramAuthor,
      item.telegramChat,
      item.chatPlatform,
      item.chatName,
      item.chatMessageId,
      item.chatAuthor,
      item.chatAuthorUsername,
      item.chatAuthorUserId,
    ].filter(Boolean).join(" ")),
  ].filter(Boolean).join(" ").toLowerCase().includes(query);
}

function renderAttributionDossiers() {
  if (!els.attributionTable) return;
  const query = els.search.value.trim().toLowerCase();
  const rows = (state.data.attributionDossiers || []).filter((row) => {
    if (!attributionDossierMatches(row, query)) return false;
    if (els.confidence.value !== "all" && !(row.topClaims || []).some((item) => item.confidence === els.confidence.value)) return false;
    if (els.sourceType.value !== "all" && !(row.topClaims || []).some((item) => item.sourceType === els.sourceType.value)) return false;
    return true;
  });
  document.getElementById("attributionRows").textContent = `${rows.length} dossiers`;
  els.attributionTable.innerHTML = rows.slice(0, 160).map((row) => {
    const tierCounts = row.tierCounts || {};
    const evidence = [
      `proof ${tierCounts.proof || 0}`,
      `telegram ${tierCounts.telegram_signal || 0}`,
      `discord ${tierCounts.discord_signal || 0}`,
      `host ${tierCounts.host_signal || 0}`,
      `context ${tierCounts.context_only || 0}`,
    ].map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join(" ");
    const addressRows = (row.addressRows || []).slice(0, 8).map((item) => (
      `<button class="row-button mono" data-address="${item.address}">${escapeHtml(item.address)}</button><br><span class="muted">${escapeHtml(actorShortLabel(item))} · ${item.roles.map(escapeHtml).join("/") || "no role"}</span>`
    )).join("<br>");
    return `
      <tr>
        <td class="num">${row.rank}</td>
        <td>${escapeHtml(row.displayLabel || row.candidateLabel)}<br>${attributionTag(row.attributionTier)} <span class="tag">${escapeHtml(row.identityBoundary || "unknown")}</span></td>
        <td>${addressRows}</td>
        <td>${(row.hosts || []).slice(0, 8).map((host) => `<span class="tag">${escapeHtml(host)}</span>`).join(" ") || "-"}</td>
        <td class="num">${gonka(row.totalCompensationGonka || 0)}<br><span class="muted">power ${fmt.format(row.totalVotingPower || 0)}</span></td>
        <td>${evidence}<br><span class="muted">${(row.topClaims || []).slice(0, 3).map((item) => `${escapeHtml(item.sourceType)} ${item.telegramMessageId ? `#${escapeHtml(item.telegramMessageId)}` : ""}`).join("<br>")}</span></td>
        <td>${(row.caveats || []).map(escapeHtml).join("<br>") || "none"}</td>
      </tr>
    `;
  }).join("");
}

function coverageRowMatches(row, query) {
  if (!query) return true;
  return [
    row.sourceFile,
    row.chat,
  ].filter(Boolean).join(" ").toLowerCase().includes(query);
}

function renderTelegramCoverage() {
  if (!els.telegramCoverageTable) return;
  const coverage = state.data.telegramCoverage || {};
  const summary = coverage.summary || {};
  const query = els.search.value.trim().toLowerCase();
  const rows = (coverage.byFile || []).filter((row) => coverageRowMatches(row, query));
  document.getElementById("telegramCoverageRows").textContent = `${rows.length} files`;
  const summaryEl = document.getElementById("telegramCoverageSummary");
  if (summaryEl) {
    summaryEl.innerHTML = [
      `files ${summary.files ?? "-"}`,
      `messages ${summary.messages ?? "-"}`,
      `raw matches ${summary.rawMatchedMessages ?? "-"}`,
      `linked ${summary.participantLinkedMessages ?? "-"}`,
      `participants with Telegram ${summary.participantAddressesWithTelegram ?? "-"}`,
      `unlinked address rows ${summary.unlinkedTelegramAddressRows ?? "-"}`,
    ].map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join(" ");
  }
  els.telegramCoverageTable.innerHTML = rows.map((row) => `
    <tr>
      <td class="mono">${escapeHtml(row.sourceFile || "-")}</td>
      <td>${escapeHtml(row.chat || "-")}</td>
      <td class="num">${fmt.format(row.rows || 0)}</td>
      <td class="num">${fmt.format(row.participantLinkedRows || 0)}</td>
      <td class="num">${fmt.format(row.addressRows || 0)}</td>
      <td>${["strongRows", "contextRows", "weakRows"].map((key) => `<span class="tag">${escapeHtml(key.replace("Rows", ""))} ${fmt.format(row[key] || 0)}</span>`).join(" ")}</td>
    </tr>
  `).join("");
}

function unlinkedTelegramMatches(row, query) {
  if (!query) return true;
  return [
    row.chat,
    row.messageId,
    row.date,
    row.author,
    row.sourceFile,
    row.sourceType,
    row.signalStrength,
    row.excerpt,
    ...(row.addresses || []),
    ...(row.urls || []),
    ...(row.usernames || []),
  ].filter(Boolean).join(" ").toLowerCase().includes(query);
}

function renderTelegramUnlinkedTable() {
  if (!els.telegramUnlinkedTable) return;
  const query = els.search.value.trim().toLowerCase();
  const rows = ((state.data.telegramCoverage || {}).unlinkedAddressRows || []).filter((row) => unlinkedTelegramMatches(row, query));
  document.getElementById("telegramUnlinkedRows").textContent = `${rows.length} shown`;
  els.telegramUnlinkedTable.innerHTML = rows.slice(0, 200).map((row) => `
    <tr>
      <td>${escapeHtml(row.date || "-")}<br><span class="mono muted">${escapeHtml(row.sourceFile || "")} ${escapeHtml(row.messageId || "")}</span></td>
      <td>${escapeHtml(row.author || "-")}<br><span class="muted">${escapeHtml(row.chat || "")}</span></td>
      <td>${(row.addresses || []).map((address) => `<span class="mono">${escapeHtml(address)}</span>`).join("<br>")}</td>
      <td>${escapeHtml(row.sourceType || "-")}<br>${attributionTag({ sourceType: row.sourceType, attributionTier: row.sourceType?.startsWith("telegram_") && (row.signalStrength || "").startsWith("strong") ? "telegram_signal" : "context_only" })} <span class="tag">${escapeHtml(row.confidence || "")}</span></td>
      <td>${escapeHtml(row.excerpt || "")}</td>
    </tr>
  `).join("");
}

function renderTelegramTable() {
  const query = els.search.value.trim().toLowerCase();
  const rows = (state.data.telegramEvidence || []).filter((row) => {
    if (!query) return true;
    return [
      row.chat,
      row.messageId,
      row.date,
      row.author,
      row.evidenceSource,
      row.sourceType,
      row.bestChatCandidateLabel,
      row.excerpt,
      ...(row.contextMessages || []).map((item) => [item.author, item.excerpt, item.replyText].join(" ")),
      ...(row.addresses || []),
      ...(row.urls || []),
      ...(row.usernames || []),
    ].join(" ").toLowerCase().includes(query);
  });
  document.getElementById("telegramRows").textContent = `${rows.length} shown`;
  els.telegramTable.innerHTML = rows.slice(0, 300).map((row) => `
    <tr>
      <td>${escapeHtml(row.date || "-")}<br><span class="mono muted">${escapeHtml(row.messageId || "")}</span></td>
      <td>${escapeHtml(row.chat || "-")}</td>
      <td>${escapeHtml(row.author || "-")}<br><span class="tag">${escapeHtml(row.evidenceSource || "telegram")}</span> ${row.bestChatCandidateLabel ? `<span class="tag">${escapeHtml(row.bestChatCandidateLabel)}</span>` : ""}</td>
      <td>${(row.addresses || []).map((address) => `<button class="row-button mono" data-address="${address.replace("gonkavaloper", "gonka")}">${escapeHtml(address)}</button>`).join("<br>")}</td>
      <td><span class="tag">${escapeHtml(row.sourceType || "")}</span> <span class="tag">${escapeHtml(row.confidence || "")}</span><br>${escapeHtml(row.excerpt || "")}${chatContextHtml({ chatContextMessages: row.contextMessages })}</td>
    </tr>
  `).join("");
}

function matchesGlobalEvidenceFilters(row, query) {
  if (els.confidence.value !== "all" && row.confidence !== els.confidence.value) return false;
  if (els.sourceType.value !== "all" && row.sourceType !== els.sourceType.value) return false;
  if (!query) return true;
  return [
    row.address,
    row.subject,
    row.category,
    row.sourceType,
    row.sourceValue,
    row.confidence,
    row.caveat,
    row.chatReplyText,
    row.telegramReplyText,
    ...(row.chatContextMessages || []).map((item) => [item.author, item.excerpt, item.replyText].join(" ")),
    ...(row.telegramContextMessages || []).map((item) => [item.author, item.excerpt, item.replyText].join(" ")),
  ].filter(Boolean).join(" ").toLowerCase().includes(query);
}

function rankedMatches(row, query) {
  if (els.label.value !== "all" && row.label !== els.label.value) return false;
  if (els.confidence.value !== "all" && row.confidence !== els.confidence.value) return false;
  if (els.vote.value !== "all" && !Object.keys(row.voteCounts || {}).includes(els.vote.value)) return false;
  if (!query) return true;
  return [
    row.label,
    row.confidence,
    row.attributionTier,
    ...(row.addresses || []),
    ...(row.roles || []),
    ...(row.identityTypes || []),
    ...(row.caveats || []),
  ].join(" ").toLowerCase().includes(query);
}

function renderRankedTable() {
  const query = els.search.value.trim().toLowerCase();
  const rows = (state.data.rankedParties || []).filter((row) => rankedMatches(row, query));
  document.getElementById("rankedRows").textContent = `${rows.length} shown`;
  els.rankedTable.innerHTML = rows.slice(0, 100).map((row) => `
    <tr>
      <td class="num">${row.rank}</td>
      <td>${escapeHtml(actorLabel(row))}<br>${attributionTag(row)}<br><span class="muted">${escapeHtml(row.identityTypes.join(", "))}</span></td>
      <td>${row.roles.map((role) => `<span class="tag">${escapeHtml(role)}</span>`).join(" ")}</td>
      <td>${row.addresses.map((address) => `<button class="row-button mono" data-address="${address}">${escapeHtml(address)}</button>`).join("<br>")}</td>
      <td class="num">${gonka(row.totalCompensationGonka)}</td>
      <td class="num">${fmt.format(row.overallPriority)}</td>
      <td><span class="tag ${row.confidence === "high" ? "good" : row.confidence === "medium" ? "warn" : ""}">${escapeHtml(row.confidence)}</span></td>
      <td>${row.caveats.map((item) => `<span class="muted">${escapeHtml(item)}</span>`).join("<br>")}</td>
    </tr>
  `).join("");
}

function renderEvidenceTable() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const labelAddresses = selectedLabel === "all"
    ? null
    : new Set((state.data.actors || []).filter((actor) => actor.label === selectedLabel).map((actor) => actor.address));
  const rows = (state.data.evidenceClaims || []).filter((row) => {
    if (labelAddresses && row.address && !labelAddresses.has(row.address)) return false;
    return matchesGlobalEvidenceFilters(row, query);
  });
  document.getElementById("evidenceRows").textContent = `${rows.length} shown`;
  els.evidenceTable.innerHTML = rows.slice(0, 300).map((row) => `
    <tr>
      <td>${escapeHtml(row.subject || "-")}</td>
      <td>${row.address ? `<button class="row-button mono" data-address="${row.address}">${escapeHtml(row.address)}</button>` : "<span class=\"muted\">repo/social</span>"}</td>
      <td><span class="tag">${escapeHtml(row.category)}</span></td>
      <td>${escapeHtml(row.sourceType)}<br><span class="mono muted">${escapeHtml(row.chatMessageId ? `${row.chatPlatform || "chat"} ${row.chatName || ""} ${row.chatMessageId}` : (row.telegramMessageId ? `${row.telegramChat || ""} ${row.telegramMessageId}` : row.sourceUrl))}</span></td>
      <td>${escapeHtml(row.sourceValue)}</td>
      <td>${attributionTag(row)} <span class="tag">${escapeHtml(row.confidence)}</span></td>
    </tr>
  `).join("");
}

function interestClusterMatches(row, query) {
  if (!query) return true;
  return [
    row.id,
    row.kind,
    row.label,
    row.evidenceBoundary,
    ...(row.addresses || []),
    ...(row.roles || []),
    ...(row.caveats || []),
  ].join(" ").toLowerCase().includes(query);
}

function renderInterestClusterTable() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const rows = (state.data.interestClusters || []).filter((row) => {
    if (!interestClusterMatches(row, query)) return false;
    if (selectedLabel !== "all" && row.label !== selectedLabel) return false;
    if (els.confidence.value !== "all") {
      const hasConfidence = (row.topEvidence || []).some((item) => item.confidence === els.confidence.value);
      if (!hasConfidence) return false;
    }
    if (els.sourceType.value !== "all") {
      const hasSourceType = (row.topEvidence || []).some((item) => item.sourceType === els.sourceType.value);
      if (!hasSourceType) return false;
    }
    if (els.vote.value !== "all" && !(row.votePowerByOption || {})[els.vote.value] && !(row.voteAddressCounts || {})[els.vote.value]) return false;
    return true;
  });
  document.getElementById("interestClusterRows").textContent = `${rows.length} shown`;
  els.interestClusterTable.innerHTML = rows.map((row) => `
    <tr>
      <td class="num">${row.rank}</td>
      <td>${escapeHtml(actorLabel(row))}<br><span class="muted">${escapeHtml(row.id)} · ${escapeHtml(row.kind)}</span></td>
      <td>${(row.addresses || []).map((address) => `<button class="row-button mono" data-address="${address}">${escapeHtml(address)}</button>`).join("<br>")}</td>
      <td class="num">${gonka(row.totalCompensationGonka)}<br><span class="muted">${row.recipientCount} recipients</span></td>
      <td class="num">${fmt.format(row.totalVotingPower || 0)}<br><span class="muted">${row.voterCount} voters</span></td>
      <td>${Object.entries(row.votePowerByOption || {}).map(([option, power]) => `<span class="tag">${escapeHtml(optionLabels[option] || option)} ${fmt.format(power)}</span>`).join(" ") || "-"}</td>
      <td><span class="tag">${escapeHtml(row.evidenceBoundary)}</span><br><span class="muted">proof ${row.proofCount}, signals ${row.signalClaimCount}</span></td>
      <td>${(row.caveats || []).map(escapeHtml).join("<br>") || "none"}</td>
    </tr>
  `).join("");
}

function benefitPowerMatches(row, query) {
  if (!query) return true;
  return [
    row.address,
    row.label,
    row.voteOption,
    row.attributionTier,
    row.clusterId,
    row.clusterKind,
    row.evidenceBoundary,
    ...(row.nextActions || []),
  ].join(" ").toLowerCase().includes(query);
}

function renderBenefitPowerTable() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const rows = (state.data.benefitPowerMatrix || []).filter((row) => {
    if (!benefitPowerMatches(row, query)) return false;
    if (selectedLabel !== "all" && row.label !== selectedLabel) return false;
    if (!voteMatches(row, els.vote.value)) return false;
    if (els.confidence.value !== "all" && !(row.topEvidence || []).some((item) => item.confidence === els.confidence.value)) return false;
    if (els.sourceType.value !== "all" && !(row.topEvidence || []).some((item) => item.sourceType === els.sourceType.value)) return false;
    return true;
  });
  document.getElementById("benefitPowerRows").textContent = `${rows.length} shown`;
  els.benefitPowerTable.innerHTML = rows.map((row) => `
    <tr>
      <td class="num">${row.rank}<br><span class="muted">${fmt.format(row.triageScore)}</span></td>
      <td><button class="row-button mono" data-address="${row.address}">${escapeHtml(row.address)}</button></td>
      <td>${escapeHtml(actorLabel(row))}<br>${attributionTag(row)}<br><span class="muted">${escapeHtml(row.clusterId || "no cluster")}</span></td>
      <td class="num">${gonka(row.totalCompensationGonka)}</td>
      <td class="num">${fmt.format(row.votingPower || 0)}<br><span class="muted">${escapeHtml(voteDisplayText(row))}</span></td>
      <td>${row.recipientVoterOverlap ? "<span class=\"tag warn\">recipient voter</span>" : row.isRecipient ? "<span class=\"tag\">recipient</span>" : row.isVoter ? "<span class=\"tag\">voter</span>" : "-"}</td>
      <td><span class="tag ${identityBoundary(row) === "public_owner_proof" ? "good" : ""}">${escapeHtml(identityBoundary(row))}</span><br><span class="muted">proof ${row.proofCount}; high ${row.highConfidenceClaimCount}</span></td>
      <td>${(row.nextActions || []).map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join(" ")}</td>
    </tr>
  `).join("");
}

function publicNameMatches(row, query) {
  if (!query) return true;
  return [
    row.address,
    row.label,
    row.bestPublicName,
    row.voteOption,
    row.evidenceBoundary,
    row.attributionTier,
    row.validatorOperatorAddress,
    row.validatorMoniker,
    row.validatorWebsite,
    row.validatorIdentity,
    row.validatorSecurityContact,
    row.inferenceUrl,
    ...(row.roles || []),
    ...(row.gnsNames || []),
    ...(row.reverseGnsNames || []),
    ...(row.nextActions || []),
    ...(row.publicNameSources || []).map((item) => `${item.sourceType} ${item.value}`),
  ].filter(Boolean).join(" ").toLowerCase().includes(query);
}

function renderPublicNameTable() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const rows = (state.data.publicNameEnrichment?.rows || []).filter((row) => {
    if (!publicNameMatches(row, query)) return false;
    if (selectedLabel !== "all" && row.label !== selectedLabel) return false;
    if (!voteMatches(row, els.vote.value)) return false;
    if (els.confidence.value !== "all" && !(row.publicNameSources || []).some((item) => item.confidence === els.confidence.value)) return false;
    if (els.sourceType.value !== "all" && !(row.publicNameSources || []).some((item) => item.sourceType === els.sourceType.value)) return false;
    return true;
  });
  document.getElementById("publicNameRows").textContent = `${rows.length} shown`;
  els.publicNameTable.innerHTML = rows.map((row) => `
    <tr>
      <td><button class="row-button mono" data-address="${row.address}">${escapeHtml(row.address)}</button></td>
      <td>${escapeHtml(actorLabel(row))}<br>${attributionTag(row)}</td>
      <td>${escapeHtml(row.bestPublicName || "none")}<br><span class="muted">${escapeHtml((row.reverseGnsNames || []).join(", ") || (row.gnsNames || []).join(", ") || "no GNS")}</span></td>
      <td>${(row.roles || []).map((role) => `<span class="tag">${escapeHtml(role)}</span>`).join(" ")}</td>
      <td class="num">${gonka(row.totalCompensationGonka || 0)}<br><span class="muted">power ${fmt.format(row.votingPower || 0)} · ${escapeHtml(voteDisplayText(row))}</span></td>
      <td><span class="tag ${row.evidenceBoundary === "public_owner_proof" ? "good" : row.evidenceBoundary === "unknown_public_owner" ? "warn" : ""}">${escapeHtml(row.evidenceBoundary)}</span></td>
      <td>${(row.publicNameSources || []).slice(0, 5).map((item) => `<span class="tag">${escapeHtml(item.sourceType)}: ${escapeHtml(String(item.value).slice(0, 52))}</span>`).join(" ") || "-"}</td>
      <td>${(row.nextActions || []).map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join(" ")}</td>
    </tr>
  `).join("");
}

function renderActorGraph() {
  const ranked = (state.data.rankedParties || []).slice(0, 25);
  const claims = state.data.evidenceClaims || [];
  const graphClaimTypes = new Set([
    "validator_key_match",
    "matched_validator_identity",
    "matched_validator_moniker",
    "matched_validator_security_contact",
    "validator_identity",
    "validator_moniker",
    "validator_security_contact",
    "gns_name",
    "gns_reverse",
    "same_inference_host",
    "same_validator_website",
    "same_security_contact",
    "same_validator_identity",
    "same_gns_contact",
    "same_ip_prefix",
    "same_asn",
    "same_tls_cert",
  ]);
  const nodes = [];
  const links = [];
  const seen = new Set();
  const addNode = (id, name, category, value = 10) => {
    if (seen.has(id)) return;
    seen.add(id);
    nodes.push({ id, name, category, value, symbolSize: Math.max(12, Math.min(46, value)) });
  };
  ranked.forEach((party) => {
    addNode(party.id, `#${party.rank} ${actorShortLabel(party)}`, "party", 18 + party.overallPriority / 3);
    party.addresses.forEach((address) => {
      const addressId = `address:${address}`;
      addNode(addressId, address, "address", 14);
      links.push({ source: party.id, target: addressId, value: "contains" });
      const seenClaims = new Set();
      claims
        .filter((claim) => claim.address === address && (claim.isAttributionProof || graphClaimTypes.has(claim.sourceType)))
        .filter((claim) => {
          const key = `${claim.sourceType}:${claim.sourceValue}`;
          if (seenClaims.has(key)) return false;
          seenClaims.add(key);
          return true;
        })
        .slice(0, 5)
        .forEach((claim) => {
        const claimId = `${claim.sourceType}:${claim.sourceValue}`.slice(0, 180);
        addNode(claimId, claim.sourceValue || claim.sourceType, claim.isAttributionProof ? "proof" : "signal", claim.isAttributionProof ? 18 : 11);
        links.push({ source: addressId, target: claimId, value: claim.sourceType });
      });
    });
  });
  state.charts.actorGraph.setOption({
    tooltip: chartTooltip({ formatter: (p) => p.dataType === "edge" ? `${p.data.source}<br>${escapeHtml(p.data.value)}<br>${p.data.target}` : escapeHtml(p.data.name) }),
    legend: [{ data: ["party", "address", "proof", "signal"], textStyle: { color: "#a7afba" } }],
    series: [{
      type: "graph",
      layout: "force",
      roam: true,
      categories: ["party", "address", "proof", "signal"].map((name) => ({ name })),
      data: nodes,
      links,
      label: { show: true, color: "#eef0f2", formatter: (p) => String(p.data.name).slice(0, 42) },
      lineStyle: { color: "source", opacity: 0.45 },
      force: { repulsion: 160, edgeLength: 90 },
    }],
  }, true);
}

function renderEpochTable() {
  const epochs = state.data.epochs || [];
  document.getElementById("epochRows").textContent = `${epochs.length} epochs`;
  els.epochTable.innerHTML = epochs.map((row) => `
    <tr>
      <td class="num">e${row.epoch}</td>
      <td><span class="tag">${escapeHtml(row.componentSource.replaceAll("_", " "))}</span></td>
      <td class="num">${row.recipientsCount}</td>
      <td class="num">${gonka(row.totalGonka)}</td>
      <td class="num">${fmt.format(row.shareOfTotal * 100)}%</td>
      <td><button class="row-button mono" data-address="${row.topRecipient}">${escapeHtml(row.topRecipient || "-")}</button></td>
      <td class="num">${gonka(row.topRecipientGonka)}</td>
    </tr>
  `).join("");
}

function renderMethodology() {
  const method = state.data.methodology || {};
  const gov = state.data.governancePowerEvidence?.summary || {};
  const rows = [
    ["Governance vote", method.governanceVoteRule],
    ["Governance voting power", method.governanceVotingPowerRule],
    ["Voting-end boundary", gov.lastBlockBeforeVotingEnd ? `Last block before voting end: ${gov.lastBlockBeforeVotingEnd.height} at ${gov.lastBlockBeforeVotingEnd.time}; first block after: ${gov.firstBlockAfterVotingEnd?.height} at ${gov.firstBlockAfterVotingEnd?.time}.` : ""],
    ["Archive gov evidence", gov.decodedGovVotesCount ? `Archive abci_query decoded ${gov.decodedGovVotesBeforeEndCount ?? gov.decodedGovVotesCount} gov votes at the last pre-end block and ${gov.decodedGovVotesAfterEndCount ?? "unknown"} votes at the first post-end block; aggregate tally matches final proposal tally: ${gov.decodedTallyMatchesFinalTally ? "yes" : "no"}; per-voter power status: ${gov.perVoterPowerStatus || "unknown"}.` : ""],
    ["Inference epoch weight", method.inferenceEpochRule],
    ["Recipient-voter conflict", method.recipientConflictRule],
    ["Identity evidence", method.identityRule],
  ].filter((row) => row[1]);
  document.getElementById("methodologyNotes").innerHTML = `
    <dl class="kv methodology-kv">
      ${rows.map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd>`).join("")}
    </dl>
    <p>${escapeHtml("GRC off-chain voters are not identified in the upstream repository. Public labels come from validator metadata, validator-key matches, GNS .gnk names, and participant inference URLs; unknown owners remain marked as unknown. Strict clusters use public self-declared identity evidence. Signal clusters may use infrastructure clues such as shared host, IP, RDAP organization, or TLS certificate and are not private attribution. Per-voter governance voting power is computed from archive staking validators and delegations, not estimated from inference epochs.")}</p>
  `;
}

function buildLabelRows(data) {
  const labels = new Map();
  const ensure = (label) => {
    if (!labels.has(label)) {
      labels.set(label, {
        label,
        addresses: new Set(),
        identityTypes: new Set(),
        recipientCount: 0,
        voterCount: 0,
        totalGonka: 0,
        votes: new Set(),
        voteOptions: new Set(),
        attributionTiers: new Set(),
      });
    }
    return labels.get(label);
  };

  data.recipients.forEach((row) => {
    const item = ensure(row.label || "Unknown public owner");
    item.addresses.add(row.address);
    item.identityTypes.add(row.identityType || "unknown");
    item.attributionTiers.add(row.attributionTier || "context_only");
    item.recipientCount += 1;
    item.totalGonka += row.totalGonka || 0;
  });

  data.votes.forEach((row) => {
    const item = ensure(row.label || "Unknown public owner");
    item.addresses.add(row.voter);
    item.identityTypes.add(row.identityType || "unknown");
    item.attributionTiers.add(row.attributionTier || "context_only");
    item.voterCount += 1;
    item.votes.add(voteDisplayText(row));
    const options = voteSplitOptions(row);
    if (options.length) options.forEach((option) => item.voteOptions.add(option.option));
    else item.voteOptions.add(row.primaryOption || primaryOption(row));
  });

  return [...labels.values()]
    .map((row) => ({
      ...row,
      addresses: [...row.addresses].sort(),
      identityTypes: [...row.identityTypes].sort(),
      votes: [...row.votes].sort(),
      voteOptions: [...row.voteOptions].sort(),
      attributionTiers: [...row.attributionTiers].sort(),
    }))
    .sort((a, b) => b.totalGonka - a.totalGonka || b.addresses.length - a.addresses.length || a.label.localeCompare(b.label));
}

function renderLabelTable() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const rows = buildLabelRows(state.data).filter((row) => {
    if (selectedLabel !== "all" && row.label !== selectedLabel) return false;
    if (els.identity.value !== "all" && !row.identityTypes.includes(els.identity.value)) return false;
    if (els.vote.value !== "all" && !row.voteOptions.includes(els.vote.value) && !(els.vote.value === "did_not_vote" && row.recipientCount > row.voterCount)) return false;
    if (!query) return true;
    return [
      row.label,
      ...row.attributionTiers,
      ...row.identityTypes,
      ...row.addresses,
      ...row.votes,
    ].join(" ").toLowerCase().includes(query);
  });

  document.getElementById("labelRows").textContent = `${rows.length} shown`;
  els.labelTable.innerHTML = rows.map((row) => `
    <tr>
      <td>${escapeHtml(actorLabel(row))}<br>${row.attributionTiers.map((tier) => attributionTag(tier)).join(" ")}</td>
      <td>${row.identityTypes.map((type) => `<span class="tag">${escapeHtml(type)}</span>`).join(" ")}</td>
      <td>${row.addresses.map((address) => `<button class="row-button mono" data-address="${address}">${escapeHtml(address)}</button>`).join("<br>")}</td>
      <td class="num">${row.recipientCount}</td>
      <td class="num">${row.voterCount}</td>
      <td class="num">${gonka(row.totalGonka)}</td>
    </tr>
  `).join("");
}

function renderTables() {
  document.getElementById("recipientRows").textContent = `${state.filteredRecipients.length} shown`;
  els.recipientTable.innerHTML = state.filteredRecipients.map((row) => `
    <tr>
      <td class="num">${row.rank}</td>
      <td><button class="row-button mono" data-address="${row.address}">${escapeHtml(row.address)}</button></td>
      <td>${escapeHtml(actorLabel(row))}<br>${attributionTag(row)}</td>
      <td><span class="tag">${escapeHtml(row.status)}</span></td>
      <td>${voteDisplayHtml(row)}</td>
      <td>${escapeHtml(row.strictClusterId || row.signalClusterId || "-")}</td>
      <td class="num">${gonka(row.totalGonka)}</td>
    </tr>
  `).join("");

  const query = els.search.value.trim().toLowerCase();
  const label = els.label.value;
  const filteredVotes = state.data.votes.filter((row) => {
    if (!textMatch({ ...row, address: row.voter }, query)) return false;
    if (!voteMatches(row, els.vote.value)) return false;
    if (els.identity.value !== "all" && row.identityType !== els.identity.value) return false;
    if (label !== "all" && row.label !== label) return false;
    return true;
  });
  document.getElementById("voteRows").textContent = `${filteredVotes.length} shown`;
  els.voteTable.innerHTML = filteredVotes.map((row) => `
    <tr>
      <td class="num">${row.height}</td>
      <td><button class="row-button mono" data-address="${row.voter}">${escapeHtml(row.voter)}</button><br><span class="muted">${escapeHtml(actorLabel(row))}</span><br>${attributionTag(row)}</td>
      <td>${row.isRecipient ? "Yes" : "No"}</td>
      <td>${voteDisplayHtml(row)}</td>
      <td>${escapeHtml(row.strictClusterId || row.signalClusterId || "-")}</td>
      <td>${row.votingPower == null ? "unknown" : fmt.format(row.votingPower)}<br><span class="muted">${escapeHtml(row.votingPowerReason || row.votingPowerSource || "")}</span><br><span class="muted">${escapeHtml(formatTime(row.blockTime))}</span></td>
    </tr>
  `).join("");

  enhanceAddressActions();
}

function clusterEdges(cluster) {
  const addresses = new Set(cluster.addresses || []);
  return (state.data.identityGraph?.edges || []).filter((edge) => {
    const sourceAddress = edge.source.startsWith("address:") ? edge.source.slice(8) : "";
    const targetAddress = edge.target.startsWith("address:") ? edge.target.slice(8) : "";
    return addresses.has(sourceAddress) || addresses.has(targetAddress);
  });
}

function clusterMatches(cluster, query) {
  if (!query) return true;
  return [
    cluster.id,
    cluster.label,
    cluster.weakestEvidence,
    ...(cluster.addresses || []),
  ].join(" ").toLowerCase().includes(query);
}

function renderClusterTables() {
  const query = els.search.value.trim().toLowerCase();
  const passesEvidenceFilters = (cluster) => {
    const edges = clusterEdges(cluster);
    if (els.confidence.value !== "all" && !edges.some((edge) => edge.confidence === els.confidence.value)) return false;
    if (els.sourceType.value !== "all" && !edges.some((edge) => edge.sourceType === els.sourceType.value)) return false;
    return true;
  };
  const strict = (state.data.identityGraph?.strictClusters || []).filter((cluster) => clusterMatches(cluster, query) && passesEvidenceFilters(cluster));
  const signal = (state.data.identityGraph?.signalClusters || []).filter((cluster) => clusterMatches(cluster, query) && passesEvidenceFilters(cluster));
  document.getElementById("strictClusterRows").textContent = `${strict.length} shown`;
  document.getElementById("signalClusterRows").textContent = `${signal.length} shown`;
  els.strictClusterTable.innerHTML = strict.map((cluster) => `
    <tr>
      <td>${escapeHtml(cluster.id)}</td>
      <td>${escapeHtml(actorLabel(cluster))}</td>
      <td>${cluster.addresses.map((address) => `<button class="row-button mono" data-address="${address}">${escapeHtml(address)}</button>`).join("<br>")}</td>
      <td class="num">${cluster.recipientCount}</td>
      <td class="num">${cluster.voterCount}</td>
      <td class="num">${gonka(cluster.totalCompensationGonka)}</td>
    </tr>
  `).join("");
  els.signalClusterTable.innerHTML = signal.map((cluster) => `
    <tr>
      <td>${escapeHtml(cluster.id)}</td>
      <td>${escapeHtml(actorLabel(cluster))}</td>
      <td>${cluster.addresses.map((address) => `<button class="row-button mono" data-address="${address}">${escapeHtml(address)}</button>`).join("<br>")}</td>
      <td><span class="tag">${escapeHtml(cluster.weakestEvidence)}</span></td>
      <td class="num">${cluster.evidenceCount}</td>
      <td class="num">${gonka(cluster.totalCompensationGonka)}</td>
    </tr>
  `).join("");
}

function renderAll() {
  renderAttackTimeline();
  renderCompensationChart();
  renderWaterfall();
  renderEpochChart();
  renderModelCapChart();
  renderModelCapMechanics();
  renderHeatmap();
  renderRecipientCompByWindow();
  renderMatrix();
  renderTimeline();
  renderTally();
  renderVoterPowerChart();
  renderWindowPowerChart();
  renderActorGraph();
  renderEntryExitChart();
  renderHypotheses();
  renderAnomalyTable();
  renderEntryExitTable();
  renderTelegramTable();
  renderAttributionDossiers();
  renderTelegramCoverage();
  renderTelegramUnlinkedTable();
  renderBenefitPowerTable();
  renderPublicNameTable();
  renderRankedTable();
  renderInterestClusterTable();
  renderEvidenceTable();
  renderSearchIndex();
  renderLabelTable();
  renderEpochTable();
  renderMethodology();
  renderTables();
  renderClusterTables();
  enhanceAddressActions();
}

function ensureTableTitles() {
  document.querySelectorAll(".panel .table-wrap").forEach((wrap) => {
    if (wrap.querySelector(".table-title")) return;
    const panel = wrap.closest(".panel");
    const heading = panel?.querySelector(":scope > .panel-head h2");
    const title = heading ? heading.textContent.trim() : "Table";
    const titleEl = document.createElement("div");
    titleEl.className = "table-title";
    titleEl.textContent = title;
    wrap.prepend(titleEl);
  });
}

function initCollapsibleTables() {
  document.querySelectorAll(".panel [data-table-collapsible='1']").forEach((wrap) => {
    const panel = wrap.closest(".panel");
    if (!panel) return;
    if (wrap === panel) return;
    const heading = panel?.querySelector(":scope > .panel-head");
    if (!heading) return;
    if (heading.querySelector(".table-toggle")) return;

    const collapsed = wrap.dataset.tableCollapsed === "true";
    if (collapsed) {
      wrap.classList.add("hidden");
      panel.classList.add("is-collapsed-table");
    }

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "table-toggle";
    const label = () => (wrap.classList.contains("hidden") ? "Show section" : "Hide section");
    toggle.textContent = label();
    toggle.setAttribute("aria-expanded", String(!wrap.classList.contains("hidden")));

    toggle.addEventListener("click", () => {
      wrap.classList.toggle("hidden");
      wrap.dataset.tableCollapsed = String(wrap.classList.contains("hidden"));
      panel.classList.toggle("is-collapsed-table", wrap.classList.contains("hidden"));
      toggle.textContent = label();
      toggle.setAttribute("aria-expanded", String(!wrap.classList.contains("hidden")));
      resizeAllChartsNow();
    });

    heading.appendChild(toggle);
  });
}

function claimSourceLine(row) {
  if (row.chatMessageId || row.chatAuthor || row.chatName) {
    return [
      row.chatPlatform || "chat",
      row.chatName,
      row.chatMessageId,
      row.chatMessageTime,
      row.chatAuthor ? `by ${row.chatAuthor}` : "",
      row.chatAuthorUsername ? `@${row.chatAuthorUsername}` : "",
      row.chatAuthorUserId ? `uid:${row.chatAuthorUserId}` : "",
    ].filter(Boolean).join(" · ");
  }
  if (row.telegramMessageId || row.telegramAuthor || row.telegramChat) {
    return [
      row.telegramChat,
      row.telegramMessageId,
      row.telegramMessageTime,
      row.telegramAuthor ? `by ${row.telegramAuthor}` : "",
    ].filter(Boolean).join(" · ");
  }
  return row.sourceUrl || row.sourceFile || "";
}

function chatContextHtml(row) {
  const context = row.chatContextMessages || row.telegramContextMessages || [];
  if (!context.length && !(row.chatReplyText || row.telegramReplyText)) return "";
  if (!context.length) {
    return `<div class="chat-context"><div class="chat-context-row"><span class="tag">reply</span><span>${escapeHtml(row.chatReplyText || row.telegramReplyText)}</span></div></div>`;
  }
  return `<div class="chat-context">${context.map((item) => {
    const relations = (item.relations || []).map((relation) => `<span class="tag">${escapeHtml(relation)}</span>`).join(" ");
    return `<div class="chat-context-row ${item.relations?.includes("target") ? "target" : ""}">
      <div class="chat-context-meta">${relations}<span class="mono">${escapeHtml(item.messageId || "")}</span> ${escapeHtml(item.date || "")} ${item.author ? `by ${escapeHtml(item.author)}` : ""}</div>
      ${item.replyText ? `<div class="chat-context-reply">reply: ${escapeHtml(item.replyText)}</div>` : ""}
      <div>${escapeHtml(item.excerpt || "")}</div>
    </div>`;
  }).join("")}</div>`;
}

function claimDetailHtml(row) {
  return `<dt>${escapeHtml(row.sourceType)}</dt><dd>${escapeHtml(row.sourceValue)} ${attributionTag(row)} <span class="tag">${escapeHtml(row.confidence || "")}</span><br><span class="mono muted">${escapeHtml(claimSourceLine(row))}</span><br><span class="muted">${escapeHtml(row.caveat || "")}</span>${chatContextHtml(row)}</dd>`;
}

function claimDisplayPriority(row) {
  const tierPriority = { proof: 0, telegram_signal: 1, discord_signal: 1, host_signal: 2, public_signal: 3, context_only: 4 };
  const sourceType = row.sourceType || "";
  const chatBoost = sourceType.startsWith("telegram_") || sourceType.startsWith("discord_") ? -1 : 0;
  return [
    chatBoost,
    tierPriority[attributionTier(row)] ?? 9,
    { high: 0, medium: 1, low: 2 }[row.confidence] ?? 3,
    sourceType,
  ];
}

function compareClaims(a, b) {
  const left = claimDisplayPriority(a);
  const right = claimDisplayPriority(b);
  for (let index = 0; index < left.length; index += 1) {
    if (left[index] < right[index]) return -1;
    if (left[index] > right[index]) return 1;
  }
  return String(a.sourceValue || "").localeCompare(String(b.sourceValue || ""));
}

function openDrawer(address) {
  const recipient = state.data.recipients.find((row) => row.address === address);
  const vote = state.data.votes.find((row) => row.voter === address);
  const evidence = state.data.identityEvidence.filter((row) => row.address === address);
  const evidenceClaims = (state.data.evidenceClaims || []).filter((row) => row.address === address).sort(compareClaims);
  const chatEvidenceClaims = evidenceClaims.filter((row) => {
    const sourceType = row.sourceType || "";
    return sourceType.startsWith("telegram_") || sourceType.startsWith("discord_") || row.chatMessageId || row.telegramMessageId;
  });
  const actor = (state.data.actors || []).find((row) => row.address === address);
  const rankedParty = (state.data.rankedParties || []).find((row) => (row.addresses || []).includes(address));
  const attributionDossiers = (state.data.attributionDossiers || []).filter((row) => (row.addresses || []).includes(address));
  const windowPower = ((state.data.votingPowerWindow || {}).rows || []).find((row) => row.voter === address);
  const nodeInfo = recipient?.publicNodeInfo || vote?.publicNodeInfo || {};
  const matchedValidator = nodeInfo.matchedValidator || {};
  const gnsNames = recipient?.gnsNames || vote?.gnsNames || [];
  const clusters = [
    ...(state.data.identityGraph?.strictClusters || []),
    ...(state.data.identityGraph?.signalClusters || []),
  ].filter((cluster) => cluster.addresses.includes(address));
  const entryExitClusters = (state.data.epochEntryExitClusters || []).filter((cluster) => cluster.addresses.includes(address));
  const graphEdges = (state.data.identityGraph?.edges || []).filter((edge) => edge.source === `address:${address}` || edge.target === `address:${address}`);
  const label = recipient?.label || vote?.label || "Unknown public owner";
  els.drawerContent.innerHTML = `
    <h2>${escapeHtml(label)}</h2>
    <p class="drawer-address-line"><span class="mono selectable-address">${escapeHtml(address)}</span><button class="copy-address-button" type="button" data-copy-address="${escapeHtml(address)}">copy</button></p>
    <div class="drawer-section">
      <h3>Chat Evidence</h3>
      ${chatEvidenceClaims.length ? `<dl class="kv">${chatEvidenceClaims.slice(0, 12).map(claimDetailHtml).join("")}</dl>` : "<p>No Telegram or Discord evidence for this address.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Attribution Dossier</h3>
      ${attributionDossiers.length ? attributionDossiers.map((dossier) => {
        const telegramClaims = (dossier.telegramClaims || []).slice(0, 8);
        const discordClaims = (dossier.discordClaims || []).slice(0, 8);
        return `<dl class="kv">
          <dt>Candidate</dt><dd>${escapeHtml(dossier.displayLabel || dossier.candidateLabel)} ${attributionTag(dossier.attributionTier)} <span class="tag">${escapeHtml(dossier.identityBoundary || "unknown")}</span></dd>
          <dt>Addresses</dt><dd>${(dossier.addresses || []).map((item) => `<button class="row-button mono" data-address="${item}">${escapeHtml(item)}</button>`).join("<br>")}</dd>
          <dt>Hosts</dt><dd>${(dossier.hosts || []).length ? dossier.hosts.map((host) => `<span class="tag">${escapeHtml(host)}</span>`).join(" ") : "none"}</dd>
          <dt>Evidence</dt><dd>${["proof", "telegram_signal", "discord_signal", "host_signal", "context_only"].map((tier) => `<span class="tag">${escapeHtml(attributionTierLabel(tier))} ${(dossier.tierCounts || {})[tier] || 0}</span>`).join(" ")}</dd>
          <dt>Telegram</dt><dd>${telegramClaims.length ? telegramClaims.map((claim) => `${escapeHtml(claim.telegramChat || "")} ${escapeHtml(claim.telegramMessageId || "")}<br><span class="muted">${escapeHtml(claim.telegramMessageTime || "")} ${claim.telegramAuthor ? `by ${escapeHtml(claim.telegramAuthor)}` : ""}</span><br>${escapeHtml(claim.sourceValue || claim.telegramExcerpt || "")}`).join("<br><br>") : "none"}</dd>
          <dt>Discord</dt><dd>${discordClaims.length ? discordClaims.map((claim) => `${escapeHtml(claim.chatName || "")} ${escapeHtml(claim.chatMessageId || "")}<br><span class="muted">${escapeHtml(claim.chatMessageTime || "")} ${claim.chatAuthor ? `by ${escapeHtml(claim.chatAuthor)}` : ""} ${claim.chatAuthorUsername ? `@${escapeHtml(claim.chatAuthorUsername)}` : ""}</span><br>${escapeHtml(claim.sourceValue || claim.chatExcerpt || "")}`).join("<br><br>") : "none"}</dd>
          <dt>Caveats</dt><dd>${(dossier.caveats || []).map(escapeHtml).join("<br>") || "none"}</dd>
        </dl>`;
      }).join("") : "<p>No attribution dossier for this address.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Actor Priority</h3>
      ${actor ? `<dl class="kv">
        <dt>Roles</dt><dd>${actor.roles.map((role) => `<span class="tag">${escapeHtml(role)}</span>`).join(" ")}</dd>
        <dt>Ranked party</dt><dd>${rankedParty ? `#${rankedParty.rank} ${escapeHtml(rankedParty.label)}` : "not ranked"}</dd>
        <dt>Priority</dt><dd>${rankedParty ? fmt.format(rankedParty.overallPriority) : "none"}</dd>
        <dt>Confidence</dt><dd>${rankedParty ? escapeHtml(rankedParty.confidence) : "none"} ${rankedParty ? attributionTag(rankedParty) : ""}</dd>
        <dt>Caveats</dt><dd>${rankedParty?.caveats?.length ? rankedParty.caveats.map(escapeHtml).join("<br>") : "none"}</dd>
      </dl>` : "<p>No actor roles for this address.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Payout</h3>
      ${recipient ? `<dl class="kv">
        <dt>Total</dt><dd>${gonka(recipient.totalGonka)}</dd>
        <dt>e265-e266 attack</dt><dd>${gonka(recipient.attackE265E266Gonka)}</dd>
        <dt>e267-e276 cap</dt><dd>${gonka(recipient.capE267E276Gonka)}</dd>
        <dt>Status</dt><dd>${escapeHtml(recipient.status)}</dd>
        <dt>Inference URL</dt><dd>${recipient.inferenceUrl ? `<a href="${escapeHtml(recipient.inferenceUrl)}">${escapeHtml(recipient.inferenceUrl)}</a>` : "none"}</dd>
      </dl>` : "<p>No compensation output for this address.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Vote</h3>
      ${vote ? `<dl class="kv">
        <dt>Final vote</dt><dd>${escapeHtml(voteDisplayText(vote))}</dd>
        <dt>Vote block</dt><dd>${vote.height}<br><span class="muted">${escapeHtml(formatTime(vote.blockTime))}</span></dd>
        <dt>Tx hash</dt><dd class="mono">${escapeHtml(vote.txHash)}</dd>
        <dt>Voting power</dt><dd>${vote.votingPower == null ? "unknown" : fmt.format(vote.votingPower)}<br><span class="muted">${escapeHtml(vote.votingPowerReason || vote.votingPowerSource || "")}</span></dd>
        <dt>Start/end power</dt><dd>${windowPower ? `${fmt.format(windowPower.startVotingPower || 0)} -> ${fmt.format(windowPower.endVotingPower || 0)}<br><span class="muted">${escapeHtml(windowStatusLabel(windowPower.windowPowerStatus))}</span>` : "not in window snapshot"}</dd>
      </dl>` : "<p>No final on-chain vote in the saved proposal vote transactions.</p>"}
    </div>
    <div class="drawer-section">
      <h3>e287 Inference Timing Cluster</h3>
      ${entryExitClusters.length ? `<dl class="kv">${entryExitClusters.map((cluster) => {
        const item = (cluster.addressRows || []).find((row) => row.address === address) || {};
        const neighbors = (cluster.addresses || []).filter((itemAddress) => itemAddress !== address).slice(0, 8);
        return `<dt>#${cluster.rank} ${escapeHtml(cluster.kind)}</dt><dd>${escapeHtml(actorLabel(cluster))}<br>e287 inference weight ${fmt.format(item.e287Weight || 0)}, prev ${fmt.format(item.prevMaxWeight || 0)}, next ${fmt.format(item.nextMaxWeight || 0)}<br>exact governance voting power ${fmt.format(item.governanceVotingPower || 0)}<br>inference enter / governance vote tx in e287 / inference exit: ${item.enteredE287 ? "yes" : "no"} / ${item.votedDuringE287 ? "yes" : "no"} / ${item.exitedAfterE287 ? "yes" : "no"}<br>vote tx ${escapeHtml(voteDisplayText(item))} ${item.voteHeight ? `at ${item.voteHeight}` : ""}<br><span class="muted">Inference weight is not governance voting power. Neighbors: ${neighbors.length ? neighbors.map(escapeHtml).join(", ") : "none"}</span><br><span class="muted">${escapeHtml((cluster.caveats || []).join(" "))}</span></dd>`;
      }).join("")}</dl>` : "<p>No e287 inference timing cluster for this address.</p>"}
    </div>
    <div class="drawer-section">
      <h3>GNS Names</h3>
      ${gnsNames.length ? `<p>${gnsNames.map((item) => `<span class="tag">${escapeHtml(item.fullName)}</span>`).join(" ")}</p>` : "<p>No .gnk name found in the saved GNS snapshot.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Public Node Metadata</h3>
      <dl class="kv">
        <dt>Inference URL</dt><dd>${nodeInfo.inferenceUrl ? `<a href="${escapeHtml(nodeInfo.inferenceUrl)}">${escapeHtml(nodeInfo.inferenceUrl)}</a>` : "none"}</dd>
        <dt>Participant status</dt><dd>${escapeHtml(nodeInfo.status || "unknown")}</dd>
        <dt>Epochs completed</dt><dd>${escapeHtml(nodeInfo.epochsCompleted ?? "unknown")}</dd>
        <dt>Validator key</dt><dd class="mono">${escapeHtml(nodeInfo.validatorKey || "none")}</dd>
        <dt>Validator moniker</dt><dd>${escapeHtml(matchedValidator.moniker || "none")}</dd>
        <dt>Validator website</dt><dd>${matchedValidator.website ? `<a href="${escapeHtml(matchedValidator.website)}">${escapeHtml(matchedValidator.website)}</a>` : "none"}</dd>
        <dt>Validator identity</dt><dd>${escapeHtml(matchedValidator.identity || "none")}</dd>
        <dt>Security contact</dt><dd>${escapeHtml(matchedValidator.securityContact || "none")}</dd>
        <dt>Validator details</dt><dd>${escapeHtml(matchedValidator.details || "none")}</dd>
      </dl>
    </div>
    <div class="drawer-section">
      <h3>Clusters</h3>
      ${clusters.length ? `<dl class="kv">${clusters.map((cluster) => `<dt>${escapeHtml(cluster.id)}</dt><dd>${escapeHtml(actorLabel(cluster))} <span class="tag">${escapeHtml(cluster.kind)}</span> <span class="tag">${escapeHtml(cluster.weakestEvidence)}</span></dd>`).join("")}</dl>` : "<p>No multi-address cluster for this address.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Public Identity Evidence</h3>
      ${evidence.length ? `<dl class="kv">${evidence.map((row) => `<dt>${escapeHtml(row.sourceType)}</dt><dd>${escapeHtml(row.sourceValue)} <span class="tag">${escapeHtml(row.confidence)}</span></dd>`).join("")}</dl>` : "<p>Unknown public owner.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Evidence Claims</h3>
      ${evidenceClaims.length ? `<dl class="kv">${evidenceClaims.slice(0, 80).map(claimDetailHtml).join("")}</dl>` : "<p>No evidence claims for this address.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Evidence Graph Edges</h3>
      ${graphEdges.length ? `<dl class="kv">${graphEdges.map((edge) => `<dt>${escapeHtml(edge.sourceType)}</dt><dd>${escapeHtml(edge.sourceValue)} <span class="tag">${escapeHtml(edge.confidence)}</span> <span class="tag">${edge.isAttributionProof ? "proof" : "signal"}</span><br><span class="mono">${escapeHtml(edge.sourceFile)}</span></dd>`).join("")}</dl>` : "<p>No graph edges for this address.</p>"}
    </div>
  `;
  enhanceAddressActions(els.drawerContent);
  els.drawer.classList.add("open");
  els.scrim.classList.add("open");
  els.drawer.setAttribute("aria-hidden", "false");
}

function closeDrawer() {
  els.drawer.classList.remove("open");
  els.scrim.classList.remove("open");
  els.drawer.setAttribute("aria-hidden", "true");
}

ensureTableTitles();
initCollapsibleTables();

document.getElementById("closeDrawer").addEventListener("click", closeDrawer);
els.scrim.addEventListener("click", closeDrawer);

loadData().then((data) => {
  state.data = data;
  renderOverview(data);
  initCharts();
  setupFilters(data);
  applyFilters();
}).catch((error) => {
  document.body.innerHTML = `<main class="notes"><h1>Dashboard data failed to load</h1><p>${escapeHtml(error.message)}</p></main>`;
});
