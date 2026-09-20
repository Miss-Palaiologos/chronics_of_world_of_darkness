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
& $py -m the_unlisted.cli finale
& $py -m the_unlisted.cli balance --profile normal
```

需要图形界面时：

```powershell
& $py -m the_unlisted.cli gui
```

图形界面分三个页签：「当前局面」显示当前场景描写、本幕变体与下一幕变体条件（红字为当前立即命中，点选条目可看玩家行为与难度）；「本场结算」分世界状态、血族变化、终局判定、结算明细四页；顶部常驻逃亡准备进度条与**托管档案当前去向**。
「道具与手动修正」页有三块：**托管档案去向下拉框**（默认世界线，可手动改并计入影响）、**人类阵营合法能力修正**（密室交易的唯一直接杠杆，决定谁在议程上）、血族派系状态修正；「自定义玩家行动」同样在这一页：把玩家模板切到 `custom`，再填写结果质量、修正池、目击次数、混乱与逃亡准备。

如果直接运行脚本，也可以使用：

```powershell
& $py src\the_unlisted\cli.py gui
```

图形界面需要当前 Python 带有可用的 Tcl/Tk。若启动时报「缺少可用的 Tcl/Tk」，改用 conda 或官方安装版的 Python 运行同一条命令即可；剧本与结算引擎本身不依赖图形界面。

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `check` | 校验人物引用、派系数与场景数 |
| `render` | 从 `data/` 重新生成 `docs/` |
| `act 3` | 查看第 3 幕总览 |
| `scene 3.1` | 查看具体场景的完整资料 |
| `advance --scene 3.1 --quality 2` | 只推进到 3.1 并结算一次 |
| `run --profile normal --seed 5` | 用预设玩家画像跑完整剧本 |
| `finale` | 输出终局判定：谁在议程上、谁是替罪羊、那句话与事件定性 |
| `finale --scene 4.1` | 只推进到 4.1 就做终局判定 |
| `balance --profile normal` | 调试用：逐幕打印人类议程表与前两名差距 |
| `advance --scene 5.1 --archive destroyed` | 结算前指定托管档案去向 |
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
6. 每一幕结束后可在「本场结算 → 终局判定」看到：按当前人类各派力量对比，谁会成为替罪羊、那句话怎么写、事件会被定性成什么。

*运行方式与剧本内容均为虚构设定。*
