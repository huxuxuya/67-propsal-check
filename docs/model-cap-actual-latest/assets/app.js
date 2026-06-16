const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const fmt1 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
const fmt3 = new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 });
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 });

const data = window.modelCapActualData || {};
const allRows = Array.isArray(data.rows) ? data.rows : [];
const summary = data.summary || {};

const rows = allRows
  .filter((row) => row && Number.isFinite(Number(row.epoch)))
  .map((row) => ({ ...row, epoch: Number(row.epoch), isForecast: false }))
  .sort((a, b) => a.epoch - b.epoch || String(a.modelLabel || "").localeCompare(String(b.modelLabel || "")));

const uniq = (values) => [...new Set(values.filter(Boolean))];
const modelName = (row) => row?.modelLabel || row?.modelId || "Unknown";
const epochLabel = (epoch, forecast = false) => `e${epoch}${forecast ? " forecast" : ""}`;
const withCommas = (value) => fmt.format(Number(value || 0));
const pct = (value) => `${fmt1.format(Number(value || 0))}%`;
const scaleText = (value) => `${fmt3.format(Number(value || 0))}x`;

const epochListAll = uniq(rows.map((row) => row.epoch)).sort((a, b) => a - b);
const epochWindow = epochListAll.slice(Math.max(0, epochListAll.length - 3));
const actualRows = rows.filter((row) => epochWindow.includes(row.epoch));
const modelList = uniq(actualRows.map(modelName)).sort();

const latestEpoch = epochWindow[epochWindow.length - 1] || Number(summary.latestEpoch || summary.latestCompletedEpoch || 0);
const latestRows = actualRows.filter((row) => row.epoch === latestEpoch);
const latestReference = latestRows[0] || {};
const latestRootTotal = Number(latestReference.rootTotalWeight || 0);
const capFactor = Number(latestReference.capFactor || 0.75);
const nextEpoch = latestEpoch ? latestEpoch + 1 : 0;
const nextCapLimit = latestRootTotal ? Math.floor(latestRootTotal * capFactor) : 0;

const forecastRows = (Array.isArray(data.forecastRows) && data.forecastRows.length ? data.forecastRows : latestRows.map((row) => {
  const requested = Number(row.rawConsensusWeight || 0);
  const capApplies = row.capApplies !== false && !row.initialModel;
  const counted = capApplies && nextCapLimit ? Math.min(requested, nextCapLimit) : requested;
  return {
    ...row,
    epoch: nextEpoch,
    isForecast: true,
    previousEpochRootTotalWeight: latestRootTotal,
    rootTotalWeight: null,
    capWeight: capApplies ? nextCapLimit : null,
    capLimitFromPreviousEpoch: capApplies ? nextCapLimit : null,
    countedWeight: counted,
    cappedConsensusWeight: counted,
    clippedWeight: capApplies ? Math.max(0, requested - counted) : 0,
    capHeadroom: capApplies ? Math.max(0, nextCapLimit - requested) : null,
    capUtilization: capApplies && nextCapLimit ? requested / nextCapLimit : null,
    pressureRatio: capApplies && nextCapLimit ? requested / nextCapLimit : null,
    status: capApplies && nextCapLimit && requested > nextCapLimit ? "forecast_capped" : capApplies ? "forecast_under_cap" : "initial_exempt",
  };
})).filter((row) => row && row.epoch);

const analysisRows = [...actualRows, ...forecastRows];
const analysisEpochs = [...epochWindow, ...(nextEpoch ? [nextEpoch] : [])];
const rowsByEpochModel = new Map(analysisRows.map((row) => [`${row.epoch}|${modelName(row)}`, row]));

const colorForModel = (model) => {
  const palette = {
    Kimi: "#49a078",
    MiniMax: "#c9853f",
    Qwen: "#4f8bc9",
  };
  return palette[model] || ["#7f9c96", "#d5a253", "#8a9fb7"][Math.max(0, modelList.indexOf(model)) % 3];
};

const els = {
  modelSelect: document.getElementById("modelSelect"),
  summaryText: document.getElementById("summaryText"),
  windowText: document.getElementById("windowText"),
  sourceText: document.getElementById("sourceText"),
  rowsText: document.getElementById("rowsText"),
  fallbackText: document.getElementById("fallbackText"),
  kpiStrip: document.getElementById("kpiStrip"),
  cappedEvents: document.getElementById("cappedEvents"),
  modelOverview: document.getElementById("modelOverview"),
  tableStatus: document.getElementById("tableStatus"),
  tableBody: document.getElementById("rowsTable"),
  paramTable: document.getElementById("paramTable"),
};

