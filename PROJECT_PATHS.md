# Project Paths / 项目路径

## Repository / 仓库

- Repository root / 仓库根目录：`.`
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
$env:PYTHONPATH='chronicles\the-unlisted\src'
$py='.\.venv\Scripts\python.exe'

& $py -m the_unlisted.cli check
& $py -m the_unlisted.cli render
& $py -m the_unlisted.cli verify
& $py -m the_unlisted.cli gui
```

Or launch the GUI directly / 或直接启动 GUI：

```powershell
.\run-unlisted-gui.ps1
```

Or / 或：

```text
run-unlisted-gui.cmd
```
