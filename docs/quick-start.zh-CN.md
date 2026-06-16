# 快速开始

本文档用于快速运行 KiCad AI Agent Beta。

## 1. 环境要求

- Windows 10/11
- KiCad 10.0.x
- Python 3.11 或更高版本

本项目已在以下环境验证：

```text
KiCad 10.0.3
Python 3.13
Windows
```

## 2. 启动本地 Agent

在项目根目录运行：

```powershell
cd app
python .\run_agent.py --project .\samples\amplifier-ac-stage1\amplifier-ac.kicad_pro --host 127.0.0.1 --port 8765
```

打开浏览器：

```text
http://127.0.0.1:8765
```

## 3. 试用自然语言修改

在输入框中输入：

```text
把 R4 改成 2K
```

Agent 会生成工具计划，点击：

1. `预览`
2. `执行并校验`

执行后会：

- 创建快照
- 修改 `.kicad_sch`
- 运行 ERC
- 导出 netlist
- 显示结果

## 4. 运行自测

在项目根目录运行：

```powershell
python .\app\scripts\self_test.py
```

自测会自动验证：

- 服务启动
- 工程摘要
- 工具计划
- 保格式 patch
- ERC 校验
- netlist 导出
- ERC 解释
- 符号/封装库搜索

## 5. 通过 KiCad 启动

将插件目录复制到 KiCad 用户插件目录：

```text
app\kicad_plugin\kicad_ai_agent_launcher
```

目标路径：

```text
%APPDATA%\kicad\10.0\scripting\plugins\kicad_ai_agent_launcher
```

然后打开 KiCad PCB Editor，刷新或重启插件，点击 `KiCad AI Agent`。
