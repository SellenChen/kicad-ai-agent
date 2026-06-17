# 常见问题

## Q1：为什么不是 KiCad 原生侧边栏？

当前 Beta 采用外部 Web 侧边栏（Edge App Mode），因为 KiCad 插件 UI 能力对完整 Copilot 体验还不够直接。外部侧边栏更适合快速验证产品能力。后续可探索 KiCad 原生 Dock Panel。

## Q2：会上传我的工程文件吗？

默认不会。未配置 API Key 时使用本地 `MockProvider`，不调用外部模型。配置 API Key 后，对话会上传原理图特征摘要（元件族分布、有源器件列表等），不会上传完整的 `.kicad_sch` 文件内容。

## Q3：为什么 PCB Editor 有菜单入口但 Schematic Editor 没有？

KiCad 10 的 Python ActionPlugin 机制支持 `pcbnew.ActionPlugin`，但不支持 `eeschema` 同等机制。因此插件只能出现在 PCB Editor 的工具菜单中。

**解决方案**：桌面快捷方式 `KiCad AI Agent.lnk`，可记录最近工程并直接启动 Agent。

## Q4：如何配置 DeepSeek？

侧边栏顶部模型配置面板：

1. 下拉选择模型（DeepSeek V4 Pro / V4 Flash）
2. 输入 API Key
3. 点击「保存」

保存后对话即调用 DeepSeek API。也可通过环境变量配置（旧方式）：

```powershell
$env:KICAD_AGENT_MODEL_BASE_URL="https://api.deepseek.com"
$env:KICAD_AGENT_API_KEY="<你的 API Key>"
$env:KICAD_AGENT_MODEL="deepseek-v4-pro"
```

## Q5：修改前能撤销吗？

每次写入前会自动创建快照到 `work/stage1_runtime/snapshots/`。侧边栏点击「快照」可查看最近记录。后端已有恢复接口（`/api/snapshots/restore`），UI 中一键恢复按钮将在后续版本加入。

## Q6：为什么 ERC 报告里有很多违规？

Beta 使用 KiCad 官方 demo 作为样例，样例本身会产生一些 ERC 提示。该项目重点验证自动化链路，而不是修复 demo 电路。

## Q7：SPICE 导出失败怎么办？

确认：

- KiCad CLI 路径正确
- 工程中器件有 SPICE 模型
- KiCad 用户配置目录可访问

必要时用真实用户权限运行服务。

## Q8：新增元件后为什么没有连线？

当前新增元件 (`schematic.add_parts`) 只追加 symbol 实例到原理图末尾，不自动连线和布局。请在 KiCad 中手动调整位置并连线。自动放置和连线是后续开发目标。

## Q9：支持 KiCad 9 吗？

当前 Beta 主要在 KiCad 10.0.x 验证。KiCad 9 理论上部分 CLI 能力可用，但未作为 Beta 验收环境。

## Q10：安装插件的 GUI 在哪？

双击 `scripts\install_plugin_gui.ps1` 启动。安装器会自动检测本机 KiCad 版本和插件目录，未检测到时可以手动选择。CLI 版可用 `powershell -ExecutionPolicy Bypass -File .\scripts\install_plugin.ps1`。

## Q11：桌面快捷方式不工作？

确认：

- `work/stage2_runtime/last_project.txt` 中有最近工程的完整路径
- 或者通过 PCB Editor 插件启动一次以写入该文件
- 也可以手动选择工程：快捷方式会在无记录时弹出文件选择框

## Q12：API Key 保存在哪？安全吗？

当前保存在 `work/stage1_runtime/settings.json` 中（明文 JSON）。该目录已通过 `.gitignore` 排除，不会上传到 GitHub。后续将迁移到 Windows Credential Manager。

## Q13：发送消息后没有反应？

检查：

- 侧边栏顶部是否显示工程路径（如未显示，点击刷新）
- 如果配置了 API Key，检查网络连接和 API Key 有效性
- 如果未配置 API Key，确认使用 mock 模式（会返回预设回复）
- 查看 `http://127.0.0.1:8765/api/health` 确认服务运行正常
