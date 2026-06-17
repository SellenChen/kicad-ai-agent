# v0.2.1-beta.1

KiCad AI Agent Beta 0.2.1 聚焦 DeepSeek/API 驱动的真实原理图工作能力，并补齐空工程生成、工程自动识别和一键安装体验。

## 新增能力

- **从空工程生成简单电路**：当工程只有 `.kicad_pro` 或原理图为空时，自动创建 `.kicad_sch` 并写入元件、连线、标签和说明文本。
- **简单电路生成器**：支持 1 kHz 方波转三角波 RC 滤波、积分电路、微分电路等基础模块。
- **可执行生成计划**：新增 `schematic.generate_circuit` 工具计划，执行前创建快照，执行后运行 ERC + netlist 校验。
- **工程自动识别增强**：桌面启动器会读取 KiCad Schematic Editor 最近文件记录，尽量自动匹配当前原理图所属工程。
- **DeepSeek Provider 拆分**：保留 OpenAI-compatible 基类，DeepSeek 独立 provider，便于后续扩展新的模型接口。
- **GUI/CLI 安装体验改进**：增加 `scripts/install_plugin_gui.cmd` 双击入口，安装器自动检测 KiCad 版本和插件目录，并创建桌面快捷方式。

## 改进

- 系统提示词明确告知模型可用本地工具：`schematic.set_property`、`schematic.add_parts`、`schematic.generate_circuit`。
- 侧边栏执行逻辑支持生成电路计划的直接应用。
- mock 模式保持最基础能力，后续重点转向真实 API 工作流。
- 自测脚本加入从空工程生成电路的验证，检查 symbol、wire、label 和 netlist 状态。

## 验证结果

已在 Windows + KiCad 10.0.x 环境完成自测：

- 服务启动成功。
- 样例工程摘要成功。
- `R4: 1K -> 2K` 保格式 patch 成功。
- `R900 / 10K / Device:R` 新增元件成功。
- 空工程生成 1 kHz 方波转三角波 RC 滤波电路成功。
- 生成后 netlist 导出成功。
- ERC 报告生成和解释接口成功。
- 符号/封装库搜索成功。
- PowerShell 启动脚本语法检查通过。

## 当前限制

- 自动生成能力当前覆盖简单模拟/RC 电路模板，复杂电路仍需要分阶段规划和人工确认。
- 侧边栏仍为 Edge App Mode 独立窗口，不是 KiCad 原生 dock panel。
- API Key 当前存储为本地明文 JSON。
- 尚未支持流式输出、自动 BOM、PCB 布局修改、复杂 SPICE 仿真闭环。
