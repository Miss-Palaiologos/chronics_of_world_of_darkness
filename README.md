# Chronicles of the World of Darkness / 黑暗世界编年史

> A bilingual repository for multiple World of Darkness / Vampire: The Masquerade V5 chronicles.
>
> 一个用于长期维护多部《黑暗世界》/《吸血鬼：避世潜藏》第五版编年史的双语仓库。

## Repository Model / 仓库模型

This repository is a **collection**, not a single scenario. Each chronicle lives in its own folder under `chronicles/`, with its own data, source code, docs, version, and changelog.

本仓库是一个**多编年史容器**，而不是单部剧本。每部编年史位于 `chronicles/` 下的独立目录，拥有自己的数据、代码、文档、版本号与版本记录。

```text
.
├── PROJECT_PATHS.md                   # Path registry / 路径索引
├── README.md                          # Repository index / 仓库入口
├── docs/                              # Shared guides / 共享资料
│   ├── vtm-v5-setting-guide.md
│   └── scenario-writing-and-structure-notes.md
├── reference/                          # Shared reference scripts / 共享参考剧本
└── chronicles/
    └── the-unlisted/                   # The Unlisted / 《不在册者》
        ├── VERSION
        ├── CHANGELOG.md
        ├── data/
        ├── docs/
        └── src/the_unlisted/
```

## Chronicles / 编年史列表

| Chronicle / 编年史 | Folder / 目录 | Version / 版本 | Status / 状态 |
| --- | --- | --- | --- |
| **The Unlisted / 《不在册者》** | `chronicles/the-unlisted/` | `1.0.0` | Public draft / 公开初稿 |

## Quick Start / 快速开始

Run from the repository root:

从仓库根目录运行：

```powershell
$env:PYTHONPATH='chronicles\the-unlisted\src'
$py='.\.venv\Scripts\python.exe'

& $py -m the_unlisted.cli check
& $py -m the_unlisted.cli render
& $py -m the_unlisted.cli verify
& $py -m the_unlisted.cli run --profile normal --seed 5
& $py -m the_unlisted.cli gui
```

Or use the launcher script:

或直接使用启动脚本：

```powershell
.\run-unlisted-gui.ps1
```

Or double-click / run / 或直接运行：

```text
run-unlisted-gui.cmd
```

If `$py` is not defined in your current PowerShell session, use the full path:

如果当前 PowerShell 会话里没有 `$py` 变量，直接使用完整路径：

```powershell
.\.venv\Scripts\python.exe -m the_unlisted.cli gui
```

## Versioning / 版本管理

- Each chronicle owns its own `VERSION` and `CHANGELOG.md`.
- Git tags are namespaced by chronicle: `the-unlisted-v1.0.0`.
- Shared guides and reference files do not carry chronicle version numbers.
- Generated documents are produced from each chronicle's own `data/` folder.

- 每部编年史独立维护 `VERSION` 与 `CHANGELOG.md`。
- Git 标签按编年史命名，例如 `the-unlisted-v1.0.0`。
- 共享资料与参考文件不绑定单部编年史的版本号。
- 生成文档从各自编年史的 `data/` 目录产出。

## Rights / 权利说明

Original chronicle material and code belong to their respective authors. Files under `reference/` are third-party translations or reference scripts and remain subject to their own rights.

原创编年史材料与代码归各自作者所有；`reference/` 下为第三方翻译或参考剧本，权利归原权利人所有。