const charts = typeof echarts === "undefined" ? {} : {
  path: echarts.init(document.getElementById("capPathChart")),
  denominator: echarts.init(document.getElementById("denominatorChart")),
  pressure: echarts.init(document.getElementById("pressureMatrixChart")),
  params: echarts.init(document.getElementById("paramsTimelineChart")),
};

const statusLabel = (status) => {
  const map = {
    under_cap: "under cap",
    capped: "capped",
    initial_exempt: "initial exempt",
    sole_group_uncapped: "sole group",
    cap_reference_missing: "cap basis missing",
    missing_subgroup: "missing subgroup",
    forecast_capped: "forecast capped",
    forecast_under_cap: "forecast under cap",
  };
  return map[String(status || "").toLowerCase()] || String(status || "ok");
};

const statusClass = (status) => {
  const value = String(status || "").toLowerCase();
  if (value.includes("capped") && !value.includes("under")) return "status-chip bad";
  if (value.includes("forecast")) return "status-chip warn";
  if (value.includes("under") || value.includes("exempt")) return "status-chip good";
  return "status-chip";
};

const chartTooltip = (formatter) => ({
  trigger: "axis",
  confine: true,
  backgroundColor: "rgba(10, 19, 31, 0.95)",
  borderColor: "#334e76",
  textStyle: { color: "#dbe5f1", fontSize: 12 },
  formatter,
});

const defaultModel = () => {
  const latestCapped = actualRows.find((row) => row.epoch === latestEpoch && Number(row.clippedWeight || 0) > 0);
  const anyCapped = actualRows.find((row) => Number(row.clippedWeight || 0) > 0);
  return modelName(latestCapped || anyCapped) || (modelList.includes("Kimi") ? "Kimi" : modelList[0] || "all");
};

const selectedModel = () => els.modelSelect?.value || defaultModel();

const modelRows = (model) => analysisEpochs
  .map((epoch) => rowsByEpochModel.get(`${epoch}|${model}`))
  .filter(Boolean);

const capAppliedModels = () => modelList.filter((model) => actualRows.some((row) => modelName(row) === model && row.capApplies !== false && !row.initialModel));

const setNoData = () => {
  if (els.summaryText) els.summaryText.textContent = "No model cap data loaded";
};

