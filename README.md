# KiCad AI Agent

Windows 平台 KiCad AI Agent Beta。它提供一个类似 Copilot 的本地侧边栏，用自然语言辅助 KiCad 工程管理、原理图检查、参数修改、ERC 解释和 netlist 导出。

> 当前版本是 Beta 验证版，重点验证“KiCad 插件启动 + 本地 Agent 服务 + 侧边栏 UI + KiCad CLI 校验 + 保格式原理图 patch”这条技术路线。

## 功能

- 本地 Web 侧边栏 UI
- KiCad PCB Editor 启动器插件
- KiCad 工程和原理图摘要
- 自然语言参数修改计划，例如“把 R4 改成 2K”
- 保格式 `.kicad_sch` 属性修改
- 修改前自动快照
- ERC + netlist 校验闭环
- ERC 报告分组解释
- SPICE netlist 导出
- KiCad 符号库和封装库搜索
- OpenAI-compatible / DeepSeek 模型接口骨架，默认 mock provider

## 快速开始

要求：

- Windows
- KiCad 10.0.x
- Python 3.11+ 或 KiCad 自带 Python

启动 Beta 样例：

```powershell
cd app
python .\run_agent.py --project .\samples\amplifier-ac-stage1\amplifier-ac.kicad_pro --host 127.0.0.1 --port 8765
```

打开：

```text
http://127.0.0.1:8765
```

自测：

```powershell
python .\app\scripts\self_test.py
```

## KiCad 插件

插件目录：

```text
app\kicad_plugin\kicad_ai_agent_launcher
```

Windows 用户插件目录：

```text
%APPDATA%\kicad\10.0\scripting\plugins\kicad_ai_agent_launcher
```

安装后打开 KiCad PCB Editor，刷新或重启插件，点击 `KiCad AI Agent` 即可启动本地侧边栏。

## 文档

- [快速开始](docs/quick-start.zh-CN.md)
- [安装指南](docs/install.zh-CN.md)
- [使用手册](docs/user-guide.zh-CN.md)
- [架构说明](docs/architecture.zh-CN.md)
- [开发指南](docs/development.zh-CN.md)
- [常见问题](docs/faq.zh-CN.md)

## 当前限制

- 当前自然语言执行范围主要覆盖元件 Value 修改。
- 当前侧边栏是浏览器页面，不是 KiCad 原生 dock panel。
- 默认使用 mock provider，真实 DeepSeek 调用需要配置 API key。
- 尚未支持自动放置符号、自动连线和 PCB 布局。

## 许可

MIT License
