const state = {
  plan: null,
};

const el = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.error || payload.reason || `请求失败: ${response.status}`);
  }
  return payload;
}

function addMessage(kind, text, detail) {
  const node = document.createElement("article");
  node.className = `message ${kind}`;
  const p = document.createElement("p");
  p.textContent = text;
  node.appendChild(p);
  if (detail) {
    const pre = document.createElement("pre");
    pre.textContent = typeof detail === "string" ? detail : JSON.stringify(detail, null, 2);
    node.appendChild(pre);
  }
  el("chatLog").appendChild(node);
  el("chatLog").scrollTop = el("chatLog").scrollHeight;
}

function validationSummary(validation) {
  const erc = validation?.erc?.summary;
  const netlist = validation?.netlist;
  if (!validation) return "没有校验结果。";
  return [
    `ERC: ${erc ? `${erc.violations} 条违规` : "未生成摘要"}`,
    `Netlist: ${netlist?.ok ? "导出成功" : "导出失败"}`,
  ].join("\n");
}

function showPlan(plan) {
  state.plan = plan;
  el("planPanel").hidden = !plan?.ok;
  el("planText").textContent = JSON.stringify(plan, null, 2);
}

async function loadProject() {
  const project = await api("/api/project");
  el("projectPath").textContent = project.schematic;
  const result = await api("/api/project/summary");
  const summary = result.summary;
  const cards = el("summaryGrid").querySelectorAll("strong");
  cards[0].textContent = summary.placed_symbols;
  cards[1].textContent = summary.wires;
  cards[2].textContent = summary.labels;
  cards[3].textContent = summary.version || "--";
}

async function sendMessage() {
  const input = el("messageInput");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  addMessage("user", message);
  try {
    const result = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    addMessage("agent", result.reply?.content || result.reply?.message || "已生成回复。");
    if (result.plan?.ok) {
      showPlan(result.plan);
      addMessage("agent", "我生成了一个需要确认的工具计划。");
    } else if (result.plan?.reason) {
      addMessage("agent", result.plan.reason);
    }
  } catch (error) {
    addMessage("agent", `出错了：${error.message}`);
  }
}

async function previewPlan() {
  if (!state.plan?.arguments) return;
  const args = state.plan.arguments;
  try {
    const result = await api("/api/tools/set-value/preview", {
      method: "POST",
      body: JSON.stringify({ reference: args.reference, value: args.new_value }),
    });
    addMessage("agent", "预览 diff：", result.result.diff);
  } catch (error) {
    addMessage("agent", `预览失败：${error.message}`);
  }
}

async function applyPlan() {
  if (!state.plan?.arguments) return;
  const args = state.plan.arguments;
  try {
    const result = await api("/api/tools/set-value/apply", {
      method: "POST",
      body: JSON.stringify({ reference: args.reference, value: args.new_value }),
    });
    addMessage("agent", `已执行修改并完成校验。\n${validationSummary(result.validation)}`, {
      diff: result.result.diff,
      snapshot: result.result.snapshot?.snapshot,
    });
    showPlan(null);
    await loadProject();
  } catch (error) {
    addMessage("agent", `执行失败：${error.message}`);
  }
}

async function validateNow() {
  try {
    const result = await api("/api/validate", { method: "POST", body: "{}" });
    addMessage("agent", `校验完成。\n${validationSummary(result.validation)}`);
  } catch (error) {
    addMessage("agent", `校验失败：${error.message}`);
  }
}

async function explainErc() {
  try {
    const result = await api("/api/erc/explain", { method: "POST", body: "{}" });
    const groups = result.explanation.groups.slice(0, 6).map((group) => ({
      count: group.count,
      description: group.description,
      suggestion: group.suggestion,
      examples: group.examples,
    }));
    addMessage("agent", "ERC 解释已生成：", groups);
  } catch (error) {
    addMessage("agent", `ERC 解释失败：${error.message}`);
  }
}

async function exportSpice() {
  try {
    const result = await api("/api/export/spice", { method: "POST", body: "{}" });
    addMessage("agent", result.result.ok ? "SPICE netlist 已导出。" : "SPICE netlist 导出失败。", result.result);
  } catch (error) {
    addMessage("agent", `SPICE 导出失败：${error.message}`);
  }
}

async function showSnapshots() {
  try {
    const result = await api("/api/snapshots");
    const snapshots = result.snapshots.slice(0, 8);
    addMessage("agent", snapshots.length ? "最近快照：" : "还没有快照。", snapshots);
  } catch (error) {
    addMessage("agent", `读取快照失败：${error.message}`);
  }
}

async function searchLibrary(kind) {
  const query = el("searchInput").value.trim();
  if (!query) {
    addMessage("agent", "请输入要搜索的符号或封装关键词。");
    return;
  }
  try {
    const path = kind === "symbols" ? "/api/library/symbols" : "/api/library/footprints";
    const result = await api(path, { method: "POST", body: JSON.stringify({ query }) });
    const data = kind === "symbols" ? result.symbols : result.footprints;
    addMessage("agent", `${kind === "symbols" ? "符号" : "封装"}搜索结果：`, data.results.slice(0, 12));
  } catch (error) {
    addMessage("agent", `搜索失败：${error.message}`);
  }
}

el("sendBtn").addEventListener("click", sendMessage);
el("messageInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") sendMessage();
});
el("refreshBtn").addEventListener("click", loadProject);
el("dismissPlanBtn").addEventListener("click", () => showPlan(null));
el("previewBtn").addEventListener("click", previewPlan);
el("applyBtn").addEventListener("click", applyPlan);
el("validateBtn").addEventListener("click", validateNow);
el("explainErcBtn").addEventListener("click", explainErc);
el("spiceBtn").addEventListener("click", exportSpice);
el("snapshotsBtn").addEventListener("click", showSnapshots);
el("symbolSearchBtn").addEventListener("click", () => searchLibrary("symbols"));
el("footprintSearchBtn").addEventListener("click", () => searchLibrary("footprints"));

loadProject().catch((error) => addMessage("agent", `工程读取失败：${error.message}`));
