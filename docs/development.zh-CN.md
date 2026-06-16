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
kicad_ai_agent/schematic.py    原理图读取、计划和保格式 patch
kicad_ai_agent/kicad_cli.py    KiCad CLI 封装
kicad_ai_agent/diagnostics.py  环境诊断和 ERC 解释
kicad_ai_agent/library.py      符号/封装搜索
kicad_ai_agent/provider.py     模型 Provider
kicad_ai_agent/sexpr.py        S-expression parser
```

## 4. 添加新工具

建议流程：

1. 在 `kicad_ai_agent` 中实现纯工具函数。
2. 在 `server.py` 中暴露 API。
3. 在 `static/app.js` 中接入 UI。
4. 在 `scripts/self_test.py` 中加入自测。
5. 更新中文文档。

## 5. 设计原则

- 所有写文件操作前创建快照。
- 模型不直接写 KiCad 文件。
- 工具调用必须可审查。
- 修改后必须运行 KiCad CLI 校验。
- 以小 diff 为目标，避免全文件重排。

## 6. 发布包

生成 Beta zip：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package_beta.ps1
```

输出：

```text
dist\kicad-ai-agent-beta-v0.2.0-beta.1.zip
```
