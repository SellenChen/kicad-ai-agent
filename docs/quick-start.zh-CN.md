# 快速开始

本文档用于快速运行 KiCad AI Agent Beta。

## 1. 环境要求

- Windows 10/11
- KiCad 10.0.x
- Python 3.11 或更高版本

本项目已在以下环境验证：

```text
KiCad 10.0.x
Python 3.13
Windows
```

## 2. 安装插件

### 推荐：GUI 安装器

双击运行，无需命令行：

```powershell
.\scripts\install_plugin_gui.cmd
```

安装器自动检测 KiCad 版本，一站式安装插件 + 桌面快捷方式。

### 备选：CLI 安装

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_plugin.ps1
```

## 3. 启动本地 Agent

### 命令行启动

```powershell
cd app
python .\run_agent.py --project .\samples\amplifier-ac-stage1\amplifier-ac.kicad_pro --host 127.0.0.1 --port 8765
```

浏览器打开 `http://127.0.0.1:8765`。

### 通过 KiCad 启动

打开 KiCad PCB Editor，点击 **工具 > KiCad AI Agent**，插件会自动启动服务并打开侧边栏。

### 通过桌面快捷方式启动

双击桌面上的 `KiCad AI Agent.lnk`（由安装脚本自动创建）。

## 4. 配置模型

侧边栏顶部模型配置面板：

1. 选择 DeepSeek V4 Pro 或 DeepSeek V4 Flash
2. 输入 API Key，点击「保存」
3. 未配置 API Key 时使用本地 mock 模式

## 5. 试用对话

在输入框中输入：

```text
把 R4 改成 2K
```

Agent 会：
1. 显示 Thinking 状态
2. 生成可执行计划
3. 显示在计划面板中
4. 点击「执行并校验」或直接回复「执行」

## 6. 运行自测

```powershell
python .\app\scripts\self_test.py
```

自测验证：

- 服务启动
- 工程摘要
- set_value 预览和执行
- add_parts 执行
- ERC/netlist 校验
- ERC 解释
- 符号/封装库搜索
- 环境诊断

## 7. 从空工程生成简单电路

在空工程或已有工程中输入：

```text
请生成一个1kHz方波转三角波的滤波电路
```

Agent 会生成可执行计划。点击“执行并校验”后，会自动放置元件、连线、标签，并运行 ERC + netlist 校验。
