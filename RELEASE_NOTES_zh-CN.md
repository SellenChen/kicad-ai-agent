# v0.2.0-beta.1

KiCad AI Agent Beta 首个可验证版本。

## 新增功能

- 本地 Agent 服务和 Web 侧边栏。
- KiCad PCB Editor 启动器插件。
- KiCad 工程/原理图摘要。
- 自然语言参数修改计划，例如“把 R4 改成 2K”。
- 保格式 `.kicad_sch` 属性修改。
- 修改前自动快照。
- 修改后自动运行 ERC 和 netlist 导出。
- ERC 报告分组解释和修复建议。
- SPICE netlist 导出。
- KiCad 符号库和封装库搜索。
- OpenAI-compatible / DeepSeek 模型接口骨架。
- 中文快速开始、安装指南、使用手册、架构说明、开发指南和 FAQ。

## 验证结果

已在 Windows + KiCad 10.0.3 上完成自测：

- 服务启动成功。
- 样例工程摘要成功。
- `R4: 1K -> 2K` 保格式 patch 成功。
- ERC 报告生成成功。
- netlist 导出成功。
- ERC 解释接口成功。
- 符号/封装库搜索成功。
- KiCad 插件启动器 smoke test 成功。

## 当前限制

- 当前自然语言执行范围主要覆盖元件 Value 修改。
- 当前侧边栏是 Web 页面，还不是 KiCad 原生 dock panel。
- 默认使用 mock provider；真实模型调用需要配置 API key。
- 尚未支持自动放置符号、自动连线和 PCB 布局。

## 下载

请下载 release 附件：

```text
kicad-ai-agent-beta-v0.2.0-beta.1.zip
```

解压后阅读：

```text
docs/quick-start.zh-CN.md
docs/install.zh-CN.md
```
