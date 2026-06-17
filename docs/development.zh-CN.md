# 开发指南

## 1. 本地运行

```powershell
cd app
python .\run_agent.py --project .\samples\amplifier-ac-stage1\amplifier-ac.kicad_pro --host 127.0.0.1 --port 8765
```

## 2. 自测

```powershell
python .\app\scripts\self_test.py
```

## 3. 主要模块

```text
kicad_ai_agent/server.py       HTTP API 和静态页面服务
kicad_ai_agent/schematic.py    原理图读取、计划、保格式 patch、新增元件
kicad_ai_agent/kicad_cli.py    KiCad CLI 封装 (ERC/netlist/SPICE)
kicad_ai_agent/features.py     原理图特征抽取（随对话上传）
kicad_ai_agent/settings.py     模型配置持久化 (settings.json)
kicad_ai_agent/provider.py     模型 Provider (Mock + OpenAI-compatible)
kicad_ai_agent/diagnostics.py  环境诊断和 ERC 解释
kicad_ai_agent/library.py      符号/封装搜索
kicad_ai_agent/sexpr.py        S-expression 解析器
kicad_ai_agent/paths.py        路径常量和运行目录管理
```

## 4. 前端

```text
static/index.html   页面结构（深色侧边栏布局）
static/styles.css   深色主题样式
static/app.js       状态管理、API 调用、计划执行、事件绑定
```

## 5. 脚本

```text
scripts/install_plugin_gui.ps1   GUI 安装器（自动检测 + 手动回退）
scripts/install_plugin.ps1       CLI 安装器
scripts/Start-KiCadAIAgent.ps1   桌面快捷方式启动器
scripts/package_beta.ps1         打包脚本
scripts/publish_github.ps1       发布脚本
```

## 6. 添加新工具

建议流程：

1. 在 `kicad_ai_agent` 中实现纯工具函数
2. 在 `server.py` 中暴露 API
3. 在 `static/app.js` 中接入 UI
4. 在 `app/scripts/self_test.py` 中加入自测
5. 更新中文文档

## 7. 设计原则

- 所有写文件操作前创建快照
- 模型不直接写 KiCad 文件
- 工具调用必须可审查（先计划，再确认，再执行）
- 修改后必须运行 KiCad CLI 校验
- 以小 diff 为目标，避免全文件重排
- 每个可执行计划包含 `requires_confirmation` 标志

## 8. 编译检查

```powershell
python -m py_compile app\kicad_ai_agent\server.py app\kicad_ai_agent\schematic.py app\kicad_ai_agent\provider.py
```

## 9. 发布包

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package_beta.ps1
```

输出：

```text
dist\kicad-ai-agent-beta-v0.2.0-beta.1.zip
```
