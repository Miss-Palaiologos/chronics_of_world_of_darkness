# 《不在册者》· 主持人入口

本作共 **六幕、八个场景**。

## 快速运行

在项目根目录运行：

```powershell
$env:PYTHONPATH='src'
$py='..\..\.venv\Scripts\python.exe'

& $py -m the_unlisted.cli check
& $py -m the_unlisted.cli render
& $py -m the_unlisted.cli verify
& $py -m the_unlisted.cli run --profile normal --seed 5
```

需要图形界面时：

```powershell
& $py -m the_unlisted.cli gui
```

图形界面会显示当前场景描写、当前幕变体、下一幕变体条件、世界状态分解、派系能力与耐心变化和逃亡准备，并提供主持人手动修正入口。
「自定义玩家行动」在本 GUI 的第三个页签中：把玩家模板切到 `custom`，再填写结果质量、修正池、目击次数、混乱与逃亡准备。

如果直接运行脚本，也可以使用：

```powershell
& $py src\the_unlisted\cli.py gui
```

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `check` | 校验人物引用、派系数与场景数 |
| `render` | 从 `data/` 重新生成 `docs/` |
| `act 3` | 查看第 3 幕总览 |
| `scene E3T` | 查看具体场景的完整资料 |
| `advance --scene E3T --quality 2` | 只推进到 E3T 并结算一次 |
| `run --profile normal --seed 5` | 用预设玩家画像跑完整剧本 |
| `verify` | 回归验证四种画像的结局边界 |
| `gui` | 打开本地图形化推演台 |

## 四种玩家画像

| 画像 | 含义 |
| --- | --- |
| `careful` | 不用超自然能力，尽量保秩序与正当性 |
| `normal` | 偶尔使用律能，两边都不得罪 |
| `sloppy` | 频繁使用律能，被人看见 |
| `reckless` | 在人群里动手、点火、制造混乱 |

## 运行样例

```text
档案        结果        预期
----------  ----------  ----------
careful     survive     survive     PASS
normal      survive     survive     PASS
sloppy      inquisition  inquisition  PASS
reckless    inquisition  inquisition  PASS
```

## 当前文件地图

```text
data/
  chronicle.json      世界状态、崩盘轨道、极乐境、附录
  kindred.json        5 个血族派系与人物
  mortal.json         3 个人类制度阵营与人物
  props.json          唯一关键道具：托管档案
  acts/act-01..06.json 每幕一个文件，文件内包含场景

src/the_unlisted/
  data.py             数据合并与索引
  engine.py           局势结算引擎
  render.py           Markdown 生成器
  cli.py              命令行
  gui.py              Tkinter 图形界面

docs/
  index.md            本文件
  system.md           当前规则、派系与幕结构
  roster.md           自动生成的名册、道具、附录与数值
  acts/act-01..06.md  自动生成的幕文件
  dashboard.html      自动生成的图形化总览
```

## 给主持人的最小流程

1. 先读 `system.md` 的“三分钟开局”。
2. 按 `acts/act-01.md` 到 `act-06.md` 推进。
3. 每个场景结束时只结算一次世界状态。
4. 不记得名词时查 `roster.md`。
5. 不确定引擎结果时运行 `verify`；不确定玩家后果时用 `advance --scene <ID>` 试算。

*运行方式与剧本内容均为虚构设定。*
