const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });
const gonka = (value) => `${fmt.format(value)} GONKA`;
const optionLabels = { yes: "Yes", no: "No", abstain: "Abstain", no_with_veto: "No with veto", did_not_vote: "Did not vote" };
const optionColors = { yes: "#79b66a", no: "#d9655f", abstain: "#d7a84f", no_with_veto: "#8f7ad3", did_not_vote: "#6d7682" };

const state = {
  data: null,
  filteredRecipients: [],
  compensationView: "bar",
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
  rankedTable: document.getElementById("rankedTable"),
  evidenceTable: document.getElementById("evidenceTable"),
  hypothesisTable: document.getElementById("hypothesisTable"),
  anomalyTable: document.getElementById("anomalyTable"),
  entryExitTable: document.getElementById("entryExitTable"),
  telegramTable: document.getElementById("telegramTable"),
  labelTable: document.getElementById("labelTable"),
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

function primaryOption(vote) {
  return vote.finalVoteOptions.slice().sort((a, b) => b.weight - a.weight)[0]?.option || "unknown";
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
    timeline: "timelineChart",
    tally: "tallyChart",
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
}

function textMatch(row, query) {
  if (!query) return true;
  return [
    row.address,
    row.voter,
    row.label,
    row.inferenceUrl,
    row.txHash,
    row.status,
    row.identityType,
    row.strictClusterId,
    row.signalClusterId,
    ...(row.gnsNames || []).map((item) => item.fullName),
  ].filter(Boolean).join(" ").toLowerCase().includes(query);
}

function applyFilters() {
  const query = els.search.value.trim().toLowerCase();
  const label = els.label.value;
  state.filteredRecipients = state.data.recipients.filter((row) => {
    if (!textMatch(row, query)) return false;
    if (els.status.value !== "all" && row.status !== els.status.value) return false;
    if (els.vote.value !== "all" && row.voteOption !== els.vote.value) return false;
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
  document.getElementById("componentSplit").textContent = `${gonka(data.summary.visibleDamageE265Gonka)} visible e265 damage became ${gonka(data.summary.totalCompensationGonka)}`;
}

function renderCompensationChart() {
  const rows = state.filteredRecipients.slice(0, 30);
  if (state.compensationView === "tree") {
    state.charts.compensation.setOption({
      tooltip: { formatter: (p) => `${p.name}<br>${gonka(p.value)}` },
      series: [{
        type: "treemap",
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: { color: "#eef0f2", formatter: "{b}" },
        itemStyle: { borderColor: "#101114", borderWidth: 2 },
        data: state.filteredRecipients.map((row) => ({ name: row.label, value: row.totalGonka, address: row.address })),
      }],
    }, true);
    return;
  }
  state.charts.compensation.setOption({
    grid: { left: 150, right: 22, top: 20, bottom: 32 },
    tooltip: { trigger: "axis", formatter: (params) => `${params[0].name}<br>${gonka(params[0].value)}` },
    xAxis: { type: "value", axisLabel: { color: "#a7afba", formatter: (v) => compact.format(v) } },
    yAxis: { type: "category", data: rows.map((row) => `#${row.rank} ${row.label}`), axisLabel: { color: "#a7afba", width: 140, overflow: "truncate" } },
    series: [{ type: "bar", data: rows.map((row) => row.totalGonka), itemStyle: { color: "#4db7a8" } }],
  }, true);
}

function renderWaterfall() {
  const summary = state.data.summary;
  state.charts.waterfall.setOption({
    grid: { left: 62, right: 16, top: 28, bottom: 48 },
    tooltip: { trigger: "axis", formatter: (params) => `${params[0].name}<br>${gonka(params[0].value)}` },
    xAxis: { type: "category", data: ["e265-e266 attack", "e267-e276 cap", "Total"], axisLabel: { color: "#a7afba", interval: 0 } },
    yAxis: { type: "value", axisLabel: { color: "#a7afba", formatter: (v) => compact.format(v) } },
    series: [{ type: "bar", data: [summary.attackE265E266Gonka, summary.capE267E276Gonka, summary.totalCompensationGonka], itemStyle: { color: (p) => ["#d9655f", "#d7a84f", "#4db7a8"][p.dataIndex] } }],
  }, true);
}

function renderEpochChart() {
  const epochs = state.data.epochs || [];
  state.charts.epoch.setOption({
    grid: { left: 70, right: 20, top: 24, bottom: 44 },
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        const row = epochs[params[0].dataIndex];
        return `Epoch ${row.epoch}<br>${gonka(row.totalGonka)}<br>${row.recipientsCount} recipients`;
      },
    },
    xAxis: { type: "category", data: epochs.map((row) => `e${row.epoch}`), axisLabel: { color: "#a7afba" } },
    yAxis: { type: "value", axisLabel: { color: "#a7afba", formatter: (v) => compact.format(v) } },
    series: [{
      type: "bar",
      data: epochs.map((row) => row.totalGonka),
      itemStyle: { color: (p) => epochs[p.dataIndex]?.componentSource === "attack_e265_e266" ? "#d9655f" : "#d7a84f" },
    }],
  }, true);
}

function renderHeatmap() {
  const rows = state.filteredRecipients.slice(0, 30);
  const epochs = Array.from({ length: 12 }, (_, i) => `e${265 + i}`);
  const values = [];
  rows.forEach((row, y) => epochs.forEach((epoch, x) => values.push([x, y, row.perEpoch[epoch] || 0, row.address])));
  state.charts.heatmap.setOption({
    tooltip: { formatter: (p) => `${rows[p.value[1]].label}<br>${epochs[p.value[0]]}: ${gonka(p.value[2])}` },
    grid: { left: 150, right: 24, top: 24, bottom: 42 },
    xAxis: { type: "category", data: epochs, axisLabel: { color: "#a7afba" } },
    yAxis: { type: "category", data: rows.map((row) => `#${row.rank} ${row.label}`), axisLabel: { color: "#a7afba", width: 140, overflow: "truncate" } },
    visualMap: { min: 0, max: Math.max(...values.map((v) => v[2]), 1), calculable: true, orient: "horizontal", left: "center", bottom: 4, textStyle: { color: "#a7afba" }, inRange: { color: ["#222831", "#4db7a8", "#d7a84f"] } },
    series: [{ type: "heatmap", data: values }],
  }, true);
}

function renderMatrix() {
  const options = ["yes", "no", "abstain", "no_with_veto"];
  const groups = ["recipient", "non-recipient"];
  const counts = new Map();
  state.data.votes.forEach((vote) => counts.set(`${vote.isRecipient ? "recipient" : "non-recipient"}:${primaryOption(vote)}`, (counts.get(`${vote.isRecipient ? "recipient" : "non-recipient"}:${primaryOption(vote)}`) || 0) + 1));
  state.charts.matrix.setOption({
    tooltip: { formatter: (p) => `${groups[p.value[1]]} / ${optionLabels[options[p.value[0]]]}<br>${p.value[2]} voters` },
    grid: { left: 110, right: 20, top: 24, bottom: 42 },
    xAxis: { type: "category", data: options.map((item) => optionLabels[item]), axisLabel: { color: "#a7afba", interval: 0, rotate: 20 } },
    yAxis: { type: "category", data: groups, axisLabel: { color: "#a7afba" } },
    visualMap: { min: 0, max: 12, show: false, inRange: { color: ["#252a32", "#4db7a8"] } },
    series: [{ type: "heatmap", data: groups.flatMap((g, y) => options.map((o, x) => [x, y, counts.get(`${g}:${o}`) || 0])) }],
  }, true);
}

function renderTimeline() {
  const votes = state.data.votes;
  state.charts.timeline.setOption({
    grid: { left: 150, right: 42, top: 20, bottom: 42 },
    tooltip: { formatter: (p) => `${votes[p.dataIndex].label}<br>${optionLabels[votes[p.dataIndex].primaryOption]} at height ${votes[p.dataIndex].height}` },
    xAxis: { type: "value", axisLabel: { color: "#a7afba" }, name: "Block height", nameTextStyle: { color: "#a7afba" } },
    yAxis: { type: "category", data: votes.map((vote) => vote.label), axisLabel: { color: "#a7afba", width: 140, overflow: "truncate" } },
    series: [{ type: "scatter", symbolSize: 13, data: votes.map((vote, i) => [vote.height, i]), itemStyle: { color: (p) => optionColors[votes[p.dataIndex].primaryOption] } }],
  }, true);
}

function renderTally() {
  const tally = state.data.summary.finalTally;
  state.charts.tally.setOption({
    tooltip: { formatter: (p) => `${p.name}<br>${fmt.format(p.value)} voting power` },
    series: [{
      type: "pie",
      radius: ["45%", "72%"],
      label: { color: "#eef0f2", formatter: "{b}\n{d}%" },
      data: Object.entries(tally).map(([name, value]) => ({ name: optionLabels[name], value, itemStyle: { color: optionColors[name] } })),
    }],
  }, true);
}

function renderAttackTimeline() {
  const phases = state.data.attackNarrative?.phases || [];
  state.charts.attackTimeline.setOption({
    grid: { left: 40, right: 24, top: 28, bottom: 90 },
    tooltip: {
      formatter: (p) => {
        const row = phases[p.dataIndex];
        return `<strong>${escapeHtml(row.label)}</strong><br>${escapeHtml(row.timeOrHeight)}<br>${escapeHtml(row.summary)}`;
      },
    },
    xAxis: { type: "category", data: phases.map((row) => row.label), axisLabel: { color: "#a7afba", interval: 0, rotate: 25 } },
    yAxis: { type: "value", show: false, min: 0, max: 2 },
    series: [{
      type: "scatter",
      symbolSize: 22,
      data: phases.map((row, index) => [index, 1, row.confidence]),
      itemStyle: { color: (p) => phases[p.dataIndex]?.confidence === "high" ? "#79b66a" : "#d7a84f" },
      label: { show: true, formatter: (p) => phases[p.dataIndex]?.timeOrHeight || "", position: "top", color: "#eef0f2" },
    }],
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
    if (els.vote.value !== "all" && row.voteOption !== els.vote.value) return false;
    if (!query) return true;
    return [row.address, row.label, row.voteOption, row.status, row.caveat].join(" ").toLowerCase().includes(query);
  });
  document.getElementById("anomalyRows").textContent = `${rows.length} shown`;
  els.anomalyTable.innerHTML = rows.map((row) => `
    <tr>
      <td class="num">${fmt.format(row.anomalyScore)}</td>
      <td><button class="row-button mono" data-address="${row.address}">${escapeHtml(row.address)}</button></td>
      <td>${escapeHtml(row.label)}</td>
      <td class="num">${fmt.format(row.e287Weight)}</td>
      <td class="num">${fmt.format(row.prevMaxWeight)}</td>
      <td class="num">${fmt.format(row.nextMaxWeight)}</td>
      <td>${escapeHtml(optionLabels[row.voteOption] || row.voteOption)}${row.voteHeight ? `<br><span class="mono muted">${row.voteHeight}</span>` : ""}${row.voteBlockTime ? `<br><span class="muted">${escapeHtml(row.voteBlockTime)}</span>` : ""}</td>
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
  const rows = (state.data.epochEntryExitClusters || []).filter((row) => entryExitClusterMatches(row, query)).slice(0, 16);
  state.charts.entryExit.setOption({
    grid: { left: 170, right: 24, top: 24, bottom: 42 },
    tooltip: {
      formatter: (params) => {
        const row = rows[params.dataIndex];
        return `${escapeHtml(row.label)}<br>${escapeHtml(row.kind)}<br>e287 inference weight ${fmt.format(row.totalE287Weight)}<br>${row.confirmedEnterVoteExitCount} operational enter/vote/exit signals<br>Not governance voting power`;
      },
    },
    xAxis: { type: "value", axisLabel: { color: "#a7afba", formatter: (v) => compact.format(v) } },
    yAxis: { type: "category", data: rows.map((row) => `#${row.rank} ${row.label}`), axisLabel: { color: "#a7afba", width: 160, overflow: "truncate" } },
    series: [{
      type: "bar",
      data: rows.map((row) => row.totalE287Weight),
      itemStyle: { color: (p) => rows[p.dataIndex]?.kind === "strict_identity" ? "#79b66a" : rows[p.dataIndex]?.kind === "signal_cluster" ? "#d7a84f" : "#4db7a8" },
    }],
  }, true);
}

