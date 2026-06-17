# v0.2.0-beta.1

KiCad AI Agent Beta 首个可验证版本，及后续持续改进。

## 首发功能

- 本地 Agent 服务和 Web 侧边栏
- KiCad PCB Editor 启动器插件
- 工程/原理图摘要
- 自然语言参数修改计划，例如「把 R4 改成 2K」
- 保格式 `.kicad_sch` 属性修改
- 修改前自动快照，修改后自动 ERC + netlist 校验
- ERC 报告分组解释和修复建议
- SPICE netlist 导出
- KiCad 符号库和封装库搜索
- OpenAI-compatible / DeepSeek 模型接口骨架
- 中文快速开始、安装指南、使用手册、架构说明、开发指南和 FAQ

## Beta 后改进 (已推送到 main 分支)

- **深色侧边栏 UI** — 类 Copilot 风格，固定输入区、独立滚动聊天区
- **模型配置面板** — 侧边栏内直接选择 DeepSeek 模型并保存 API Key
- **原理图特征抽取** — 随对话上传紧凑的工程上下文 JSON
- **Thinking 状态提示** — 模型调用时显示旋转图标和模型名称
- **新增元件初步能力** — 从 Markdown 表格解析并追加 symbol 实例
- **上下文确认执行** — 回复「执行」直接触发上一条可执行计划
- **桌面快捷方式启动器** — 补充 Schematic Editor 无原生插件入口的问题
- **GUI 插件安装器** — 双击运行，自动检测 KiCad 版本，手动选择回退
- **CLI 安装脚本增强** — 自动检测 KiCad 版本，不再硬编码路径
- **自测覆盖扩展** — 加入 add-parts、features、ERC 解释验证
- **settings.py / features.py** — 模型配置持久化 + 原理图特征提取模块
- **开发维护手册** — 完整的项目走查和模块说明

## 验证结果

已在 Windows + KiCad 10.0.x 上完成自测：

- 服务启动成功
- 样例工程摘要成功
- `R4: 1K -> 2K` 保格式 patch 成功
- `R900 / 10K / Device:R` 新增元件成功
- ERC 报告生成成功
- netlist 导出成功
- ERC 解释接口成功（6 个分组）
- 符号/封装库搜索成功
- KiCad 插件启动器验证成功

## 当前限制

- 新增元件不自动连线和布局
- 侧边栏是 Edge App Mode 独立窗口，不是 KiCad 原生 dock panel
- API Key 存储为本地明文 JSON
- 尚未支持流式输出、自动 BOM、PCB 布局修改
