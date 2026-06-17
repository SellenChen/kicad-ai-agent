# KiCad AI Agent

Windows 平台 KiCad AI Agent Beta。提供类似 Copilot 的深色侧边栏，用自然语言辅助 KiCad 工程管理、原理图检查、参数修改、元件新增、ERC 解释和 netlist/SPICE 导出。

> 当前版本 `0.2.0b1`，重点验证「KiCad 插件启动 + 本地 Agent 服务 + 侧边栏 UI + KiCad CLI 校验 + 保格式原理图 patch」这条技术路线。

## 功能

- **深色侧边栏 UI** — Edge App Mode 独立窗口，固定输入区、Thinking 状态提示
- **KiCad PCB Editor 插件启动器** — 工具菜单一键启动
- **桌面快捷方式启动器** — 补充 Schematic Editor 无原生插件入口的限制
- **工程和原理图摘要** — 符号/连线/标签/版本统计
- **原理图特征抽取** — 随对话上传元件族分布、有源器件、电源符号等上下文
- **自然语言修改 Value** — 例如「把 R4 改成 2K」，生成可预览计划，确认后写入
- **新增元件实例** — 从模型回复的 Markdown 表格中解析并追加 symbol block
- **保格式 `.kicad_sch` 写入** — 局部文本替换，不重排整个文件
- **修改前自动快照** — 每次写入前保存副本，可回滚
- **ERC + netlist 校验闭环** — 写入后自动运行 KiCad CLI 校验
- **ERC 报告分组解释** — 按违规类型分组并给出修复建议
- **SPICE netlist 导出**
- **KiCad 符号库和封装库搜索**
- **DeepSeek API 接入** — 侧边栏直接配置 API Key 和模型，可选 DeepSeek V4 Pro / V4 Flash
- **上下文确认执行** — 上一步生成计划后回复「执行」直接触发写入
- **完整自测脚本** — 覆盖 health → set-value → add-parts → ERC → 库搜索全链路

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
.\scripts\install_plugin_gui.ps1
```

- 自动检测本机 KiCad 版本和插件目录
- 未检测到时可用「Browse...」手动选择 `scripting\plugins` 目录
- 自动创建桌面快捷方式

### CLI 安装

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_plugin.ps1
```

安装后在 KiCad PCB Editor 点击 **工具 > KiCad AI Agent** 启动。在 Schematic Editor 中使用桌面快捷方式。

## 模型配置

侧边栏顶部可直接配置：

- **模型选择** — DeepSeek V4 Pro / DeepSeek V4 Flash
- **API Key** — 输入并保存
- **上传原理图特征** — 勾选后随对话上传紧凑的工程上下文 JSON

未配置 API Key 时使用本地 mock 模式，不调用外部模型。

## 自测

```powershell
python .\app\scripts\self_test.py
```

自测覆盖：服务启动、工程摘要、set_value 预览/执行、add_parts 执行、ERC 解释、符号/封装搜索、环境诊断。

## 目录结构

```text
app/kicad_ai_agent/      后端服务和工具层 (server, schematic, kicad_cli, features, settings, ...)
app/static/              深色侧边栏 UI (index.html, app.js, styles.css)
app/kicad_plugin/         KiCad ActionPlugin 启动器
app/samples/              样例工程
scripts/                  安装/打包/发布脚本
docs/                     中文文档
work/                     运行时数据 (快照/报告/设置)
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

- 新增元件不自动连线和布局（仅追加符号实例）
- 侧边栏是 Edge App Mode 独立窗口，不是 KiCad 原生 dock panel
- API Key 存储为本地明文 JSON（后续将迁移到 Windows Credential Manager）
- 尚未支持流式输出、自动 BOM、PCB 布局修改

## 许可

MIT License