const renderSummary = () => {
  if (!actualRows.length) return setNoData();
  const clipped = actualRows.reduce((sum, row) => sum + Number(row.clippedWeight || 0), 0);
  const capped = actualRows.filter((row) => Number(row.clippedWeight || 0) > 0).length;
  const snapshotHeight = Number(summary.latestBlockHeight || latestReference.height || 0);
  if (els.summaryText) els.summaryText.textContent = "Actual chain model-cap mechanics";
  if (els.windowText) els.windowText.textContent = `${epochLabel(epochWindow[0])}-${epochLabel(latestEpoch)} + ${epochLabel(nextEpoch, true)}`;
  if (els.sourceText) els.sourceText.textContent = `${data.source?.rpcNode || "GONKA_RPC_URL"} · snapshot height ${withCommas(snapshotHeight)}`;
  if (els.rowsText) els.rowsText.textContent = `${actualRows.length} actual rows · ${forecastRows.length} forecast rows`;
  if (els.fallbackText) els.fallbackText.textContent = summary.statusCatchingUp ? "RPC is catching up; current values are provisional." : "";
  if (!els.kpiStrip) return;
  const initial = latestRows.find((row) => row.initialModel)?.modelLabel || latestRows.find((row) => row.initialModel)?.modelId || "n/a";
  els.kpiStrip.innerHTML = [
    ["Current root total", withCommas(latestRootTotal), `basis for ${epochLabel(nextEpoch)} cap`],
    ["Next cap limit", withCommas(nextCapLimit), `${withCommas(latestRootTotal)} x ${scaleText(capFactor)}`],
    ["Capped rows", withCommas(capped), `${withCommas(clipped)} clipped weight`],
    ["Initial model", initial, "cap exempt"],
    ["Cap factor", scaleText(capFactor), "network parameter"],
  ].map(([label, value, note]) => `
    <div class="kpi">
      <span>${label}</span>
      <strong>${value}</strong>
      <em>${note}</em>
    </div>
  `).join("");
  if (!els.cappedEvents) return;
  const cappedRows = actualRows
    .filter((row) => Number(row.clippedWeight || 0) > 0)
    .sort((a, b) => b.epoch - a.epoch || Number(b.clippedWeight || 0) - Number(a.clippedWeight || 0));
  els.cappedEvents.innerHTML = cappedRows.length
    ? cappedRows.map((row) => `
      <div class="event-card bad">
        <span>${epochLabel(row.epoch)} capped</span>
        <strong>${modelName(row)}</strong>
        <em>${withCommas(row.rawConsensusWeight || 0)} requested -> ${withCommas(row.countedWeight || row.cappedConsensusWeight || 0)} counted, ${withCommas(row.clippedWeight || 0)} clipped</em>
      </div>
    `).join("")
    : `
      <div class="event-card good">
        <span>No capped rows</span>
        <strong>Latest 3 epochs under cap</strong>
        <em>All cap-applied models stayed below their cap limit.</em>
      </div>
    `;
  if (!els.modelOverview) return;
  els.modelOverview.innerHTML = modelList.map((model) => {
    const row = rowsByEpochModel.get(`${latestEpoch}|${model}`);
    if (!row) return "";
    const requested = Number(row.rawConsensusWeight || 0);
    const counted = Number(row.countedWeight ?? row.cappedConsensusWeight ?? requested);
    const clipped = Number(row.clippedWeight || 0);
    const share = latestRootTotal ? (counted / latestRootTotal) * 100 : 0;
    return `
      <div class="model-card ${clipped > 0 ? "bad" : row.initialModel ? "exempt" : "good"}">
        <span>${epochLabel(latestEpoch)} ${row.initialModel ? "initial exempt" : clipped > 0 ? "capped" : "under cap"}</span>
        <strong>${model}</strong>
        <em>requested ${withCommas(requested)} · counted ${withCommas(counted)} · ${pct(share)} of root</em>
        <em>${row.capWeight == null ? "cap exempt" : `cap ${withCommas(row.capWeight)} · clipped ${withCommas(clipped)}`}</em>
      </div>
    `;
  }).join("");
};

const renderOptions = () => {
  if (!els.modelSelect) return;
  const preferred = defaultModel();
  els.modelSelect.innerHTML = `<option value="all">All models</option>${modelList.map((model) => `<option value="${model}">${model}</option>`).join("")}`;
  els.modelSelect.value = preferred;
};

