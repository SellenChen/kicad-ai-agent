# 安装指南

## 1. 下载 Beta Release

从 GitHub Release 下载：

```text
kicad-ai-agent-beta-v0.2.0-beta.1.zip
```

解压到任意目录，例如：

```text
C:\Users\<你的用户名>\Documents\kicad-ai-agent
```

## 2. 检查 KiCad

当前 Beta 默认查找：

```text
C:\Program Files\KiCad\10.0\bin\kicad-cli.exe
```

如安装路径不同，可设置环境变量：

```powershell
$env:KICAD_AGENT_KICAD_CLI="D:\KiCad\10.0\bin\kicad-cli.exe"
```

## 3. 安装 KiCad 插件

推荐直接运行安装脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_plugin.ps1
```

脚本会自动清理旧插件并复制新版插件到：

```text
%APPDATA%\kicad\10.0\scripting\plugins\kicad_ai_agent_launcher
```

如果 KiCad 已经打开，请重启 KiCad 或 PCB Editor，让它重新加载插件。

## 4. 启动

### 方法 A：命令行启动

```powershell
cd app
python .\run_agent.py --project <你的工程.kicad_pro> --host 127.0.0.1 --port 8765
```

打开：

```text
http://127.0.0.1:8765
```

### 方法 B：KiCad 插件启动

1. 打开 KiCad。
2. 打开 PCB Editor。
3. 刷新插件或重启 KiCad。
4. 点击 `KiCad AI Agent`。

## 5. 配置模型

默认不调用外部模型，使用 mock provider。

如果要接入 DeepSeek 或 OpenAI-compatible API：

```powershell
$env:KICAD_AGENT_MODEL_BASE_URL="https://api.deepseek.com"
$env:KICAD_AGENT_API_KEY="<你的 API Key>"
$env:KICAD_AGENT_MODEL="<模型名称>"
```

侧边栏顶部也可以直接选择 DeepSeek 模型并保存 API Key。当前可选：

- DeepSeek V4 Pro
- DeepSeek V4 Flash

保存后，对话会随请求上传紧凑的原理图特征 JSON，帮助模型理解当前工程。
