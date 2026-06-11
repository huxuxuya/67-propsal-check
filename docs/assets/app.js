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
  charts: {},
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
  evidenceTable: document.getElementById("evidenceTable"),
  hypothesisTable: document.getElementById("hypothesisTable"),
  anomalyTable: document.getElementById("anomalyTable"),
  entryExitTable: document.getElementById("entryExitTable"),
  telegramTable: document.getElementById("telegramTable"),
  labelTable: document.getElementById("labelTable"),
  searchIndex: document.getElementById("searchIndex"),
  epochTable: document.getElementById("epochTable"),
  recipientTable: document.getElementById("recipientTable"),
  voteTable: document.getElementById("voteTable"),
  strictClusterTable: document.getElementById("strictClusterTable"),
  signalClusterTable: document.getElementById("signalClusterTable"),
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

function formatTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
}

function chartTooltip(options = {}) {
  return {
    appendToBody: true,
    confine: false,
    renderMode: "html",
    extraCssText: "max-width:min(440px, calc(100vw - 32px));white-space:normal;overflow-wrap:anywhere;z-index:9999;",
    ...options,
  };
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
    heatmap: "heatmapChart",
    matrix: "matrixChart",
    matrixStats: "matrixStats",
    timeline: "timelineChart",
    tally: "tallyChart",
    voterPower: "voterPowerChart",
    windowPower: "windowPowerChart",
    actorGraph: "actorGraphChart",
    entryExit: "entryExitChart",
  })) {
    state.charts[key] = echarts.init(document.getElementById(id));
  }
  window.addEventListener("resize", () => Object.values(state.charts).forEach((chart) => chart.resize()));
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
}