const renderCapPath = () => {
  const model = selectedModel();
  if (model === "all") {
    renderAllModelsCapPath();
    return;
  }
  const chartRows = modelRows(model);
  if (!charts.path || !chartRows.length) return;
  const labels = chartRows.map((row) => epochLabel(row.epoch, row.isForecast));
  charts.path.setOption({
    grid: { left: 78, right: 30, top: 48, bottom: 70 },
    legend: { top: 8, textStyle: { color: "#9aa8b9" } },
    tooltip: chartTooltip((params) => {
      const row = chartRows[params[0]?.dataIndex];
      if (!row) return "";
      const requested = Number(row.rawConsensusWeight || 0);
      const cap = row.capWeight == null ? null : Number(row.capWeight || 0);
      const counted = Number(row.countedWeight ?? row.cappedConsensusWeight ?? requested);
      const basis = Number(row.previousEpochRootTotalWeight || 0);
      return [
        `<strong>${epochLabel(row.epoch, row.isForecast)} ${model}</strong>`,
        row.isForecast ? "Forecast: assumes latest requested weight repeats." : "Actual chain row.",
        `raw subgroup: <strong>${withCommas(row.subgroupRawWeight)}</strong>`,
        `requested = raw x scale: <strong>${withCommas(requested)}</strong> = ${withCommas(row.subgroupRawWeight)} x ${scaleText(row.weightScaleFactor)}`,
        row.capApplies === false || row.initialModel ? "cap: initial/exempt model" : `cap = previous root x factor: <strong>${withCommas(cap)}</strong> = ${withCommas(basis)} x ${scaleText(row.capFactor)}`,
        `counted: <strong>${withCommas(counted)}</strong>`,
        `clipped: <strong>${withCommas(row.clippedWeight || 0)}</strong>`,
        row.capHeadroom != null ? `headroom: <strong>${withCommas(row.capHeadroom)}</strong>` : "",
        `status: ${statusLabel(row.status)}`,
      ].filter(Boolean).join("<br>");
    }),
    xAxis: { type: "category", data: labels, axisLabel: { color: "#9aa8b9", interval: 0 } },
    yAxis: { type: "value", name: "weight", nameTextStyle: { color: "#9aa8b9" }, axisLabel: { color: "#9aa8b9", formatter: (value) => compact.format(value) } },
    series: [
      {
        name: "Raw subgroup",
        type: "line",
        data: chartRows.map((row) => row.subgroupRawWeight || 0),
        symbol: "circle",
        lineStyle: { color: "#7d8a96", width: 2, type: "dotted" },
        itemStyle: { color: "#7d8a96" },
      },
      {
        name: "Requested after scale",
        type: "line",
        data: chartRows.map((row) => row.rawConsensusWeight || 0),
        symbol: "circle",
        lineStyle: { color: "#d9655f", width: 3 },
        itemStyle: { color: "#d9655f" },
      },
      {
        name: "Cap limit",
        type: "line",
        data: chartRows.map((row) => row.capWeight == null ? null : row.capWeight),
        symbol: "circle",
        lineStyle: { color: "#d7a84f", width: 2.5, type: "dashed" },
        itemStyle: { color: "#d7a84f" },
      },
      {
        name: "Counted",
        type: "bar",
        stack: "final",
        data: chartRows.map((row) => row.countedWeight ?? row.cappedConsensusWeight ?? row.rawConsensusWeight ?? 0),
        barMaxWidth: 34,
        itemStyle: { color: colorForModel(model), opacity: 0.86 },
      },
      {
        name: "Clipped",
        type: "bar",
        stack: "final",
        data: chartRows.map((row) => row.clippedWeight || 0),
        barMaxWidth: 34,
        itemStyle: { color: "#c7504f", opacity: 0.72 },
      },
      {
        name: "Cap basis",
        type: "line",
        data: chartRows.map((row) => row.previousEpochRootTotalWeight || null),
        symbol: "triangle",
        lineStyle: { color: "#4f8bc9", width: 2, type: "dotted" },
        itemStyle: { color: "#4f8bc9" },
      },
    ],
  }, true);
};

const renderAllModelsCapPath = () => {
  if (!charts.path) return;
  const labels = analysisEpochs.map((epoch) => epochLabel(epoch, epoch === nextEpoch));
  const selectedModels = modelList;
  const series = [];
  for (const model of selectedModels) {
    const color = colorForModel(model);
    series.push({
      name: `${model} requested`,
      type: "line",
      data: analysisEpochs.map((epoch) => rowsByEpochModel.get(`${epoch}|${model}`)?.rawConsensusWeight ?? null),
      symbol: "circle",
      lineStyle: { color, width: 2.5 },
      itemStyle: { color },
    });
    series.push({
      name: `${model} counted`,
      type: "bar",
      stack: `${model}-requested`,
      data: analysisEpochs.map((epoch) => rowsByEpochModel.get(`${epoch}|${model}`)?.countedWeight ?? null),
      barMaxWidth: 22,
      itemStyle: { color, opacity: 0.58 },
    });
    series.push({
      name: `${model} clipped`,
      type: "bar",
      stack: `${model}-requested`,
      data: analysisEpochs.map((epoch) => rowsByEpochModel.get(`${epoch}|${model}`)?.clippedWeight || 0),
      barMaxWidth: 14,
      itemStyle: { color: "#c7504f", opacity: 0.7 },
      label: {
        show: true,
        position: "top",
        color: "#b44842",
        fontWeight: 700,
        formatter: (item) => item.value > 0 ? `cut ${withCommas(item.value)}` : "",
      },
    });
  }
  series.push({
    name: "Cap limit",
    type: "line",
    data: analysisEpochs.map((epoch) => {
      const row = analysisRows.find((item) => item.epoch === epoch && item.capWeight != null);
      return row?.capWeight ?? null;
    }),
    symbol: "diamond",
    lineStyle: { color: "#d7a84f", width: 2.6, type: "dashed" },
    itemStyle: { color: "#d7a84f" },
  });
  charts.path.setOption({
    grid: { left: 78, right: 30, top: 48, bottom: 70 },
    legend: { top: 8, textStyle: { color: "#9aa8b9" }, selectedMode: true },
    tooltip: chartTooltip((params) => {
      const epoch = analysisEpochs[params[0]?.dataIndex];
      const lines = [`<strong>${epochLabel(epoch, epoch === nextEpoch)} all models</strong>`];
      for (const model of selectedModels) {
        const row = rowsByEpochModel.get(`${epoch}|${model}`);
        if (!row) continue;
        lines.push(`${model}: requested <strong>${withCommas(row.rawConsensusWeight || 0)}</strong>, counted <strong>${withCommas(row.countedWeight ?? row.cappedConsensusWeight ?? 0)}</strong>, cap cut <strong>${withCommas(row.clippedWeight || 0)}</strong>${row.initialModel ? " · exempt" : ""}`);
      }
      return lines.join("<br>");
    }),
    xAxis: { type: "category", data: labels, axisLabel: { color: "#9aa8b9", interval: 0 } },
    yAxis: { type: "value", name: "weight", nameTextStyle: { color: "#9aa8b9" }, axisLabel: { color: "#9aa8b9", formatter: (value) => compact.format(value) } },
    series,
  }, true);
};

