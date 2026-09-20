# 项目路径

## 当前剧本

- 标题：**《不在册者》**
- 项目根目录：`the-unlisted/`
- 数据目录：`the-unlisted/data/`
- 源目录：`the-unlisted/src/the_unlisted/`
- 剧本文档：`the-unlisted/docs/`
- 幕文件：`the-unlisted/docs/acts/act-01.md` 至 `act-06.md`
- 名册总表：`the-unlisted/docs/roster.md`
- 图形看板：`the-unlisted/docs/dashboard.html`
- 项目说明：`the-unlisted/README.md`
- 系统说明：`the-unlisted/docs/system.md`

## 共享资料

- 世界观总结：`docs/vtm-v5-setting-guide.md`
- 写作技法总结：`docs/scenario-writing-and-structure-notes.md`
- 参考剧本：`reference/*.docx`

## 运行

```powershell
cd D:\trpg\wod\chronics\the-unlisted
$env:PYTHONPATH='src'
$py='..\.venv\Scripts\python.exe'

& $py -m the_unlisted.cli check
& $py -m the_unlisted.cli render
& $py -m the_unlisted.cli verify
& $py -m the_unlisted.cli gui
```
