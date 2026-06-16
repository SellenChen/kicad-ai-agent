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

复制：

```text
app\kicad_plugin\kicad_ai_agent_launcher
```

到：

```text
%APPDATA%\kicad\10.0\scripting\plugins\kicad_ai_agent_launcher
```

如果目录不存在，请手动创建。

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

当前 Beta 已预留模型接口，但主要能力仍通过本地工具链验证。
