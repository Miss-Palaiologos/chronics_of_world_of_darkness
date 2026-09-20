# Project Paths / 项目路径

## Repository / 仓库

- Repository root / 仓库根目录：`.`
- Project file / 工程文件：`pyproject.toml`（唯一）
- Lock file / 锁文件：`uv.lock`（唯一）
- Environment / 环境：`.venv/`（唯一，勿在编年史目录内另建）
- Python pin / Python 版本：`.python-version`
- Shared setting guide / 共享世界观：`docs/vtm-v5-setting-guide.md`
- Shared writing notes / 共享写作技法：`docs/scenario-writing-and-structure-notes.md`
- Reference scripts / 参考剧本：`reference/*.docx`
- Chronicle index / 编年史索引：`chronicles/README.md`

## The Unlisted / 《不在册者》

- Chronicle root / 编年史根目录：`chronicles/the-unlisted/`
- Version / 版本：`chronicles/the-unlisted/VERSION`
- Changelog / 版本记录：`chronicles/the-unlisted/CHANGELOG.md`
- Data / 数据：`chronicles/the-unlisted/data/`
- Source / 代码：`chronicles/the-unlisted/src/the_unlisted/`
- Docs / 文档：`chronicles/the-unlisted/docs/`
- Acts / 幕文件：`chronicles/the-unlisted/docs/acts/act-01.md` ... `act-06.md`
- Roster / 名册总表：`chronicles/the-unlisted/docs/roster.md`
- Dashboard / 图形看板：`chronicles/the-unlisted/docs/dashboard.html`

## Commands / 命令

From repository root / 从仓库根目录运行：

```powershell
# 首次或依赖变化时
uv sync

# 日常
uv run the-unlisted check
uv run the-unlisted render
uv run the-unlisted verify
uv run the-unlisted finale

# 或者直接用共享环境的解释器
.\.venv\Scripts\python.exe -m the_unlisted.cli check
```

New chronicle / 新增一部编年史：

```text
1. 在 chronicles/ 下建立新目录，放 data/、docs/、src/<包名>/
2. 在根 pyproject.toml 里补一行命令行入口，并把 build-backend 的 module-root
   指向新编年史的 src/（或把各编年史源码统一到仓库根 src/ 后设 module-root = "src"）
3. 回到仓库根目录跑 uv sync
4. 不要在新目录里另建 .venv
```

Or launch the GUI directly / 或直接启动 GUI（需要带 Tcl/Tk 的解释器）：

```powershell
.\run-unlisted-gui.ps1
$env:CHRONICS_PYTHON = 'C:\path\to\python.exe'; .\run-unlisted-gui.ps1
```

Or / 或：

```text
run-unlisted-gui.cmd
```
