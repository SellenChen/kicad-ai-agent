# 架构说明

当前版本：`0.2.2`。

## 1. 总体架构

```text
KiCad PCB Editor 插件 / 桌面快捷方式
  -> 本地 Agent 服务 (127.0.0.1:8765)
  -> 深色 Web 侧边栏 (Edge App Mode)
  -> KiCad 工具层
      -> .kicad_sch 解析/patch/生成 (schematic.py + sexpr.py)
      -> kicad-cli ERC/netlist/SPICE (kicad_cli.py)
      -> KiCad 符号/封装库搜索 (library.py)
  -> 原理图特征提取 (features.py)
  -> 模型配置持久化 (settings.py)
  -> 模型 Provider 层 (provider.py)
      -> MockProvider（无 API Key，基础演示）
      -> DeepSeekProvider（当前主路径）
      -> OpenAICompatibleProvider（扩展基类）
```

## 2. 启动链路

两种启动方式：

1. **PCB Editor 插件**：`pcbnew.ActionPlugin` 获取工程路径，启动本地服务，打开 Edge App Mode 侧边栏，并写入 `last_project.txt`。
2. **桌面快捷方式**：读取显式参数、KiCad Schematic Editor 最近文件记录或 `last_project.txt`，复用已有服务或启动新服务。

桌面快捷方式用于补齐 KiCad 10 Schematic Editor 不能原生挂载 Python ActionPlugin 工具菜单的问题。

## 3. 工程自动识别

`scripts/Start-KiCadAIAgent.ps1` 中的 `Get-AgentProject` 会按顺序尝试：

- 命令行 `-Project`。
- `%APPDATA%\kicad\**\eeschema.json` 中最近打开的 `.kicad_sch`。
- 与 `.kicad_sch` 同名的 `.kicad_pro`。
- `work/stage2_runtime/last_project.txt`。
- 样例工程。

这使用户从原理图编辑器工作流打开 Agent 时，更容易自动绑定当前工程。

## 4. 原理图修改策略

Beta 采用结构化读取 + 原文局部替换。

### 修改 Value

1. 正则定位 `(property "Reference" "R4")`。
2. 向前查找所属 `(symbol ...)` 起点。
3. 用 `_matching_paren` 找到完整 symbol 块。
4. 在 symbol 块中定位 Value 属性。
5. 仅替换值字符串。
6. 保存前创建快照。
7. 保存后调用 KiCad CLI 校验。

### 新增元件

1. 从模型回复 Markdown 表格或结构化计划解析元件信息。
2. 过滤已存在 Reference。
3. 用 `_symbol_block()` 生成 KiCad symbol 实例。
4. 追加到 `.kicad_sch` 根节点闭合括号前。
5. 写入前创建快照。
6. 写入后运行 ERC + netlist。

### 生成简单电路

1. `plan_circuit_from_prompt()` 根据用户输入识别生成意图。
2. 内置 recipe 生成 components、wires、labels、junctions、notes。
3. 前端显示 `schematic.generate_circuit` 可执行计划。
4. 用户确认后调用 `generate_circuit_preserving_format()`。
5. 执行器写入 symbol、wire、label、junction、text。
6. 自动创建快照并运行 KiCad CLI 校验。

优点：diff 小、用户容易审查、不重排完整文件。

## 5. KiCad CLI

KiCad CLI 用于可靠校验和导出：

- `sch erc`：电气规则检查。
- `sch export netlist`：导出 netlist。
- `sch export netlist --format spice`：导出 SPICE netlist。
- `pcb drc`：PCB 设计规则检查（预留）。

## 6. 模型层

当前真实工作路径是 DeepSeek：

- `settings.py` 保存模型、API Key 和是否上传特征。
- `features.py` 抽取紧凑工程上下文 JSON。
- `provider.py` 调用 DeepSeek API。
- `server.py` 将模型回复和本地 parser 组合成可执行计划。

mock 模式只保留基础演示，不再作为主要开发方向。

## 7. 数据流

```text
用户输入 -> app.js -> POST /api/chat -> server.py
  -> provider.py -> DeepSeek API
  -> features.py（上传原理图上下文）
  -> schematic.py（plan_from_prompt / plan_parts_from_text / plan_circuit_from_prompt）
  -> 生成可执行计划 JSON
  -> 用户确认 -> _execute_plan
    -> create_snapshot
    -> set_property_preserving_format / add_parts_preserving_format / generate_circuit_preserving_format
    -> validate_schematic (ERC + netlist)
  -> 返回校验结果
```

## 8. 关键目录

```text
app/kicad_ai_agent/      后端服务层
app/static/              深色侧边栏
app/kicad_plugin/         KiCad ActionPlugin 启动器
app/samples/              样例工程
scripts/                  安装/打包/发布/启动脚本
docs/                     中文文档
work/stage1_runtime/      settings、snapshots、reports
work/stage2_runtime/      last_project、logs
```
