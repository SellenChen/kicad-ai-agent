# 开发指南

本文面向后续开发维护者，说明本地运行、模块分工、自测和发布方式。当前版本：`0.2.1`。

## 1. 本地运行

```powershell
cd app
python .\run_agent.py --project .\samples\amplifier-ac-stage1\amplifier-ac.kicad_pro --host 127.0.0.1 --port 8765
```

访问 `http://127.0.0.1:8765`。

如果只传入 `.kicad_pro` 且项目内没有同名 `.kicad_sch`，后端会通过 `ensure_schematic()` 创建最小原理图文件。

## 2. 自测

```powershell
python .\app\scripts\self_test.py
```

自测覆盖：

- 服务 health、settings、summary。
- 自然语言 Value 修改计划、diff 预览和执行。
- 新增元件计划和执行。
- 从空工程生成 1 kHz 方波转三角波 RC 滤波电路。
- ERC、netlist、ERC 解释。
- KiCad 符号库/封装库搜索。
- 环境诊断。

## 3. 主要模块

```text
kicad_ai_agent/server.py       HTTP API、静态页面服务、计划调度
kicad_ai_agent/schematic.py    原理图读取、空图创建、计划生成、保格式 patch、电路生成
kicad_ai_agent/kicad_cli.py    KiCad CLI 封装 (ERC/netlist/SPICE)
kicad_ai_agent/features.py     原理图特征抽取（随对话上传）
kicad_ai_agent/settings.py     模型配置持久化 (settings.json)
kicad_ai_agent/provider.py     模型 Provider (Mock + DeepSeek + OpenAI-compatible base)
kicad_ai_agent/diagnostics.py  环境诊断和 ERC 解释
kicad_ai_agent/library.py      符号/封装搜索
kicad_ai_agent/sexpr.py        S-expression 解析器
kicad_ai_agent/paths.py        路径常量和运行时目录管理
```

## 4. 原理图生成链路

入口在 `server.py` 的 `/api/chat`：

1. 调用 DeepSeek 或 mock provider 获得回复。
2. 优先解析 `schematic.set_property` 和 `schematic.add_parts`。
3. 如果用户意图是生成/搭建/创建电路，调用 `plan_circuit_from_prompt()`。
4. 返回 `schematic.generate_circuit` 计划给前端。
5. 用户确认后，前端调用 `/api/tools/generate-circuit/apply`。
6. 后端执行 `generate_circuit_preserving_format()`，写入 symbol、wire、label、junction、text。
7. 自动创建快照并执行 `validate_schematic()`。

当前内置模板位于 `schematic.py`：

- `_recipe_square_to_triangle()`：1 kHz 方波转三角波 RC 滤波。
- `_recipe_integrator()`：基础 RC 积分电路。
- `_recipe_differentiator()`：基础 RC 微分电路。

后续增加新电路时，优先新增 recipe，并让 `plan_circuit_from_prompt()` 根据用户语义选择 recipe。复杂电路可以逐步改为让 DeepSeek 输出结构化 JSON，再由本地执行器校验和落盘。

## 5. 前端

```text
static/index.html   页面结构（深色侧边栏布局）
static/styles.css   深色主题样式、固定输入区、Thinking 状态
static/app.js       状态管理、API 调用、计划执行、事件绑定
```

`app.js` 的 `applyPlan()` 已支持：

- `schematic.set_property`
- `schematic.add_parts`
- `schematic.generate_circuit`

## 6. 模型 Provider

`provider.py` 中的设计：

- `MockProvider`：无 API Key 时使用，只保留最基础的离线演示能力。
- `OpenAICompatibleProvider`：通用 OpenAI-compatible 调用基类。
- `DeepSeekProvider`：当前真实 API provider，继承 OpenAI-compatible 基类。

新增模型接口时建议：

1. 新增 provider 类。
2. 在 `settings.py` 增加模型配置项。
3. 在 `make_provider()` 中按 provider 名称分发。
4. 保持返回格式为普通 assistant 文本，由本地 parser 解析可执行计划。

## 7. 启动和安装脚本

```text
scripts/install_plugin_gui.cmd   GUI 安装器双击入口
scripts/install_plugin_gui.ps1   GUI 安装器主体（自动检测 + 手动回退）
scripts/install_plugin.ps1       CLI 安装器
scripts/Start-KiCadAIAgent.ps1   桌面快捷方式启动器
scripts/package_beta.ps1         打包脚本
scripts/publish_github.ps1       GitHub 发布脚本
```

`Start-KiCadAIAgent.ps1` 的工程识别顺序：

1. 显式传入 `-Project`。
2. KiCad Schematic Editor 最近文件记录中的 `.kicad_sch`，并映射到同名 `.kicad_pro`。
3. `work/stage2_runtime/last_project.txt`。
4. 样例工程回退。

## 8. 设计原则

- 模型不直接写 KiCad 文件，只生成计划。
- 本地执行器负责落盘、快照和校验。
- 每次写入前创建快照。
- 修改后运行 KiCad CLI 校验。
- 尽量做小 diff，避免全文件重排。
- 每个可执行计划包含 `requires_confirmation`。

## 9. 编译检查

```powershell
python -m py_compile app\kicad_ai_agent\server.py app\kicad_ai_agent\schematic.py app\kicad_ai_agent\provider.py app\scripts\self_test.py
```

PowerShell 启动脚本语法检查：

```powershell
$null = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path .\scripts\Start-KiCadAIAgent.ps1), [ref]$null, [ref]$null)
```

## 10. 发布包

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package_beta.ps1
```

输出：

```text
dist\kicad-ai-agent-beta-v0.2.1-beta.1.zip
```
