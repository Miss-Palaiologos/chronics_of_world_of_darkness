# Chronicles of the World of Darkness / 黑暗世界编年史

> A bilingual repository for multiple World of Darkness / Vampire: The Masquerade V5 chronicles.
>
> 一个用于长期维护多部《黑暗世界》/《吸血鬼：避世潜藏》第五版编年史的双语仓库。

## Repository Model / 仓库模型

This repository is a **collection**, not a single scenario. Each chronicle lives in its own folder under `chronicles/`, with its own data, source code, docs, version, and changelog.

本仓库是一个**多编年史容器**，而不是单部剧本。每部编年史位于 `chronicles/` 下的独立目录，拥有自己的数据、代码、文档、版本号与版本记录。

```text
.
├── pyproject.toml                     # The only project file / 唯一的工程文件
├── uv.lock                            # The only lock file / 唯一的锁文件
├── .venv/                             # The only environment / 唯一的环境
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
| **The Unlisted / 《不在册者》** | `chronicles/the-unlisted/` | `1.0.9` | Public draft / 公开初稿 |

## Quick Start / 快速开始

**One project, one environment.** The repository root is the only [uv](https://docs.astral.sh/uv/) project: one `pyproject.toml`, one `uv.lock`, one `.venv`. Chronicle folders hold content and code, not their own environments or package manifests.

**一个工程，一个环境。** 仓库根目录是唯一的 uv 工程：一份 `pyproject.toml`、一份 `uv.lock`、一个 `.venv`。编年史目录只放内容与代码，不再各自建环境或维护独立的包清单。

```powershell
# 第一次使用，或改了 pyproject 之后：在仓库根目录同步一次
uv sync

# 之后可以直接跑（编年史代码已经装进根目录的 .venv）
uv run the-unlisted check
uv run the-unlisted render
uv run the-unlisted verify

# 也可以用共享环境的解释器，不需要 PYTHONPATH
.\.venv\Scripts\python.exe -m the_unlisted.cli check
.\.venv\Scripts\python.exe -m the_unlisted.cli finale
```

| 命令 | 用途 |
| --- | --- |
| `uv sync` | 在根目录同步工程依赖 |
| `uv lock` | 更新根目录的 `uv.lock` |
| `uv run the-unlisted <子命令>` | 不解锁直接运行编年史命令 |
| `uv add <包>` | 给工程加依赖 |

## GUI / 图形界面

图形界面需要当前解释器带可用的 Tcl/Tk。**uv 托管的 CPython 目前不带可用的 Tcl/Tk**，所以 GUI 要用 python.org 安装版或 conda 环境来跑；命令行推演不受影响。

The GUI needs a Python with a working Tcl/Tk. The uv-managed CPython currently ships without usable Tcl/Tk, so run the GUI with a python.org or conda interpreter; the CLI is unaffected.

启动脚本会自动挑选一个带 Tk 的解释器（也可以先用 `$env:CHRONICS_PYTHON` 指定）：

The launcher picks a Tk-capable interpreter automatically (or set `$env:CHRONICS_PYTHON` first):

```powershell
.\run-unlisted-gui.ps1
$env:CHRONICS_PYTHON = 'C:\path\to\python.exe'; .\run-unlisted-gui.ps1
```

```text
run-unlisted-gui.cmd
```

## Versioning / 版本管理

- Each chronicle owns its own `VERSION` and `CHANGELOG.md`.
- Git tags are namespaced by chronicle: `the-unlisted-v1.0.0`.
- Shared guides and reference files do not carry chronicle version numbers.
- Generated documents are produced from each chronicle's own `data/` folder.
- The project file, lock file, and virtual environment live at the repository root; chronicle folders hold content and code, not environments.
- All chronicle Python code is packaged by the single root project (`tool.uv.build-backend` points at the chronicle source tree); command-line entry points live in the root `pyproject.toml`.

- 每部编年史独立维护 `VERSION` 与 `CHANGELOG.md`。
- Git 标签按编年史命名，例如 `the-unlisted-v1.0.0`。
- 共享资料与参考文件不绑定单部编年史的版本号。
- 生成文档从各自编年史的 `data/` 目录产出。
- 工程配置、锁文件与虚拟环境放在仓库根目录；编年史目录只放内容与代码，不再各自建环境。
- 编年史的 Python 代码由根工程统一打包（`tool.uv.build-backend` 指向编年史源码树），命令行入口写在根 `pyproject.toml`。

## Rights / 权利说明

Original chronicle material and code belong to their respective authors. Files under `reference/` are third-party translations or reference scripts and remain subject to their own rights.

原创编年史材料与代码归各自作者所有；`reference/` 下为第三方翻译或参考剧本，权利归原权利人所有。
