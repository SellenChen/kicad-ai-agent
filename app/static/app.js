const state = {
  plan: null,
  settings: null,
  history: [],
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
  scrollChatToBottom();
  return node;
}

function addThinkingMessage() {
  const modelName = el("modelSelect")?.selectedOptions?.[0]?.textContent || "模型";
  const node = document.createElement("article");
  node.className = "message agent thinking";
  const line = document.createElement("p");
  line.className = "thinking-line";
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  const label = document.createElement("span");
  label.textContent = `[${modelName}] Thinking...`;
  line.appendChild(spinner);
  line.appendChild(label);
  node.appendChild(line);
  el("chatLog").appendChild(node);
  scrollChatToBottom();
  return node;
}

function removeNode(node) {
  if (node?.parentNode) node.parentNode.removeChild(node);
}

function scrollChatToBottom() {
  const chat = el("chatLog");
  chat.scrollTop = chat.scrollHeight;
}

function isConfirmExecution(text) {
  const normalized = text.trim().replace(/\s+/g, "").toLowerCase();
  return [
    "执行",
    "确认执行",
    "直接执行",
    "直接帮我执行",
    "开始执行",
    "可以执行",
    "好的执行",
    "好执行",
    "ok",
    "yes",
    "y",
  ].includes(normalized);
}

function validationSummary(validation) {
  if (!validation) return "没有校验结果。";
  const erc = validation.erc?.summary;
  const netlist = validation.netlist;
  return [
    `ERC: ${erc ? `${erc.violations} 条违规` : "未生成摘要"}`,
    `Netlist: ${netlist?.ok ? "导出成功" : "导出失败"}`,
  ].join("\n");
}

function showPlan(plan) {
  state.plan = plan?.ok ? plan : null;
  el("planPanel").hidden = !state.plan;
  el("planText").textContent = state.plan ? JSON.stringify(state.plan, null, 2) : "";
}

async function loadSettings() {
  const result = await api("/api/settings");
  state.settings = result.settings;
  const select = el("modelSelect");
  select.innerHTML = "";
  for (const model of result.models) {
    const option = document.createElement("option");
    option.value = model.id;
    option.textContent = model.label;
    select.appendChild(option);
  }
  select.value = result.settings.model;
  el("uploadFeaturesToggle").checked = Boolean(result.settings.upload_schematic_features);
  el("apiKeyInput").placeholder = result.settings.api_key_set ? "已保存，输入新 Key 可覆盖" : "输入 DeepSeek API Key";
  el("settingsStatus").textContent = result.settings.api_key_set
    ? `已配置 ${result.settings.model}，对话会调用 DeepSeek。`
    : "未配置 API Key，当前使用本地 mock 模式。";
}

async function saveSettings() {
  const apiKey = el("apiKeyInput").value.trim();
  const payload = {
    model: el("modelSelect").value,
    base_url: "https://api.deepseek.com",
    upload_schematic_features: el("uploadFeaturesToggle").checked,
  };
  if (apiKey) payload.api_key = apiKey;
  const result = await api("/api/settings", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  state.settings = result.settings;
  el("apiKeyInput").value = "";
  await loadSettings();
  addMessage("agent", "模型配置已保存。");
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
  state.history.push({ role: "user", content: message });

  if (isConfirmExecution(message) && state.plan?.ok) {
    addMessage("agent", "收到确认，正在执行上一条工具计划。");
    await applyPlan();
    return;
  }

  const thinking = addThinkingMessage();
  try {
    const result = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, history: state.history.slice(-12) }),
    });
    removeNode(thinking);
    const replyText = result.reply?.content || "已生成回复。";
    addMessage("agent", replyText, result.reply?.error ? { error: result.reply.error } : null);
    state.history.push({ role: "assistant", content: replyText });

    if (result.executed) {
      addMessage("agent", `已执行并完成校验。\n${validationSummary(result.executed.validation)}`, result.executed.result);
      await loadProject();
      showPlan(null);
      return;
    }

    if (result.plan?.ok) {
      showPlan(result.plan);
      addMessage("agent", "我生成了一个可执行计划。你可以点“执行并校验”，也可以直接回复“执行”。");
    } else {
      showPlan(null);
    }
  } catch (error) {
    removeNode(thinking);
    addMessage("agent", `出错了：${error.message}`);
  }
}

async function previewPlan() {
  if (!state.plan?.arguments) return;
  if (state.plan.tool !== "schematic.set_property") {
    addMessage("agent", "当前计划包含新增元件，暂不提供 diff 预览；执行前会自动创建快照。");
    return;
  }
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
    let result;
    if (state.plan.tool === "schematic.set_property") {
      result = await api("/api/tools/set-value/apply", {
        method: "POST",
        body: JSON.stringify({ reference: args.reference, value: args.new_value }),
      });
    } else if (state.plan.tool === "schematic.add_parts") {
      result = await api("/api/tools/add-parts/apply", {
        method: "POST",
        body: JSON.stringify({ parts: args.parts || [] }),
      });
    } else {
      throw new Error(`暂不支持执行该计划：${state.plan.tool}`);
    }
    addMessage("agent", `已执行修改并完成校验。\n${validationSummary(result.validation)}`, {
      result: result.result,
      snapshot: result.result?.snapshot?.snapshot,
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

async function showFeatures() {
  try {
    const result = await api("/api/project/features");
    addMessage("agent", "当前会上传给模型的原理图特征：", result.features);
  } catch (error) {
    addMessage("agent", `读取特征失败：${error.message}`);
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
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});
el("refreshBtn").addEventListener("click", loadProject);
el("saveSettingsBtn").addEventListener("click", saveSettings);
el("dismissPlanBtn").addEventListener("click", () => showPlan(null));
el("previewBtn").addEventListener("click", previewPlan);
el("applyBtn").addEventListener("click", applyPlan);
el("featuresBtn").addEventListener("click", showFeatures);
el("validateBtn").addEventListener("click", validateNow);
el("explainErcBtn").addEventListener("click", explainErc);
el("spiceBtn").addEventListener("click", exportSpice);
el("snapshotsBtn").addEventListener("click", showSnapshots);
el("symbolSearchBtn").addEventListener("click", () => searchLibrary("symbols"));
el("footprintSearchBtn").addEventListener("click", () => searchLibrary("footprints"));

Promise.all([loadSettings(), loadProject()]).catch((error) => addMessage("agent", `初始化失败：${error.message}`));
