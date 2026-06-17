# KiCad AI Agent

Windows 平台 KiCad AI Agent Beta。它提供类似 Copilot 的深色侧边栏，让用户通过自然语言辅助 KiCad 工程管理、原理图读取、元件参数修改、简单电路自动生成、ERC 解释、netlist/SPICE 导出和模型 API 调用。

> 当前版本 `0.2.2`。本版本重点修复 PCB Editor 插件启动时错误复用旧工程服务的问题，并继续保留「DeepSeek API + 可执行原理图计划 + 空工程自动建图 + 元件摆放/连线 + KiCad CLI 校验」链路。

## 功能

- **深色侧边栏 UI**：Edge App Mode 独立窗口，固定输入区、独立聊天滚动区、Thinking 状态提示。
- **KiCad PCB Editor 插件启动器**：在 PCB Editor 的工具菜单中一键启动。
- **桌面快捷方式启动器**：补充 Schematic Editor 暂无原生 Python ActionPlugin 菜单入口的限制。
- **工程自动识别**：优先使用启动参数，其次读取 KiCad Schematic Editor 最近文件记录，再回退到最近一次工程。
- **工程一致性校验**：插件启动时会确认已有服务的 `/api/project` 是否等于当前 KiCad 工程，不一致时自动换端口启动新实例。
- **工程和原理图摘要**：统计符号、连线、标签和 KiCad schematic version。
- **原理图特征抽取**：随对话上传紧凑工程上下文，包括元件族分布、有源器件、电源符号等。
- **DeepSeek API 接入**：侧边栏直接配置 API Key 和模型，当前提供 DeepSeek V4 Pro / V4 Flash。
- **简单电路自动生成**：支持从空工程通过对话生成常见积分、微分、1 kHz 方波转三角波 RC 滤波等原理图模块。
- **自动摆放与连线**：生成 KiCad symbol、wire、label、junction、说明文本，并写入 `.kicad_sch`。
- **自然语言修改 Value**：例如“把 R4 改成 2K”，生成可预览计划，确认后写入。
- **新增元件实例**：从模型回复的 Markdown 表格或本地计划中解析并追加 symbol block。
- **保格式 `.kicad_sch` 写入**：局部文本 patch，不重排整个文件。
- **修改前自动快照**：每次写入前保存副本，可回溯。
- **ERC + netlist 校验闭环**：写入后自动运行 KiCad CLI 校验。
- **ERC 报告分组解释**：按违规类型分组并给出修复建议。
- **SPICE netlist 导出**。
- **KiCad 符号库和封装库搜索**。
- **上下文确认执行**：上一轮生成计划后，用户回复“执行”即可触发写入。
- **完整自测脚本**：覆盖 health、set-value、add-parts、generate-circuit、ERC、库搜索和环境诊断。

## 快速开始

要求：

- Windows 10/11
- KiCad 10.0.x
- Python 3.11+

启动 Beta 样例：

```powershell
cd app
python .\run_agent.py --project .\samples\amplifier-ac-stage1\amplifier-ac.kicad_pro --host 127.0.0.1 --port 8765
```

浏览器打开 `http://127.0.0.1:8765`。

## 安装到 KiCad

### GUI 安装器（推荐）

双击运行，无需命令行：

```powershell
.\scripts\install_plugin_gui.cmd
```

- 自动检测本机 KiCad 版本和插件目录。
- 未检测到时可用 Browse 手动选择 `scripting\plugins` 目录。
- 自动创建桌面快捷方式。

### CLI 安装

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_plugin.ps1
```

安装后在 KiCad PCB Editor 点击 **工具 > KiCad AI Agent** 启动。在 Schematic Editor 中使用桌面快捷方式，启动脚本会尝试从 KiCad 最近原理图记录中识别当前工程。

## 模型配置

侧边栏顶部可直接配置：

- **模型选择**：DeepSeek V4 Pro / DeepSeek V4 Flash。
- **API Key**：输入并保存。
- **上传原理图特征**：勾选后随对话上传紧凑的工程上下文 JSON。

未配置 API Key 时使用最基础的本地 mock 模式，不调用外部模型。本项目后续重点放在 DeepSeek/API 驱动的真实工作能力。

## 生成原理图示例

在空工程中输入：

```text
请生成一个1kHz方波转三角波的滤波电路
```

Agent 会生成可执行计划，确认后写入：

- `R1 10K` 串联输入。
- `C1 47nF` 对地积分滤波。
- `VIN_1KHZ_SQUARE` / `VOUT_TRIANGLE` 网络标签。
- `GND` 电源符号、连线、junction 和说明文本。
- 写入后自动运行 ERC 和 netlist 导出校验。

同类简单请求还包括积分电路、微分电路和基础波形转换模块。

## 自测

```powershell
python .\app\scripts\self_test.py
```

自测覆盖：服务启动、工程摘要、set_value 预览/执行、add_parts 执行、从空工程生成电路、ERC 解释、符号/封装搜索、环境诊断。

## 目录结构

```text
app/kicad_ai_agent/      后端服务和工具层 (server, schematic, kicad_cli, features, settings, provider, ...)
app/static/              深色侧边栏 UI (index.html, app.js, styles.css)
app/kicad_plugin/         KiCad ActionPlugin 启动器
app/samples/              样例工程
scripts/                  安装/打包/发布/启动脚本
docs/                     中文文档
work/                     运行时数据（快照/报告/设置）
```

## 文档

- [快速开始](docs/quick-start.zh-CN.md)
- [安装指南](docs/install.zh-CN.md)
- [使用手册](docs/user-guide.zh-CN.md)
- [架构说明](docs/architecture.zh-CN.md)
- [开发指南](docs/development.zh-CN.md)
- [常见问题](docs/faq.zh-CN.md)
- [开发维护手册](docs/KiCad_AI_Agent_开发维护手册.zh-CN.md)

## 当前限制

- 0.2.2 的自动生成能力主要覆盖简单模拟/RC 电路模板；复杂电路仍需要模型规划和人工审查。
- 侧边栏是 Edge App Mode 独立窗口，不是 KiCad 原生 dock panel。
- API Key 当前存储为本地明文 JSON，后续应迁移到 Windows Credential Manager。
- 暂未支持流式输出、自动 BOM、PCB 布局修改和复杂 SPICE 仿真自动闭环。

## 许可

MIT License
