# 架构说明

## 1. 总体架构

```text
KiCad PCB Editor 插件 / 桌面快捷方式
  -> 本地 Agent 服务 (127.0.0.1:8765)
  -> 深色 Web 侧边栏 (Edge App Mode)
  -> KiCad 工具层
      -> .kicad_sch 解析/patch (schematic.py + sexpr.py)
      -> kicad-cli ERC/netlist/SPICE (kicad_cli.py)
      -> KiCad 符号/封装库搜索 (library.py)
  -> 原理图特征提取 (features.py)
  -> 模型配置持久化 (settings.py)
  -> 模型 Provider 层 (provider.py)
      -> MockProvider (无 API Key)
      -> OpenAICompatibleProvider (DeepSeek / 自定义)
```

## 2. 启动链路

两种启动方式：

1. **PCB Editor 插件**：`pcbnew.ActionPlugin` -> 获取工程路径 -> 启动本地服务 -> Edge App Mode 打开侧边栏 -> 写入 `last_project.txt`
2. **桌面快捷方式**：读取 `last_project.txt` 获取最近工程 -> 复用已有服务或启动新服务 -> 打开侧边栏

桌面快捷方式解决了 KiCad 10 Schematic Editor 不支持 Python ActionPlugin 的限制。

## 3. 为什么使用外部侧边栏

KiCad 当前 Python Action Plugin 对 PCB Editor 支持较好，但不适合作为完整原理图侧边栏 UI。Beta 版本采用外部 Web 侧边栏：

- 开发速度快
- 不需要修改 KiCad 源码
- 可以独立迭代 UI 和 Agent 后端
- 后续可替换为 WebView2 或 Qt 容器

## 4. 原理图修改策略

Beta 采用**结构化读取 + 原文局部替换**：

**修改 Value 流程**：
1. 正则定位 `(property "Reference" "R4")`
2. 向前查找所属 `(symbol ...)` 起点
3. 用 `_matching_paren` 找到完整 symbol 块
4. 在 symbol 块中定位 value 字符串
5. 只替换值字符串，不重写整个 S-expression
6. 保存前创建快照
7. 保存后调用 KiCad CLI 校验

**新增元件流程**：
1. 从模型回复 Markdown 表格解析元件信息
2. 过滤已存在的 Reference
3. 用 `_symbol_block` 生成 KiCad symbol 实例
4. 追加到 `.kicad_sch` 根节点闭合括号前
5. 写入前创建快照
6. 写入后运行 ERC + netlist 校验

优点：diff 小、用户容易审查、不会重排整个文件。

## 5. KiCad CLI

KiCad CLI 用于可靠校验和导出：

- `sch erc` — 电气规则检查
- `sch export netlist` — 导出 netlist
- `sch export netlist --format spice` — 导出 SPICE netlist
- `pcb drc` — PCB 设计规则检查（预留）

## 6. 模型层

当前支持两种 provider：

- **MockProvider**：无 API Key 时使用，返回预设回复，不上传工程信息
- **OpenAICompatibleProvider**：配置 API Key 后使用，支持 DeepSeek 及任何 OpenAI-compatible API

模型配置通过侧边栏保存到 `work/stage1_runtime/settings.json`，由 `settings.py` 管理。

侧边栏开启「随对话上传原理图特征」时，`features.py` 会提取工程特征 JSON 作为 system message 传给模型。

## 7. 关键目录

```text
app/kicad_ai_agent/      后端服务层 (server, schematic, kicad_cli, features, settings, provider, ...)
app/static/              深色侧边栏 (index.html, app.js, styles.css)
app/kicad_plugin/         KiCad ActionPlugin 启动器
app/samples/              样例工程
scripts/                  安装/打包/发布/启动脚本
docs/                     中文文档
work/stage1_runtime/      运行时数据 (settings.json, snapshots/, reports/)
work/stage2_runtime/      插件启动记录 (last_project.txt, logs/)
```

## 8. 数据流

```text
用户输入 -> app.js -> POST /api/chat -> server.py
  -> provider.py -> DeepSeek API (or MockProvider)
  -> features.py (上传原理图上下文)
  -> schematic.py (plan_from_prompt / plan_parts_from_text)
  -> 生成可执行计划 JSON
  -> 用户确认 -> _execute_plan
    -> create_snapshot
    -> set_property_preserving_format / add_parts_preserving_format
    -> validate_schematic (ERC + netlist)
  -> 返回校验结果
```