function renderEntryExitTable() {
  const query = els.search.value.trim().toLowerCase();
  const rows = (state.data.epochEntryExitClusters || []).filter((row) => entryExitClusterMatches(row, query));
  document.getElementById("entryExitRows").textContent = `${rows.length} shown`;
  els.entryExitTable.innerHTML = rows.map((row) => {
    const voteText = Object.entries(row.voteCounts || {}).map(([option, count]) => `${optionLabels[option] || option}: ${count}`).join("<br>") || "-";
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
        <td>${escapeHtml(row.label)}<br><span class="tag">${escapeHtml(row.kind)}</span><br><span class="mono muted">${escapeHtml(row.id)}</span></td>
        <td>${addressRows}</td>
        <td class="num">${fmt.format(row.totalE287Weight)}<br><span class="muted">max ${fmt.format(row.maxE287Weight)}; not gov power</span></td>
        <td>${row.enteredCount}/${row.votedDuringCount}/${row.exitedCount}<br><span class="muted">${row.confirmedEnterVoteExitCount} operational full path</span></td>
        <td>${voteText}</td>
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
      <td>${escapeHtml(row.label)}<br><span class="muted">${escapeHtml(row.identityTypes.join(", "))}</span></td>
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

function renderActorGraph() {
  const ranked = (state.data.rankedParties || []).slice(0, 25);
  const claims = state.data.evidenceClaims || [];
  const nodes = [];
  const links = [];
  const seen = new Set();
  const addNode = (id, name, category, value = 10) => {
    if (seen.has(id)) return;
    seen.add(id);
    nodes.push({ id, name, category, value, symbolSize: Math.max(12, Math.min(46, value)) });
  };
  ranked.forEach((party) => {
    addNode(party.id, `#${party.rank} ${party.label}`, "party", 18 + party.overallPriority / 3);
    party.addresses.forEach((address) => {
      const addressId = `address:${address}`;
      addNode(addressId, address, "address", 14);
      links.push({ source: party.id, target: addressId, value: "contains" });
      claims.filter((claim) => claim.address === address).slice(0, 5).forEach((claim) => {
        const claimId = `${claim.sourceType}:${claim.sourceValue}`.slice(0, 180);
        addNode(claimId, claim.sourceValue || claim.sourceType, claim.isAttributionProof ? "proof" : "signal", claim.isAttributionProof ? 18 : 11);
        links.push({ source: addressId, target: claimId, value: claim.sourceType });
      });
    });
  });
  state.charts.actorGraph.setOption({
    tooltip: { formatter: (p) => p.dataType === "edge" ? `${p.data.source}<br>${escapeHtml(p.data.value)}<br>${p.data.target}` : escapeHtml(p.data.name) },
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
  const rows = [
    ["Governance vote", method.governanceVoteRule],
    ["Governance voting power", method.governanceVotingPowerRule],
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
    item.votes.add(row.primaryOption || primaryOption(row));
  });

  return [...labels.values()]
    .map((row) => ({
      ...row,
      addresses: [...row.addresses].sort(),
      identityTypes: [...row.identityTypes].sort(),
      votes: [...row.votes].sort(),
    }))
    .sort((a, b) => b.totalGonka - a.totalGonka || b.addresses.length - a.addresses.length || a.label.localeCompare(b.label));
}

function renderLabelTable() {
  const query = els.search.value.trim().toLowerCase();
  const selectedLabel = els.label.value;
  const rows = buildLabelRows(state.data).filter((row) => {
    if (selectedLabel !== "all" && row.label !== selectedLabel) return false;
    if (els.identity.value !== "all" && !row.identityTypes.includes(els.identity.value)) return false;
    if (els.vote.value !== "all" && !row.votes.includes(els.vote.value) && !(els.vote.value === "did_not_vote" && row.recipientCount > row.voterCount)) return false;
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
      <td>${escapeHtml(row.label)}</td>
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
      <td>${escapeHtml(row.label)}</td>
      <td><span class="tag">${escapeHtml(row.status)}</span></td>
      <td>${escapeHtml(optionLabels[row.voteOption] || row.voteOption)}</td>
      <td>${escapeHtml(row.strictClusterId || row.signalClusterId || "-")}</td>
      <td class="num">${gonka(row.totalGonka)}</td>
    </tr>
  `).join("");

  const query = els.search.value.trim().toLowerCase();
  const label = els.label.value;
  const filteredVotes = state.data.votes.filter((row) => {
    if (!textMatch({ ...row, address: row.voter }, query)) return false;
    if (els.vote.value !== "all" && row.primaryOption !== els.vote.value) return false;
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
      <td>${escapeHtml(row.finalVoteOptions.map((item) => `${optionLabels[item.option]} ${fmt.format(item.weight * 100)}%`).join(", "))}</td>
      <td>${escapeHtml(row.strictClusterId || row.signalClusterId || "-")}</td>
      <td>unknown</td>
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
      <td>${escapeHtml(cluster.label)}</td>
      <td>${cluster.addresses.map((address) => `<button class="row-button mono" data-address="${address}">${escapeHtml(address)}</button>`).join("<br>")}</td>
      <td class="num">${cluster.recipientCount}</td>
      <td class="num">${cluster.voterCount}</td>
      <td class="num">${gonka(cluster.totalCompensationGonka)}</td>
    </tr>
  `).join("");
  els.signalClusterTable.innerHTML = signal.map((cluster) => `
    <tr>
      <td>${escapeHtml(cluster.id)}</td>
      <td>${escapeHtml(cluster.label)}</td>
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
  renderActorGraph();
  renderEntryExitChart();
  renderHypotheses();
  renderAnomalyTable();
  renderEntryExitTable();
  renderTelegramTable();
  renderRankedTable();
  renderEvidenceTable();
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
        <dt>Final vote</dt><dd>${escapeHtml(vote.finalVoteOptions.map((item) => `${optionLabels[item.option]} ${fmt.format(item.weight * 100)}%`).join(", "))}</dd>
        <dt>Height</dt><dd>${vote.height}</dd>
        <dt>Tx hash</dt><dd class="mono">${escapeHtml(vote.txHash)}</dd>
        <dt>Voting power</dt><dd>unknown</dd>
      </dl>` : "<p>No final on-chain vote in the saved proposal vote transactions.</p>"}
    </div>
    <div class="drawer-section">
      <h3>e287 Inference Timing Cluster</h3>
      ${entryExitClusters.length ? `<dl class="kv">${entryExitClusters.map((cluster) => {
        const item = (cluster.addressRows || []).find((row) => row.address === address) || {};
        const neighbors = (cluster.addresses || []).filter((itemAddress) => itemAddress !== address).slice(0, 8);
        return `<dt>#${cluster.rank} ${escapeHtml(cluster.kind)}</dt><dd>${escapeHtml(cluster.label)}<br>e287 inference weight ${fmt.format(item.e287Weight || 0)}, prev ${fmt.format(item.prevMaxWeight || 0)}, next ${fmt.format(item.nextMaxWeight || 0)}<br>inference enter / governance vote tx in e287 / inference exit: ${item.enteredE287 ? "yes" : "no"} / ${item.votedDuringE287 ? "yes" : "no"} / ${item.exitedAfterE287 ? "yes" : "no"}<br>vote tx ${escapeHtml(optionLabels[item.voteOption] || item.voteOption || "none")} ${item.voteHeight ? `at ${item.voteHeight}` : ""}<br><span class="muted">Inference weight is not governance voting power. Neighbors: ${neighbors.length ? neighbors.map(escapeHtml).join(", ") : "none"}</span><br><span class="muted">${escapeHtml((cluster.caveats || []).join(" "))}</span></dd>`;
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
      ${clusters.length ? `<dl class="kv">${clusters.map((cluster) => `<dt>${escapeHtml(cluster.id)}</dt><dd>${escapeHtml(cluster.label)} <span class="tag">${escapeHtml(cluster.kind)}</span> <span class="tag">${escapeHtml(cluster.weakestEvidence)}</span></dd>`).join("")}</dl>` : "<p>No multi-address cluster for this address.</p>"}
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
