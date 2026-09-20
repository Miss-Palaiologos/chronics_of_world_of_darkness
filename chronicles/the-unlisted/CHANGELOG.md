# Changelog / 版本记录

## [1.0.3] - 2026-09-20

### English

- Localized all V5 skill and background references in variant effects into Chinese.
- Corrected variant logic so each variable maps to an appropriate scene consequence.
- Changed the 5.1 high-exposure variant to represent Second Inquisition observation.
- Changed the 5.1 low-capital variant to represent collapsing resources, transport, bribes, and escape routes.
- Adjusted the 2.1 crowd-growth trigger from Order to Legitimacy.

### 中文

- 将变体中的 V5 技能与背景统一改为中文。
- 重新校正变体逻辑，让每个变量都对应合理的场景后果。
- 第五幕高暴露度变体改为第二审判庭已经到场观察。
- 第五幕低资本信心变体改为资源、车辆、贿赂与退路枯竭，不再暴露墓中文件。
- 第二幕守夜人数增加改由正当性下降触发。

## [1.0.2] - 2026-09-20

### English

- Added explicit meaning, scene expression, player behavior, and difficulty effects to every variant entry.
- Replaced loose terms with V5 skills and backgrounds such as Politics, Academics (Law), Resources, Influence, Leadership, Subterfuge, Stealth, and Investigation.
- Updated generated act documents and the GUI variant table to show the new mechanics.

### 中文

- 为每个变体词条补充明确的世界含义、场景体现、玩家行为与难度影响。
- 将“官僚”“资源”等松散说法替换为 V5 技能与背景，例如 Politics、Academics（Law）、Resources、Influence、Leadership、Subterfuge、Stealth、Investigation。
- 生成幕文档与 GUI 变体表同步展示新机制。

## [1.0.1] - 2026-09-20

### English

- Changed scene program IDs to readable hierarchical numbers such as `2.1`, `3.1`, and `6.2`.
- Updated CLI, GUI, data anchors, props, and generated documents to use the new numbering.
- Reduced the GUI home page to the current scene and next-act variant conditions.

### 中文

- 场景程序 ID 改为可读的二级编号，例如 `2.1`、`3.1`、`6.2`。
- CLI、GUI、数据锚点、道具流转和生成文档同步使用新编号。
- GUI 当前局面页只保留当前场景与下一幕变体条件，减少信息量。

## [1.0.0] - 2026-09-20

### English

- Initial public release of the bilingual chronicle repository.
- Added **The Unlisted / 《不在册者》** as the main chronicle.
- Added the six-act, eight-scene structure.
- Added the data engine, CLI, Markdown renderer, Tkinter GUI, and static dashboard.
- Added the `verify` regression command.
- Consolidated shared setting and scenario-writing notes under `docs/`.
- Added `PROJECT_PATHS.md` as the path registry.

### 中文

- 双语编年史仓库首次公开版本。
- 主作品确定为 **《不在册者》**。
- 建立六幕、八个场景的结构。
- 加入数据引擎、命令行、Markdown 生成器、Tkinter GUI 与静态看板。
- 加入 `verify` 回归验证命令。
- `docs/` 下保留世界观总结与编剧技法总结。
- 加入 `PROJECT_PATHS.md` 作为路径索引。
