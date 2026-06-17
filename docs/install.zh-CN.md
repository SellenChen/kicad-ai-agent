# 安装指南

## 1. 方式 A：GUI 安装器（推荐）

双击运行，完全无需命令行：

```powershell
.\scripts\install_plugin_gui.ps1
```

安装器会：

- **自动检测**本机已安装的 KiCad 版本和插件目录
- 在列表中显示所有检测到的安装，选择目标版本
- **未检测到时**点击「Browse...」手动选择 `scripting\plugins` 目录
- 一键安装插件并创建桌面快捷方式
- 深色主题 UI，与 Agent 侧边栏风格一致

## 2. 方式 B：CLI 安装

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_plugin.ps1
```

脚本会自动检测 KiCad 版本，将插件复制到用户插件目录，并创建桌面快捷方式。

## 3. 检查 KiCad

当前 Beta 默认查找：

```text
C:\Program Files\KiCad\10.0\bin\kicad-cli.exe
```

如安装路径不同，可设置环境变量：

```powershell
$env:KICAD_AGENT_KICAD_CLI="D:\KiCad\10.0\bin\kicad-cli.exe"
```

## 4. 启动方式

### 方式 A：PCB Editor 工具菜单

1. 打开 KiCad PCB Editor
2. 点击 **工具 > KiCad AI Agent**
3. 插件会自动启动本地服务并打开侧边栏窗口

> 首次使用需重启 KiCad 以加载插件。

### 方式 B：桌面快捷方式

双击桌面上的 `KiCad AI Agent.lnk`。

- 如果最近通过 PCB Editor 启动过工程，会自动打开最近工程
- 如果未记录，会弹出文件选择框，让你选择 `.kicad_pro` 或 `.kicad_sch`
- 适用于 **Schematic Editor 工作流**（KiCad 10 的 Python ActionPlugin 不支持原生挂载到原理图编辑器工具菜单）

### 方式 C：命令行启动

```powershell
cd app
python .\run_agent.py --project <你的工程.kicad_pro> --host 127.0.0.1 --port 8765
```

打开 `http://127.0.0.1:8765`。

## 5. 模型配置

侧边栏顶部有模型配置面板：

1. 选择模型 — DeepSeek V4 Pro 或 DeepSeek V4 Flash
2. 输入 API Key — 点击「保存」
3. 是否上传原理图特征 — 默认开启

保存后对话即会调用 DeepSeek API。未配置 API Key 时使用本地 mock 模式，不调用外部模型。

## 6. 运行自测

```powershell
python .\app\scripts\self_test.py
```

自测会复制样例工程并在临时服务上验证所有核心链路。