const renderDenominator = () => {
  if (!charts.denominator) return;
  const actualEpochs = epochWindow;
  const labels = actualEpochs.map((epoch) => epochLabel(epoch));
  const compositionSeries = modelList.map((model) => ({
    name: `${model} counted`,
    type: "bar",
    stack: "root",
    data: actualEpochs.map((epoch) => {
      const row = rowsByEpochModel.get(`${epoch}|${model}`);
      return row ? Number(row.countedWeight ?? row.cappedConsensusWeight ?? row.rawConsensusWeight ?? 0) : 0;
    }),
    itemStyle: { color: colorForModel(model), opacity: 0.74 },
  }));
  const rootTotals = actualEpochs.map((epoch) => {
    const row = actualRows.find((item) => item.epoch === epoch);
    return row?.rootTotalWeight || null;
  });
  const nextLimits = actualEpochs.map((epoch) => {
    const row = actualRows.find((item) => item.epoch === epoch);
    return row?.rootTotalWeight ? Math.floor(Number(row.rootTotalWeight) * Number(row.capFactor || 0.75)) : null;
  });
  charts.denominator.setOption({
    grid: { left: 78, right: 28, top: 48, bottom: 60 },
    legend: { top: 8, textStyle: { color: "#9aa8b9" } },
    tooltip: chartTooltip((params) => {
      const epoch = actualEpochs[params[0]?.dataIndex];
      const root = rootTotals[params[0]?.dataIndex] || 0;
      const next = nextLimits[params[0]?.dataIndex] || 0;
      const lines = [`<strong>${epochLabel(epoch)} denominator</strong>`, `root total: <strong>${withCommas(root)}</strong>`, `next cap: <strong>${withCommas(next)}</strong> = ${withCommas(root)} x ${scaleText(capFactor)}`];
      for (const model of modelList) {
        const row = rowsByEpochModel.get(`${epoch}|${model}`);
        if (row) lines.push(`${model}: ${withCommas(row.countedWeight ?? row.cappedConsensusWeight ?? row.rawConsensusWeight ?? 0)} counted`);
      }
      return lines.join("<br>");
    }),
    xAxis: { type: "category", data: labels, axisLabel: { color: "#9aa8b9" } },
    yAxis: { type: "value", name: "weight", nameTextStyle: { color: "#9aa8b9" }, axisLabel: { color: "#9aa8b9", formatter: (value) => compact.format(value) } },
    series: [
      ...compositionSeries,
      {
        name: "Root total",
        type: "line",
        data: rootTotals,
        symbol: "diamond",
        lineStyle: { color: "#f1efe7", width: 2.4 },
        itemStyle: { color: "#f1efe7" },
      },
      {
        name: "Next epoch cap from this root",
        type: "line",
        data: nextLimits,
        symbol: "circle",
        lineStyle: { color: "#d7a84f", width: 2.4, type: "dashed" },
        itemStyle: { color: "#d7a84f" },
      },
    ],
  }, true);
};

