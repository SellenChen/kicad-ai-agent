# v0.2.2-beta.1

KiCad AI Agent Beta 0.2.2 修复 PCB Editor 插件启动时可能进入旧工程的问题，并进一步加固工程路径识别。

## 关键修复

- **修复错误复用旧 Agent 服务**：插件不再只检查 `api/health`。现在必须同时确认 `/api/project` 返回的工程路径与当前 KiCad 工程一致，才会复用已有服务。
- **自动换端口启动新工程实例**：如果 `8765` 上已有旧工程服务，插件会自动尝试 `8766` 起的可用端口，避免打开旧项目。
- **增强 KiCad 工程推断**：插件会从 `pcbnew.GetBoard().GetFileName()`、KiCad project 对象、当前工作目录、KiCad 最近文件记录等多来源推断当前工程。
- **路径归一化**：当识别到 `.kicad_pcb` 或 `.kicad_sch` 时，优先映射到同名 `.kicad_pro`。
- **启动日志继续写入**：每次启动仍会更新 `work/stage2_runtime/last_project.txt` 和 `logs/kicad_plugin_launch.log`，便于排查。

## 继承自 0.2.1 的能力

- 从空工程自动创建最小 `.kicad_sch`。
- 支持 1 kHz 方波转三角波 RC 滤波、基础积分电路、基础微分电路模板。
- `schematic.generate_circuit` 可执行工具会写入元件、连线、标签、junction 和说明文本。
- 写入后自动运行 ERC + netlist 校验。
- DeepSeek Provider 独立化，mock 模式保持基础演示。

## 验证结果

- Python 编译检查通过。
- PowerShell 启动脚本语法检查通过。
- 插件 launcher 编译检查通过。
- `self_test.py` 通过，包括空工程生成电路和 netlist 校验。

## 当前限制

- 自动生成能力当前覆盖简单模拟/RC 电路模板，复杂电路仍需要分阶段规划和人工确认。
- 侧边栏仍为 Edge App Mode 独立窗口，不是 KiCad 原生 dock panel。
- API Key 当前存储为本地明文 JSON。
- 尚未支持流式输出、自动 BOM、PCB 布局修改、复杂 SPICE 仿真闭环。
