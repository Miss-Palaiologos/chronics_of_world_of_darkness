# Changelog / 版本记录

## [1.0.4] - 2026-09-20

### English

- Rewrote scene 5.1 completely: the whole scene now takes place at the Yong An cemetery and tomb. All building, corridor, stairwell, and archive-room remnants are gone.
- Fixed the arrival order at the tomb: the Silent Court first, then the technocratic government with military police and special tactics, while the Second Inquisition stays outside to fish for a big fish. Blood servants appear only after blood is spilled or someone dies; if the Methuselah wakes, the Inquisition enters and kills everyone.
- Replaced the water-utility hook with jurisdiction: the case file cannot be retrieved because the site of the incident falls inside the joint authority zone drawn by the trusteeship record.
- Localized remaining English skill and name leftovers: ` Leadership` became 领导力, and Kavita, Daniel, and Nadia are now 卡维塔、蔡丹尼、娜迪亚.
- Removed the split banners from act 3 (the movement has not split yet) and changed the Unionist slogan to 「公开附件，落实过渡」 in act 4.
- Added finale resolution: the engine now reads human faction strength and outputs who holds the agenda, who becomes the scapegoat, which sentence is written, and how the events are characterized. Wired into `the_unlisted.cli finale` and the GUI 终局判定 tab.
- Rebuilt the GUI layout: scene and variants split into panes, settlement split into four sub-tabs, and an escape-preparation progress bar in the header.

### 中文

- 完全重写 5.1：整幕都发生在永安义山与墓前，删去所有楼房、走廊、楼梯与档案室残留。
- 固定墓前到场顺序：缄默庭先到，随后是技术官僚派的宪特与特警；第二审判庭留在义山外围钓大鱼。血仆只在见血或有人死亡后出现；玛土撒拉一旦被唤醒，审判庭进场清场。
- 「水务条款」改为「管辖权条款」：案卷调不出来，是因为案发地在托管记录里被划入联合机构辖区。
- 统一残留英文：` Leadership` 改为领导力，Kavita／Daniel／Nadia 改为卡维塔／蔡丹尼／娜迪亚。
- 第三幕删去两派各自的横幅（运动尚未分裂）；第四幕联盟派口号改为「公开附件，落实过渡」。
- 新增终局判定：按人类各派力量对比输出谁在议程上、谁是替罪羊、那句话怎么写、事件如何被定性；接入 CLI `finale` 与界面「终局判定」页。
- 重排界面：当前局面分上下栏、变体左右分栏；本场结算拆成四个子页；顶部加入逃亡准备进度条。

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
- Replaced loose terms with V5 skills and backgrounds such as Politics, Academics (Law), Resources, Influence, Leadership (领导力), Subterfuge, Stealth, and Investigation.
- Updated generated act documents and the GUI variant table to show the new mechanics.

### 中文

- 为每个变体词条补充明确的世界含义、场景体现、玩家行为与难度影响。
- 将“官僚”“资源”等松散说法替换为 V5 技能与背景，例如政治、学术（法律）、资源、影响力、领导力、欺骗、潜行、调查。
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
