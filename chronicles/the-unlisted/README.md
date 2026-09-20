# The Unlisted / 不在册者

> A VTM V5 modern-night chronicle project.
>
> 一部 VTM V5 现代之夜编年史项目。

## Quick Start / 快速开始

```powershell
# 从仓库根目录：整个仓库只有一个工程、一个环境
uv sync

uv run the-unlisted check
uv run the-unlisted render
uv run the-unlisted verify
uv run the-unlisted run --profile normal --seed 5
uv run the-unlisted finale
uv run the-unlisted balance --profile normal

# GUI 需要带 Tcl/Tk 的解释器（uv 托管的 CPython 目前没有）
.\run-unlisted-gui.ps1
```

## Documentation / 文档

- `docs/index.md` — ST quick start / 主持人入口
- `docs/system.md` — rules, factions, acts / 规则、派系与幕结构
- `docs/acts/` — act files / 幕文件
- `docs/roster.md` — characters, props, rules lookup / 名册与规则索引
- `docs/dashboard.html` — static dashboard / 静态看板

## Version / 版本

Current release: **1.0.7**

当前版本：**1.0.7**