const renderPressure = () => {
  if (!charts.pressure) return;
  const capModels = modelList;
  const xLabels = analysisEpochs.map((epoch) => epochLabel(epoch, epoch === nextEpoch));
  const yLabels = capModels;
  const points = [];
  const pointRows = new Map();
  for (const [y, model] of yLabels.entries()) {
    for (const [x, epoch] of analysisEpochs.entries()) {
      const row = rowsByEpochModel.get(`${epoch}|${model}`);
      const key = `${x}|${y}`;
      pointRows.set(key, row);
      const value = row?.capUtilization == null ? 0 : Number(row.capUtilization) * 100;
      points.push([x, y, value]);
    }
  }
  charts.pressure.setOption({
    grid: { left: 92, right: 36, top: 44, bottom: 56 },
    tooltip: {
      confine: true,
      backgroundColor: "rgba(10, 19, 31, 0.95)",
      borderColor: "#334e76",
      textStyle: { color: "#dbe5f1", fontSize: 12 },
      formatter: (item) => {
        const row = pointRows.get(`${item.data?.[0]}|${item.data?.[1]}`);
        if (!row) return "";
        if (row.capUtilization == null) {
          return [
            `<strong>${epochLabel(row.epoch, row.isForecast)} ${modelName(row)}</strong>`,
            "cap pressure: <strong>exempt</strong>",
            `requested: ${withCommas(row.rawConsensusWeight || 0)}`,
            `counted: ${withCommas(row.countedWeight ?? row.cappedConsensusWeight ?? row.rawConsensusWeight ?? 0)}`,
            `status: ${statusLabel(row.status)}`,
          ].join("<br>");
        }
        return [
          `<strong>${epochLabel(row.epoch, row.isForecast)} ${modelName(row)}</strong>`,
          `pressure: <strong>${pct(Number(row.capUtilization || 0) * 100)}</strong>`,
          `requested: ${withCommas(row.rawConsensusWeight || 0)}`,
          `cap: ${withCommas(row.capWeight || 0)}`,
          `headroom: ${row.capHeadroom == null ? "-" : withCommas(row.capHeadroom)}`,
          `clipped: ${withCommas(row.clippedWeight || 0)}`,
        ].join("<br>");
      },
    },
    xAxis: { type: "category", data: xLabels, axisLabel: { color: "#9aa8b9", interval: 0 } },
    yAxis: { type: "category", data: yLabels, axisLabel: { color: "#9aa8b9" } },
    visualMap: {
      min: 0,
      max: 125,
      calculable: false,
      orient: "horizontal",
      left: "center",
      bottom: 4,
      textStyle: { color: "#9aa8b9" },
      inRange: { color: ["#244d3f", "#d7a84f", "#c7504f"] },
    },
    series: [{
      name: "Cap pressure",
      type: "heatmap",
      data: points,
      label: {
        show: true,
        color: "#f5f0e8",
        formatter: (item) => {
          const row = pointRows.get(`${item.value[0]}|${item.value[1]}`);
          return row?.capUtilization == null ? "exempt" : pct(item.value[2]);
        },
      },
      itemStyle: {
        color: (item) => {
          const row = pointRows.get(`${item.value[0]}|${item.value[1]}`);
          if (row?.capUtilization == null) return "#6f8090";
          if (item.value[2] >= 100) return "#c7504f";
          if (item.value[2] >= 80) return "#d7a84f";
          return "#2f7d5f";
        },
      },
      emphasis: { itemStyle: { borderColor: "#f5f0e8", borderWidth: 1 } },
    }],
  }, true);
};

const flattenParamRows = () => {
  const snapshots = Array.isArray(data.paramSnapshots) ? data.paramSnapshots : [];
  return snapshots.flatMap((snapshot) => (snapshot.models || []).map((model) => ({
    epoch: snapshot.epoch,
    height: snapshot.height,
    position: snapshot.position,
    capFactor: snapshot.capFactor,
    initialModelLabel: snapshot.initialModelLabel,
    modelLabel: model.modelLabel || model.modelId,
    weightScaleFactor: model.weightScaleFactor,
  })));
};

