# 使用手册

## 1. 界面组成

侧边栏包含：

- 工程路径
- 原理图摘要
- Chat 对话区
- 工具按钮
- 符号/封装搜索
- 待执行计划面板

## 2. 工程摘要

启动后会自动读取当前工程的 `.kicad_sch`，显示：

- 符号数量
- 连线数量
- 标签数量
- KiCad schematic version

## 3. 修改元件参数

输入：

```text
把 R4 改成 2K
```

Agent 会生成计划：

```text
tool: schematic.set_property
reference: R4
property: Value
old_value: 1K
new_value: 2K
```

点击 `预览` 可以查看 diff。

点击 `执行并校验` 后，Agent 会：

1. 创建快照。
2. 修改原理图。
3. 运行 ERC。
4. 导出 netlist。
5. 显示结果。

## 4. ERC + Netlist

点击 `ERC + Netlist`：

- 运行 KiCad ERC。
- 导出 KiCad netlist。
- 显示违规数量和导出状态。

## 5. 解释 ERC

点击 `解释 ERC`：

- 自动运行 ERC。
- 分组整理违规类型。
- 给出常见修复建议。

例如：

```text
Input Power pin not driven by any Output Power pins
建议：检查电源输入脚是否由电源输出脚或 PWR_FLAG 驱动。
```

## 6. 导出 SPICE

点击 `导出 SPICE`：

- 调用 `kicad-cli sch export netlist --format spice`
- 输出 `.cir` 文件到运行报告目录

注意：SPICE 导出可能需要 KiCad 用户配置目录访问权限。

## 7. 搜索符号和封装

在搜索框输入关键词，例如：

```text
Device
SOT
```

点击：

- `符号`
- `封装`

Agent 会搜索 KiCad 默认库目录并返回匹配结果。

## 8. 快照

每次执行修改前，系统会保存快照到：

```text
work\stage1_runtime\snapshots
```

点击 `快照` 可查看最近快照。

当前 Beta 已提供恢复接口，但 UI 中尚未加入一键恢复按钮。