function textMatch(row, query) {
  if (!query) return true;
  return [
    row.address,
    row.voter,
    actorLabel(row),
    actorShortLabel(row),
    row.publicName,
    row.inferenceUrl,
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
        totalGonka: 0,
        votingPower: 0,
      });
    }
    return rows.get(normalized);
  };
  const addLabel = (row, value) => {
    if (value) row.labels.add(value);
  };

  (data.recipients || []).forEach((item) => {
    const row = ensure(item.address);
    if (!row) return;
    row.roles.add("recipient");
    row.sources.add("recipients");
    addLabel(row, actorLabel(item));
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
    row.votes.add(voteDisplayText(item));
    row.votingPower = Math.max(row.votingPower, item.votingPower || 0);
  });

  (data.actors || []).forEach((item) => {
    const row = ensure(item.address);
    if (!row) return;
    row.sources.add("actors");
    (item.roles || []).forEach((role) => row.roles.add(role));
    addLabel(row, actorLabel(item));
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
    });
  });

  (data.identityEvidence || []).forEach((item) => {
    const row = ensure(item.address);
    if (!row) return;
    row.sources.add(item.sourceType || "identity evidence");
    addLabel(row, item.publicLabel || item.sourceValue);
  });

  (data.evidenceClaims || []).forEach((item) => {
    const row = ensure(item.address);
    if (!row) return;
    row.sources.add(item.sourceType || "evidence claim");
    addLabel(row, item.subject || item.sourceValue);
  });

  (data.identityGraph?.edges || []).forEach((edge) => {
    [edge.source, edge.target].forEach((value) => {
      const address = String(value || "").startsWith("address:") ? String(value).slice(8) : "";
      const row = ensure(address);
      if (!row) return;
      row.sources.add(edge.sourceType || "graph edge");
      addLabel(row, edge.sourceValue || edge.target);
    });
  });

  (data.telegramEvidence || []).forEach((item) => {
    (item.addresses || []).forEach((address) => {
      const row = ensure(address);
      if (!row) return;
      row.sources.add("telegram evidence");
      addLabel(row, item.author || item.chat);
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
    ].join(" ").toLowerCase().includes(query);
  });
  document.getElementById("searchIndexRows").textContent = `${rows.length} searchable addresses`;
  els.searchIndex.innerHTML = rows.map((row) => `
    <div class="search-index-row">
      <span class="mono search-index-address">${escapeHtml(row.address)}</span>
      <span class="search-index-meta">${escapeHtml([...row.labels].filter(Boolean).slice(0, 3).join(" | ") || "Unknown public owner")}</span>
      <span class="search-index-tags">${[...row.roles].sort().map((role) => `<span class="tag">${escapeHtml(role)}</span>`).join(" ")}</span>
      <span class="search-index-stats">${row.totalGonka ? gonka(row.totalGonka) : ""}${row.votingPower ? ` · power ${fmt.format(row.votingPower)}` : ""}</span>
      <button class="row-button search-index-open" data-address="${escapeHtml(row.address)}">Open</button>
    </div>
  `).join("");
  els.searchIndex.querySelectorAll("[data-address]").forEach((button) => {
    button.addEventListener("click", () => openDrawer(button.dataset.address));
  });
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
  document.getElementById("multiplier").textContent = `${fmt.format(data.summary.visibleDamageToFinalMultiplier)}x`;
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
  const attackEpoch = epochById.get(265)?.totalGonka || summary.visibleDamageE265Gonka || 0;
  const excludedEpoch = epochById.get(266)?.totalGonka || Math.max(0, (summary.attackE265E266Gonka || 0) - attackEpoch);
  const capEpochs = (state.data.epochs || [])
    .filter((row) => row.epoch >= 267 && row.epoch <= 276)
    .reduce((total, row) => total + (row.totalGonka || 0), 0) || summary.capE267E276Gonka || 0;
  const components = [
    { name: "e265 attack", value: attackEpoch, color: "#d9655f", description: "Epoch 265: direct attack/damage epoch" },
    { name: "e266 could not enter", value: excludedEpoch, color: "#e78f61", description: "Epoch 266: attacked participants could not enter the next epoch" },
    { name: "e267-e276 cap", value: capEpochs, color: "#d7a84f", description: "Epochs 267-276: capped compensation window after the attack impact" },
  ];
  state.charts.waterfall.setOption({
    grid: { left: 70, right: 24, top: 28, bottom: 72 },
    tooltip: chartTooltip({
      trigger: "item",
      formatter: (p) => {
        const total = summary.totalCompensationGonka || 1;
        const row = components[p.dataIndex] || {};
        return `<strong>${escapeHtml(row.name || p.name)}</strong><br>${escapeHtml(row.description || "")}<br>${gonka(row.value || 0)}<br>${fmt.format(((row.value || 0) / total) * 100)}% of final payout<br>final total ${gonka(summary.totalCompensationGonka || 0)}`;
      },
    }),
    xAxis: { type: "category", data: components.map((row) => row.name), axisLabel: { color: "#a7afba", interval: 0, rotate: 18 } },
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

function renderTelegramTable() {
  const query = els.search.value.trim().toLowerCase();
  const rows = (state.data.telegramEvidence || []).filter((row) => {
    if (!query) return true;
    return [
      row.chat,
      row.messageId,
      row.date,
      row.author,
      row.excerpt,
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
      <td>${escapeHtml(row.author || "-")}</td>
      <td>${(row.addresses || []).map((address) => `<button class="row-button mono" data-address="${address.replace("gonkavaloper", "gonka")}">${escapeHtml(address)}</button>`).join("<br>")}</td>
      <td>${escapeHtml(row.excerpt || "")}</td>
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
      <td>${escapeHtml(actorLabel(row))}<br><span class="muted">${escapeHtml(row.identityTypes.join(", "))}</span></td>
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
      <td>${escapeHtml(row.sourceType)}<br><span class="mono muted">${escapeHtml(row.sourceUrl)}</span></td>
      <td>${escapeHtml(row.sourceValue)}</td>
      <td><span class="tag ${row.isAttributionProof ? "good" : ""}">${row.isAttributionProof ? "proof" : "signal"}</span> <span class="tag">${escapeHtml(row.confidence)}</span></td>
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
      <td>${escapeHtml(actorLabel(row))}<br><span class="muted">${escapeHtml(row.clusterId || "no cluster")}</span></td>
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
      <td>${escapeHtml(actorLabel(row))}</td>
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
      });
    }
    return labels.get(label);
  };

  data.recipients.forEach((row) => {
    const item = ensure(row.label || "Unknown public owner");
    item.addresses.add(row.address);
    item.identityTypes.add(row.identityType || "unknown");
    item.recipientCount += 1;
    item.totalGonka += row.totalGonka || 0;
  });

  data.votes.forEach((row) => {
    const item = ensure(row.label || "Unknown public owner");
    item.addresses.add(row.voter);
    item.identityTypes.add(row.identityType || "unknown");
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
      ...row.identityTypes,
      ...row.addresses,
      ...row.votes,
    ].join(" ").toLowerCase().includes(query);
  });

  document.getElementById("labelRows").textContent = `${rows.length} shown`;
  els.labelTable.innerHTML = rows.map((row) => `
    <tr>
      <td>${escapeHtml(actorLabel(row))}</td>
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
      <td>${escapeHtml(actorLabel(row))}</td>
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
      <td><button class="row-button mono" data-address="${row.voter}">${escapeHtml(row.voter)}</button></td>
      <td>${row.isRecipient ? "Yes" : "No"}</td>
      <td>${voteDisplayHtml(row)}</td>
      <td>${escapeHtml(row.strictClusterId || row.signalClusterId || "-")}</td>
      <td>${row.votingPower == null ? "unknown" : fmt.format(row.votingPower)}<br><span class="muted">${escapeHtml(row.votingPowerReason || row.votingPowerSource || "")}</span><br><span class="muted">${escapeHtml(formatTime(row.blockTime))}</span></td>
    </tr>
  `).join("");

  document.querySelectorAll("[data-address]").forEach((button) => {
    button.addEventListener("click", () => openDrawer(button.dataset.address));
  });
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
  renderHeatmap();
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
  document.querySelectorAll("[data-address]").forEach((button) => {
    button.addEventListener("click", () => openDrawer(button.dataset.address));
  });
}

function openDrawer(address) {
  const recipient = state.data.recipients.find((row) => row.address === address);
  const vote = state.data.votes.find((row) => row.voter === address);
  const evidence = state.data.identityEvidence.filter((row) => row.address === address);
  const evidenceClaims = (state.data.evidenceClaims || []).filter((row) => row.address === address);
  const actor = (state.data.actors || []).find((row) => row.address === address);
  const rankedParty = (state.data.rankedParties || []).find((row) => (row.addresses || []).includes(address));
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
    <p class="mono">${escapeHtml(address)}</p>
    <div class="drawer-section">
      <h3>Actor Priority</h3>
      ${actor ? `<dl class="kv">
        <dt>Roles</dt><dd>${actor.roles.map((role) => `<span class="tag">${escapeHtml(role)}</span>`).join(" ")}</dd>
        <dt>Ranked party</dt><dd>${rankedParty ? `#${rankedParty.rank} ${escapeHtml(rankedParty.label)}` : "not ranked"}</dd>
        <dt>Priority</dt><dd>${rankedParty ? fmt.format(rankedParty.overallPriority) : "none"}</dd>
        <dt>Confidence</dt><dd>${rankedParty ? escapeHtml(rankedParty.confidence) : "none"}</dd>
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
      ${evidenceClaims.length ? `<dl class="kv">${evidenceClaims.slice(0, 80).map((row) => `<dt>${escapeHtml(row.sourceType)}</dt><dd>${escapeHtml(row.sourceValue)} <span class="tag">${escapeHtml(row.confidence)}</span> <span class="tag">${row.isAttributionProof ? "proof" : "signal"}</span><br><span class="muted">${escapeHtml(row.caveat || "")}</span></dd>`).join("")}</dl>` : "<p>No evidence claims for this address.</p>"}
    </div>
    <div class="drawer-section">
      <h3>Evidence Graph Edges</h3>
      ${graphEdges.length ? `<dl class="kv">${graphEdges.map((edge) => `<dt>${escapeHtml(edge.sourceType)}</dt><dd>${escapeHtml(edge.sourceValue)} <span class="tag">${escapeHtml(edge.confidence)}</span> <span class="tag">${edge.isAttributionProof ? "proof" : "signal"}</span><br><span class="mono">${escapeHtml(edge.sourceFile)}</span></dd>`).join("")}</dl>` : "<p>No graph edges for this address.</p>"}
    </div>
  `;
  els.drawer.classList.add("open");
  els.scrim.classList.add("open");
  els.drawer.setAttribute("aria-hidden", "false");
}

function closeDrawer() {
  els.drawer.classList.remove("open");
  els.scrim.classList.remove("open");
  els.drawer.setAttribute("aria-hidden", "true");
}

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
