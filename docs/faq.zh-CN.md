# 常见问题

## Q1：为什么不是 KiCad 原生侧边栏？

当前 Beta 采用外部 Web 侧边栏，因为 KiCad 插件 UI 能力对完整 Copilot 体验还不够直接。外部侧边栏更适合快速验证产品能力。

## Q2：会上传我的工程文件吗？

默认不会。当前 Beta 默认使用 `MockProvider`，不调用外部模型。只有配置模型环境变量后，才会走 OpenAI-compatible provider。

## Q3：为什么 ERC 报告里有很多错误？

Beta 使用 KiCad 官方 demo 作为样例，样例本身会产生一些 ERC 提示。该项目重点验证自动化链路，而不是修复 demo 电路。

## Q4：修改前能撤销吗？

每次写入前会创建快照。当前 UI 可以查看快照，后端已有恢复接口。完整的一键恢复按钮将在后续版本加入。

## Q5：SPICE 导出失败怎么办？

确认：

- KiCad CLI 路径正确。
- 工程中器件有 SPICE 模型。
- KiCad 用户配置目录可访问。

必要时用真实用户权限运行服务。

## Q6：如何接 DeepSeek？

设置：

```powershell
$env:KICAD_AGENT_MODEL_BASE_URL="https://api.deepseek.com"
$env:KICAD_AGENT_API_KEY="<你的 API Key>"
$env:KICAD_AGENT_MODEL="<模型名称>"
```

然后重新启动 Agent。

## Q7：支持 KiCad 9 吗？

当前 Beta 主要在 KiCad 10.0.3 验证。KiCad 9 理论上部分 CLI 能力可用，但未作为 Beta 验收环境。
