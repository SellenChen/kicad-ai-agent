# 架构说明

## 1. 总体架构

```text
KiCad PCB Editor 插件
  -> 本地 Agent 服务
  -> Web 侧边栏
  -> KiCad 工具层
      -> .kicad_sch 解析/patch
      -> kicad-cli ERC/DRC/netlist
      -> KiCad 符号/封装库搜索
  -> 模型 Provider
      -> MockProvider
      -> OpenAI-compatible Provider
```

## 2. 为什么使用外部侧边栏

KiCad 当前 Python Action Plugin 对 PCB Editor 支持较好，但不适合作为完整原理图侧边栏 UI。Beta 版本采用外部 Web 侧边栏：

- 开发速度快。
- 不需要修改 KiCad 源码。
- 可以独立迭代 UI 和 Agent 后端。
- 后续可替换为 WebView2 或 Qt 容器。

## 3. 原理图修改策略

Beta 采用：

```text
结构化读取 + 原文局部替换
```

流程：

1. 解析 `.kicad_sch`。
2. 定位目标 symbol。
3. 定位目标 property。
4. 只替换属性值。
5. 保存前创建快照。
6. 保存后调用 KiCad CLI 校验。

优点：

- diff 小。
- 用户容易审查。
- 不会重排整个文件。

## 4. KiCad CLI

KiCad CLI 用于可靠校验和导出：

- `sch erc`
- `sch export netlist`
- `sch export netlist --format spice`
- `pcb drc`

## 5. 模型层

当前 Beta 默认使用 `MockProvider`，不上传工程内容。

如配置环境变量，可使用 OpenAI-compatible provider：

```text
KICAD_AGENT_MODEL_BASE_URL
KICAD_AGENT_API_KEY
KICAD_AGENT_MODEL
```

后续阶段会将工具调用、上下文裁剪和隐私策略做成正式模块。

## 6. 关键目录

```text
app/kicad_ai_agent      后端服务和工具层
app/static              Web 侧边栏
app/kicad_plugin        KiCad 启动器插件
app/samples             样例工程
docs                    中文文档
work/stage1_runtime     快照和报告输出
```