const renderParams = () => {
  const paramRows = flattenParamRows().filter((row) => epochWindow.includes(Number(row.epoch)));
  if (els.paramTable) {
    els.paramTable.innerHTML = paramRows.map((row) => `
      <tr>
        <td>e${row.epoch}</td>
        <td>${row.position || "-"}</td>
        <td>${withCommas(row.height || 0)}</td>
        <td>${row.modelLabel}</td>
        <td>${scaleText(row.weightScaleFactor)}</td>
        <td>${scaleText(row.capFactor)}</td>
        <td>${row.initialModelLabel || "-"}</td>
      </tr>
    `).join("");
  }
  if (!charts.params || !paramRows.length) return;
  const points = uniq(paramRows.map((row) => `${row.epoch}|${row.position}|${row.height}`));
  const labels = points.map((key) => {
    const [epoch, position] = key.split("|");
    return `e${epoch} ${position}`;
  });
  charts.params.setOption({
    grid: { left: 64, right: 26, top: 44, bottom: 70 },
    legend: { top: 8, textStyle: { color: "#9aa8b9" } },
    tooltip: chartTooltip((params) => {
      const key = points[params[0]?.dataIndex];
      const rowsAtPoint = paramRows.filter((row) => `${row.epoch}|${row.position}|${row.height}` === key);
      const first = rowsAtPoint[0];
      return [
        `<strong>e${first.epoch} ${first.position}</strong>`,
        `height: ${withCommas(first.height)}`,
        `cap factor: ${scaleText(first.capFactor)}`,
        `initial model: ${first.initialModelLabel}`,
        ...rowsAtPoint.map((row) => `${row.modelLabel}: ${scaleText(row.weightScaleFactor)}`),
      ].join("<br>");
    }),
    xAxis: { type: "category", data: labels, axisLabel: { color: "#9aa8b9", rotate: 20 } },
    yAxis: { type: "value", name: "scale", nameTextStyle: { color: "#9aa8b9" }, axisLabel: { color: "#9aa8b9", formatter: scaleText } },
    series: modelList.map((model) => ({
      name: `${model} scale`,
      type: "line",
      step: "end",
      data: points.map((key) => paramRows.find((row) => `${row.epoch}|${row.position}|${row.height}` === key && row.modelLabel === model)?.weightScaleFactor ?? null),
      lineStyle: { color: colorForModel(model), width: 2.5 },
      itemStyle: { color: colorForModel(model) },
      symbolSize: 7,
    })).concat([{
      name: "Cap factor",
      type: "line",
      step: "end",
      data: points.map((key) => paramRows.find((row) => `${row.epoch}|${row.position}|${row.height}` === key)?.capFactor ?? null),
      lineStyle: { color: "#d7a84f", width: 2, type: "dashed" },
      itemStyle: { color: "#d7a84f" },
      symbolSize: 7,
    }]),
  }, true);
};

const renderTable = () => {
  if (!els.tableBody) return;
  const tableRows = analysisRows
    .slice()
    .sort((a, b) => a.epoch - b.epoch || modelName(a).localeCompare(modelName(b)));
  if (els.tableStatus) els.tableStatus.textContent = `All models · ${tableRows.length} formula rows`;
  els.tableBody.innerHTML = tableRows.map((row) => {
    const requested = row.rawConsensusWeight || 0;
    const counted = row.countedWeight ?? row.cappedConsensusWeight ?? requested;
    return `
      <tr class="${row.isForecast ? "forecast-row" : ""}">
        <td>${epochLabel(row.epoch, row.isForecast)}</td>
        <td>${modelName(row)}</td>
        <td>${withCommas(row.subgroupRawWeight)}</td>
        <td>${scaleText(row.weightScaleFactor)}</td>
        <td>${withCommas(requested)}</td>
        <td>${withCommas(row.previousEpochRootTotalWeight || 0)}</td>
        <td>${row.capWeight == null ? "exempt" : withCommas(row.capWeight)}</td>
        <td>${withCommas(counted)}</td>
        <td>${withCommas(row.clippedWeight || 0)}</td>
        <td>${row.capHeadroom == null ? "-" : withCommas(row.capHeadroom)}</td>
        <td>${row.capUtilization == null ? "-" : pct(Number(row.capUtilization) * 100)}</td>
        <td>${withCommas(row.participantCount || 0)}</td>
        <td>${withCommas(row.nodeCount || 0)}</td>
        <td><span class="${statusClass(row.status)}">${statusLabel(row.status)}</span></td>
      </tr>
    `;
  }).join("");
};

const renderAll = () => {
  renderSummary();
  renderCapPath();
  renderDenominator();
  renderPressure();
  renderParams();
  renderTable();
};

if (!actualRows.length || !Object.keys(charts).length) {
  setNoData();
} else {
  renderOptions();
  renderAll();
  els.modelSelect?.addEventListener("change", renderAll);
  window.addEventListener("resize", () => Object.values(charts).forEach((chart) => chart.resize()));
}
