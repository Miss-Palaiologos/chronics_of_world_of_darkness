"""《不在册者》主持人图形化推演台。

推荐运行：`python -m the_unlisted.cli gui`
也支持：`python src/the_unlisted/gui.py`

布局约定：

- **当前局面**：上半是当前场景描写，下半是本幕／下一幕变体。左表右详情，避免长句挤在表格里。
- **本场结算**：世界状态、血族变化、终局判定、结算明细分成四个子页。
- **手动修正／自定义行动**：世界状态、派系状态、自定义玩家行动三块。
"""

from __future__ import annotations

import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "the_unlisted"

from .data import WORLD_VARS, ChronicleData, scene_label
from .engine import Chronicle, PlayerMods

PROFILE_ZH = {
    "careful": "谨慎：不用超自然能力，保秩序",
    "normal": "正常：偶尔用一次律能",
    "sloppy": "冒失：靠律能解决问题",
    "reckless": "整烂活：点火、暴露、制造混乱",
    "custom": "自定义：手动填写玩家行动",
}

PROFILE_MODE = {
    "careful": (3, 0, 0, 0),
    "normal": (2, 0, 0, 0),
    "sloppy": (1, 1, 1, 0),
    "reckless": (1, 2, 2, 0),
    "custom": (0, 0, 0, 0),
}

VAR_ZH = {
    "order": "秩序",
    "legitimacy": "正当性",
    "feeding": "猎食条件",
    "exposure": "暴露度",
    "capital": "资本信心",
}

STANCE_ZH = {
    "destroy": "守土",
    "public": "开门",
    "delay": "拖字",
    "abstain": "旁观",
    "chaos": "搅局",
}

ZH_TO_VAR = {
    "秩序": "order",
    "正当性": "legitimacy",
    "猎食条件": "feeding",
    "暴露度": "exposure",
    "资本信心": "capital",
}


def variant_triggered(when: str, world: dict[str, int]) -> bool:
    match = re.search(r"(秩序|正当性|猎食条件|暴露度|资本信心)\s*([≤≥])\s*(\d+)", when)
    if not match:
        return False
    var = ZH_TO_VAR[match.group(1)]
    op = match.group(2)
    threshold = int(match.group(3))
    return world[var] <= threshold if op == "≤" else world[var] >= threshold


class ChronicleGui:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("《不在册者》· 主持人局势台")
        self.root.geometry("1380x920")
        self.root.minsize(1120, 760)

        self.data = ChronicleData.load()
        self.ch = Chronicle(self.data)
        self.profile = tk.StringVar(value="normal")
        self.act_text = tk.StringVar()
        self.escape_text = tk.StringVar()
        self.status_text = tk.StringVar(value="")
        self.state_text = {v: tk.StringVar() for v in WORLD_VARS}

        self.manual_world = {v: tk.IntVar(value=0) for v in WORLD_VARS}
        self.escape_value = tk.IntVar(value=0)
        self.faction_id = tk.StringVar()
        self.faction_patience = tk.IntVar(value=0)
        self.faction_capability = tk.IntVar(value=0)
        self.faction_stance = tk.StringVar(value="不改变")
        self.archive_choice = tk.StringVar()
        self.archive_apply_effect = tk.BooleanVar(value=True)
        self.archive_text = tk.StringVar()
        self.custom_quality = tk.IntVar(value=2)
        self.custom_witnessed = tk.IntVar(value=0)
        self.custom_agitation = tk.IntVar(value=0)
        self.custom_escape_delta = tk.IntVar(value=0)
        self.custom_alloc = {v: tk.IntVar(value=0) for v in WORLD_VARS}

        self._build()
        self._refresh()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build(self) -> None:
        header = ttk.Frame(self.root, padding=(14, 12, 14, 6))
        header.pack(fill="x")
        ttk.Label(header, textvariable=self.act_text, font=("", 15, "bold")).pack(
            anchor="w"
        )

        progress_row = ttk.Frame(header)
        progress_row.pack(fill="x", pady=(6, 0))
        ttk.Label(
            progress_row, textvariable=self.escape_text, font=("", 11, "bold")
        ).pack(side="left")
        self.escape_bar = ttk.Progressbar(
            progress_row,
            orient="horizontal",
            length=220,
            maximum=self.data.escape_rules["range"][1] or 3,
            mode="determinate",
        )
        self.escape_bar.pack(side="left", padx=(10, 0))
        ttk.Label(
            progress_row, textvariable=self.archive_text, font=("", 11, "bold")
        ).pack(side="left", padx=(24, 0))

        state_frame = ttk.LabelFrame(self.root, text="当前世界状态", padding=8)
        state_frame.pack(fill="x", padx=14, pady=(0, 8))
        for col, var in enumerate(WORLD_VARS):
            ttk.Label(state_frame, text=VAR_ZH[var]).grid(
                row=0, column=col, padx=14, sticky="e"
            )
            ttk.Label(
                state_frame,
                textvariable=self.state_text[var],
                font=("", 15, "bold"),
            ).grid(row=1, column=col, padx=14, sticky="w")

        controls = ttk.Frame(self.root, padding=(14, 0))
        controls.pack(fill="x")
        ttk.Label(controls, text="玩家模板").pack(side="left")
        combo = ttk.Combobox(
            controls,
            state="readonly",
            width=38,
            values=[f"{k}｜{v}" for k, v in PROFILE_ZH.items()],
        )
        combo.set(f"normal｜{PROFILE_ZH['normal']}")
        combo.pack(side="left", padx=8)

        def select_profile(_event=None) -> None:
            self.profile.set(combo.get().split("｜", 1)[0])

        combo.bind("<<ComboboxSelected>>", select_profile)
        ttk.Button(controls, text="推进下一场", command=self._advance).pack(
            side="left", padx=8
        )
        ttk.Button(controls, text="重置", command=self._reset).pack(side="left")
        ttk.Label(controls, textvariable=self.status_text).pack(side="left", padx=16)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=14, pady=12)
        home_tab = ttk.Frame(notebook)
        result_tab = ttk.Frame(notebook)
        manual_tab = ttk.Frame(notebook)
        notebook.add(home_tab, text="当前局面")
        notebook.add(result_tab, text="本场结算")
        notebook.add(manual_tab, text="道具与手动修正")

        self._build_home_tab(home_tab)
        self._build_result_tab(result_tab)
        self._build_manual_tab(manual_tab)

    # ---- 当前局面 -------------------------------------------------------

    def _build_home_tab(self, tab: ttk.Frame) -> None:
        pane = ttk.PanedWindow(tab, orient="vertical")
        pane.pack(fill="both", expand=True, padx=6, pady=6)

        scene_box = ttk.LabelFrame(pane, text="当前场景描写", padding=6)
        pane.add(scene_box, weight=3)
        self.home_scene = ScrolledText(
            scene_box, wrap="word", height=12, font=("", 11)
        )
        self.home_scene.pack(fill="both", expand=True)

        variant_box = ttk.LabelFrame(pane, text="变体", padding=6)
        pane.add(variant_box, weight=4)

        self.variant_book = ttk.Notebook(variant_box)
        self.variant_book.pack(fill="both", expand=True)

        self.variant_trees: dict[str, ttk.Treeview] = {}
        self.variant_details: dict[str, ScrolledText] = {}
        self._variant_cache: dict[str, dict[str, dict]] = {"current": {}, "next": {}}
        for key, label in (("current", "本幕变体"), ("next", "下一幕变体条件")):
            page = ttk.Frame(self.variant_book)
            self.variant_book.add(page, text=label)
            split = ttk.PanedWindow(page, orient="horizontal")
            split.pack(fill="both", expand=True)

            tree = ttk.Treeview(
                split,
                columns=("scene", "when", "text"),
                show="headings",
                height=8,
            )
            for col, head, width in (
                ("scene", "场景", 70),
                ("when", "触发条件", 160),
                ("text", "场景体现", 520),
            ):
                tree.heading(col, text=head)
                tree.column(
                    col,
                    width=width,
                    anchor="center" if col in {"scene", "when"} else "w",
                )
            tree.tag_configure("triggered", foreground="#c62828")
            tree.pack(side="left", fill="both", expand=True)
            split.add(tree, weight=3)

            detail = ScrolledText(split, wrap="word", height=8, font=("", 10))
            split.add(detail, weight=2)
            detail.insert("end", "选中一条变体，这里会显示它的含义与玩家行为／难度。\n")
            tree.bind(
                "<<TreeviewSelect>>",
                lambda _e, k=key: self._show_variant_detail(k),
            )
            self.variant_trees[key] = tree
            self.variant_details[key] = detail

        ttk.Label(
            tab,
            text="红字 = 按当前世界状态会立即命中。世界状态每推进一步刷新一次。",
            foreground="#666666",
        ).pack(anchor="w", padx=10, pady=(0, 6))

    # ---- 本场结算 -------------------------------------------------------

    def _build_result_tab(self, tab: ttk.Frame) -> None:
        self.result_summary = tk.StringVar()
        ttk.Label(
            tab, textvariable=self.result_summary, font=("", 12, "bold")
        ).pack(anchor="w", padx=10, pady=(8, 4))

        book = ttk.Notebook(tab)
        book.pack(fill="both", expand=True, padx=6, pady=6)

        world_page = ttk.Frame(book)
        kindred_page = ttk.Frame(book)
        finale_page = ttk.Frame(book)
        detail_page = ttk.Frame(book)
        book.add(world_page, text="世界状态")
        book.add(kindred_page, text="血族变化")
        book.add(finale_page, text="终局判定")
        book.add(detail_page, text="结算明细")

        self.world_tree = ttk.Treeview(
            world_page,
            columns=("var", "before", "pulse", "action", "player", "after"),
            show="headings",
            height=8,
        )
        for key, label, width in (
            ("var", "变量", 130),
            ("before", "起始", 80),
            ("pulse", "固有", 80),
            ("action", "行动", 90),
            ("player", "玩家", 80),
            ("after", "终值", 80),
        ):
            self.world_tree.heading(key, text=label)
            self.world_tree.column(key, width=width, anchor="center")
        self.world_tree.pack(fill="x", padx=10, pady=10)
        ttk.Label(
            world_page,
            text="固有 = 事件本身的历史惯性；行动 = 血族与人类各派系效果之和；玩家 = 修正池。",
            foreground="#666666",
        ).pack(anchor="w", padx=10)

        self.kindred_tree = ttk.Treeview(
            kindred_page,
            columns=("faction", "stance", "patience", "capability", "change"),
            show="headings",
            height=8,
        )
        for key, label, width in (
            ("faction", "派系", 150),
            ("stance", "立场", 130),
            ("patience", "耐心", 100),
            ("capability", "能力", 100),
            ("change", "变化", 220),
        ):
            self.kindred_tree.heading(key, text=label)
            self.kindred_tree.column(key, width=width, anchor="center")
        self.kindred_tree.pack(fill="x", padx=10, pady=10)

        self.finale_text = ScrolledText(finale_page, wrap="word", font=("", 11))
        self.finale_text.pack(fill="both", expand=True, padx=10, pady=10)

        self.result_details = ScrolledText(detail_page, wrap="word", font=("", 10))
        self.result_details.pack(fill="both", expand=True, padx=10, pady=10)

    # ---- 手动修正 -------------------------------------------------------

    def _build_manual_tab(self, tab: ttk.Frame) -> None:
        pad = {"padx": 10, "pady": 8}

        archive_box = ttk.LabelFrame(
            tab, text="关键道具 · 托管档案去向（玩家唯一能直接摸到的东西）", padding=10
        )
        archive_box.pack(fill="x", **pad)
        self.archive_combo = ttk.Combobox(
            archive_box,
            state="readonly",
            width=34,
            values=[
                f"{o['id']}｜{o['action']}" for o in self.data.archive_options
            ],
            textvariable=self.archive_choice,
        )
        self.archive_combo.grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.archive_combo.bind("<<ComboboxSelected>>", lambda _e: self._archive_preview())
        ttk.Checkbutton(
            archive_box,
            text="同时计入该去向的世界影响",
            variable=self.archive_apply_effect,
        ).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(archive_box, text="应用去向", command=self._apply_archive).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(
            archive_box, text="恢复默认世界线", command=self._reset_archive
        ).grid(row=0, column=3)
        self.archive_default_label = tk.StringVar()
        ttk.Label(archive_box, textvariable=self.archive_default_label).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )
        self.archive_preview = ScrolledText(
            archive_box, wrap="word", height=4, font=("", 10)
        )
        self.archive_preview.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        archive_box.columnconfigure(0, weight=1)

        world_box = ttk.LabelFrame(tab, text="世界状态修正", padding=10)
        world_box.pack(fill="x", **pad)
        for col, var in enumerate(WORLD_VARS):
            ttk.Label(world_box, text=VAR_ZH[var]).grid(row=0, column=col)
            ttk.Spinbox(
                world_box,
                from_=-3,
                to=3,
                textvariable=self.manual_world[var],
                width=5,
            ).grid(row=1, column=col, padx=8)
        ttk.Label(world_box, text="逃亡准备").grid(row=0, column=5)
        ttk.Spinbox(
            world_box,
            from_=0,
            to=self.data.escape_rules["range"][1],
            textvariable=self.escape_value,
            width=5,
        ).grid(row=1, column=5, padx=8)
        ttk.Button(world_box, text="应用", command=self._apply_world).grid(
            row=1, column=6, padx=12
        )
        ttk.Label(
            world_box,
            text="世界状态输入的是增量；应用后会清零。逃亡准备输入的是当前绝对值。",
        ).grid(row=2, column=0, columnspan=7, sticky="w", pady=(8, 0))

        mortal_box = ttk.LabelFrame(
            tab, text="人类阵营合法能力修正（密室交易 · 决定谁在议程上）", padding=10
        )
        mortal_box.pack(fill="x", **pad)
        mortal_labels = [
            f"{f['id']}｜{f['zh']}" for f in self.data.mortal["factions"]
        ]
        self.mortal_combo = ttk.Combobox(
            mortal_box, state="readonly", values=mortal_labels, width=22
        )
        self.mortal_combo.set(mortal_labels[0])
        self.mortal_combo.grid(row=0, column=0, padx=(0, 8))
        ttk.Label(mortal_box, text="合法能力 ±1").grid(row=0, column=1, padx=4)
        self.mortal_delta = tk.IntVar(value=0)
        ttk.Spinbox(
            mortal_box, from_=-1, to=1, textvariable=self.mortal_delta, width=4
        ).grid(row=0, column=2)
        ttk.Button(mortal_box, text="应用", command=self._apply_mortal_capability).grid(
            row=0, column=3, padx=12
        )
        self.mortal_note = tk.StringVar()
        ttk.Label(
            mortal_box, textvariable=self.mortal_note, foreground="#666666"
        ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))

        faction_box = ttk.LabelFrame(tab, text="派系状态修正", padding=10)
        faction_box.pack(fill="x", **pad)
        factions = list(self.data.kindred_factions.values())
        faction_labels = [f"{f['id']}｜{f['zh']}" for f in factions]
        faction_combo = ttk.Combobox(
            faction_box, state="readonly", values=faction_labels, width=22
        )
        faction_combo.set(faction_labels[0])
        faction_combo.grid(row=0, column=0, padx=8)

        def select_faction(_event=None) -> None:
            self.faction_id.set(faction_combo.get().split("｜", 1)[0])

        faction_combo.bind("<<ComboboxSelected>>", select_faction)
        self.faction_id.set(factions[0]["id"])
        ttk.Label(faction_box, text="耐心").grid(row=0, column=1, padx=4)
        ttk.Spinbox(
            faction_box, from_=-1, to=1, textvariable=self.faction_patience, width=4
        ).grid(row=0, column=2)
        ttk.Label(faction_box, text="能力").grid(row=0, column=3, padx=4)
        ttk.Spinbox(
            faction_box, from_=-1, to=1, textvariable=self.faction_capability, width=4
        ).grid(row=0, column=4)
        ttk.Label(faction_box, text="立场").grid(row=0, column=5, padx=4)
        ttk.Combobox(
            faction_box,
            state="readonly",
            width=8,
            values=["不改变", *STANCE_ZH.values()],
            textvariable=self.faction_stance,
        ).grid(row=0, column=6)
        ttk.Button(faction_box, text="应用", command=self._apply_faction).grid(
            row=0, column=7, padx=12
        )

        custom_box = ttk.LabelFrame(
            tab, text="自定义玩家行动（把玩家模板切到 custom 后生效）", padding=10
        )
        custom_box.pack(fill="x", **pad)
        for col, (label, var) in enumerate(
            (
                ("结果质量", self.custom_quality),
                ("目击超自然", self.custom_witnessed),
                ("制造混乱", self.custom_agitation),
                ("逃亡准备增量", self.custom_escape_delta),
            )
        ):
            ttk.Label(custom_box, text=label).grid(row=0, column=col)
            ttk.Spinbox(
                custom_box, from_=0, to=3, textvariable=var, width=5
            ).grid(row=1, column=col, padx=8)
        ttk.Label(custom_box, text="世界状态修正池（手动分配）").grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(10, 0)
        )
        for col, var in enumerate(WORLD_VARS):
            ttk.Label(custom_box, text=VAR_ZH[var]).grid(row=3, column=col)
            ttk.Spinbox(
                custom_box,
                from_=-3,
                to=3,
                textvariable=self.custom_alloc[var],
                width=5,
            ).grid(row=4, column=col, padx=8)
        ttk.Label(
            custom_box,
            text=(
                "结果质量 0–3；修正池 = 结果质量 × 2。"
                "目击超自然会额外增加暴露度，制造混乱会降低秩序并提高暴露度。"
            ),
            wraplength=1000,
        ).grid(row=5, column=0, columnspan=8, sticky="w", pady=(10, 0))

    # ------------------------------------------------------------------
    # 状态与推进
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        if self.ch.act_cursor >= len(self.data.acts()):
            self.act_text.set("编年史结束")
        else:
            scene = self.ch.current_act()
            group = self.data.group(scene["act"])
            self.act_text.set(
                f"第 {group['act']} 幕 · {group['title']}　"
                f"当前场景：{scene_label(scene)} · {scene['title']}"
            )
        for var in WORLD_VARS:
            self.state_text[var].set(str(self.ch.world[var]))
        self.escape_value.set(self.ch.escape_prep)
        self.escape_bar["value"] = self.ch.escape_prep
        threshold = self.data.escape_rules["threshold_survive"]
        mark = "达标" if self.ch.escape_prep >= threshold else "未达标"
        self.escape_text.set(
            f"逃亡准备：{self.ch.escape_prep}/3（存活门槛 {threshold}，{mark}）"
        )
        arc = self.ch.archive_report()
        flag = "手动指定" if arc["manual"] else f"默认世界线：{arc['default_zh']}"
        self.archive_text.set(f"托管档案：{arc['zh']}（{flag}）")
        self._sync_archive_widgets()
        self._sync_mortal_widgets()
        self._render_home()

    # ---- 关键道具：托管档案 ----------------------------------------------

    def _sync_archive_widgets(self) -> None:
        arc = self.ch.archive_report()
        current = next(
            (o for o in self.data.archive_options if o["id"] == arc["id"]), None
        )
        if current:
            self.archive_choice.set(f"{current['id']}｜{current['action']}")
        self.archive_default_label.set(
            f"默认世界线（第 {self.data.group(self.ch.current_act()['act'])['act']} 幕）："
            f"{arc['default_zh']}　—— 只要不手动改动，引擎就按它走，且不额外计入数值；"
            "手动改动才把该去向的世界影响算进来。"
        )
        self._archive_preview()

    def _selected_archive_option(self) -> dict:
        raw = self.archive_choice.get()
        aid = raw.split("｜", 1)[0] if raw else ""
        return next(
            (o for o in self.data.archive_options if o["id"] == aid), {}
        )

    def _archive_preview(self) -> None:
        opt = self._selected_archive_option()
        self.archive_preview.delete("1.0", "end")
        if not opt:
            return
        delta = opt.get("delta", {})
        cells = "　".join(
            f"{VAR_ZH.get(k, k)} {v:+d}" for k, v in delta.items()
        ) or "无世界状态变化"
        lines = [
            f"{opt['id']}｜{opt['action']}",
            f"世界影响：{cells}",
        ]
        kd = opt.get("kindred_delta", {})
        if kd:
            lines.append(
                "血族影响："
                + "　".join(
                    f"{self.data.kindred_factions[f]['zh']} 能力 {v:+d}"
                    for f, v in kd.items()
                )
            )
        if opt.get("note"):
            lines.append(opt["note"])
        self.archive_preview.insert("end", "\n".join(lines) + "\n")

    def _apply_archive(self) -> None:
        opt = self._selected_archive_option()
        if not opt:
            self._status("先选一个档案去向。")
            return
        report = self.ch.set_archive_location(
            opt["id"], apply_delta=self.archive_apply_effect.get()
        )
        applied = "已计入世界影响" if report["applied"] else "未计入影响（只记录去向）"
        self._refresh()
        self._render_finale()
        self._status(f"托管档案 → {report['zh']}（{applied}）")

    def _reset_archive(self) -> None:
        report = self.ch.reset_archive_to_default()
        self._refresh()
        self._render_finale()
        self._status(f"托管档案回到默认世界线：{report['zh']}")

    def _mods(self) -> PlayerMods:
        if self.profile.get() == "custom":
            return PlayerMods(
                outcome_quality=self.custom_quality.get(),
                allocations={
                    v: self.custom_alloc[v].get() for v in WORLD_VARS
                },
                witnessed_supernatural=self.custom_witnessed.get(),
                agitation=self.custom_agitation.get(),
                escape_delta=self.custom_escape_delta.get(),
            )
        quality, agitation, witnessed, escape = PROFILE_MODE[self.profile.get()]
        prefer = {
            "careful": ("order", "legitimacy", "capital"),
            "normal": ("order", "legitimacy", "capital", "feeding"),
            "sloppy": ("order", "legitimacy"),
            "reckless": ("order",),
        }[self.profile.get()]
        pool = quality * 2
        alloc: dict[str, int] = {}
        for i in range(pool):
            var = prefer[i % len(prefer)]
            alloc[var] = alloc.get(var, 0) + 1
        return PlayerMods(
            outcome_quality=quality,
            allocations=alloc,
            witnessed_supernatural=witnessed,
            agitation=agitation,
            escape_delta=escape,
        )

    def _advance(self) -> None:
        if self.ch.act_cursor >= len(self.data.acts()):
            self._status("编年史已经结束。")
            return
        res = self.ch.advance(self._mods())
        self.ch.act_cursor += 1
        self._render_result(res)
        self._refresh()

    # ---- 结算渲染 -------------------------------------------------------

    def _render_result(self, res) -> None:
        self.result_summary.set(
            f"{res.act_id} · {res.title}　烈度 {res.intensity}（{res.intensity_band}）"
        )
        self._clear(self.world_tree)
        for var in WORLD_VARS:
            self.world_tree.insert(
                "",
                "end",
                values=(
                    VAR_ZH[var],
                    res.world_before[var],
                    res.inherent_pulse.get(var, 0),
                    f"{res.action_delta[var]:.1f}",
                    res.player_delta[var],
                    res.world_after[var],
                ),
            )
        self._clear(self.kindred_tree)
        for _fid, before in res.kindred_before.items():
            after = res.kindred_after[_fid]
            changed = []
            if before["stance"] != after["stance"]:
                changed.append(
                    f"立场 {STANCE_ZH.get(before['stance'], before['stance'])}→"
                    f"{STANCE_ZH.get(after['stance'], after['stance'])}"
                )
            if before["patience"] != after["patience"]:
                changed.append(f"耐心 {before['patience']}→{after['patience']}")
            if before["capability"] != after["capability"]:
                changed.append(f"能力 {before['capability']}→{after['capability']}")
            self.kindred_tree.insert(
                "",
                "end",
                values=(
                    before["zh"],
                    f"{STANCE_ZH.get(before['stance'], before['stance'])}→"
                    f"{STANCE_ZH.get(after['stance'], after['stance'])}",
                    f"{before['patience']}→{after['patience']}",
                    f"{before['capability']}→{after['capability']}",
                    "、".join(changed) or "不变",
                ),
            )
        self._render_finale()

        self.result_details.delete("1.0", "end")
        details = [f"逃亡准备：{self.ch.escape_prep}/3", "", "变化原因："]
        details.extend(f"· {c}" for c in res.kindred_changes or ["无"])
        if res.clamps_applied:
            details.extend(["", "上限保护："])
            details.extend(f"· {c}" for c in res.clamps_applied)
        if res.collapse:
            details.extend(
                [
                    "",
                    f"崩盘：{res.collapse['zh']}",
                    f"结果：{res.collapse['outcome']}",
                    f"逃亡结算：{self.ch.escape_outcome()}",
                ]
            )
        self.result_details.insert("end", "\n".join(details) + "\n")

    def _render_finale(self) -> None:
        r = self.ch.finale_resolution()
        sc = r["scapegoat"]
        inst = r["institutional"]
        lines = ["【人类各派力量对比】", f"{'阵营':<8}{'立场':<10}{'合法能力':<10}效果"]
        for row in r["agenda"]["table"]:
            mark = "　← 在议程上" if row["zh"] == r["agenda"]["zh"] else ""
            lines.append(
                f"{row['zh']:<8}{row['stance']:<10}{row['legal']:<12}{row['effect']}{mark}"
            )
        lines += [
            "",
            f"在议程上的阵营：{r['agenda']['zh']}",
            f"制度侧提名（{inst['nominated_by']}）：{inst['who']}｜{inst['means']}",
            f"　那句话：「{inst['line']}」",
        ]
        if r["street_override"]:
            lines += [
                f"※ 街头否决生效：旧自由邦能力 {r['street_capability']} ≥ "
                f"制度侧赢家合法能力 {r['agenda']['legal']}。",
                f"最终写进《事件说明》第一条的人：{sc['who']}｜{sc['means']}",
                f"　那句话：「{sc['line']}」",
            ]
        else:
            lines.append(
                f"最终写进《事件说明》第一条的人：{sc['who']}｜{sc['means']}"
            )
        lines += [
            "",
            f"事件如何被定性：{r['characterization']['zh']}",
            f"  {r['characterization']['text']}",
            "",
            f"附则十九由谁处理：{r['annex']['who']}（{r['annex']['how']}）",
            f"联合开发区条款：{r['zone']['result']}",
            f"托管档案去向：{r['archive']['zh']}"
            + (
                f"（手动指定；默认世界线：{r['archive']['default_zh']}）"
                if r["archive"]["manual"]
                else "（默认世界线）"
            ),
            f"逃亡准备：{r['escape']['value']}/3 → {r['escape']['text']}",
        ]
        if r["agenda"]["tie"]:
            lines.insert(
                1,
                "※ 主权派与联盟派效果相同——按平局判定："
                "条约先被写下来，所以联盟派优先。",
            )
        if r["collapse"]:
            lines += [
                "",
                f"⚠ 崩盘轨道：{r['collapse']['zh']}——{r['collapse']['outcome']}",
            ]
        self.finale_text.delete("1.0", "end")
        self.finale_text.insert("end", "\n".join(lines) + "\n")

    # ---- 当前局面渲染 ---------------------------------------------------

    def _render_home(self) -> None:
        self.home_scene.delete("1.0", "end")
        for key in ("current", "next"):
            self._clear(self.variant_trees[key])
            self.variant_details[key].delete("1.0", "end")
            self._variant_cache[key].clear()

        if self.ch.act_cursor >= len(self.data.acts()):
            self.home_scene.insert(
                "end", "所有场景已经完成。请在「本场结算 → 终局判定」查看结果。\n"
            )
            return

        scene = self.data.acts()[self.ch.act_cursor]
        group = self.data.group(scene["act"])
        self.home_scene.insert(
            "end", f"【{scene_label(scene)} · {scene['title']}】\n\n"
        )
        for para in scene.get("scene", []):
            self.home_scene.insert("end", para + "\n\n")
        if scene.get("hook"):
            self.home_scene.insert("end", f"钩子：{scene['hook']}\n")

        self._fill_variants("current", group["scenes"], "本幕没有变体条件。")
        next_group = self.data.groups_by_no.get(group["act"] + 1)
        if next_group:
            self._fill_variants("next", next_group["scenes"], "下一幕没有变体条件。")
            self.variant_book.tab(
                1, text=f"下一幕变体条件（第 {next_group['act']} 幕）"
            )
        else:
            self.variant_details["next"].insert("end", "已经是最后一幕。\n")
            self.variant_book.tab(1, text="下一幕变体条件")

    def _fill_variants(self, key: str, scenes: list[dict], empty: str) -> None:
        tree = self.variant_trees[key]
        rows = 0
        for scene in scenes:
            for v in scene.get("variants", []):
                triggered = variant_triggered(v["when"], self.ch.world)
                iid = tree.insert(
                    "",
                    "end",
                    values=(
                        scene_label(scene),
                        v["when"],
                        v.get("scene_effect", v.get("text", "")),
                    ),
                    tags=("triggered",) if triggered else (),
                )
                self._variant_cache[key][iid] = v
                rows += 1
        if not rows:
            self.variant_details[key].insert("end", empty + "\n")

    def _show_variant_detail(self, key: str) -> None:
        tree = self.variant_trees[key]
        selection = tree.selection()
        box = self.variant_details[key]
        box.delete("1.0", "end")
        if not selection:
            return
        v = self._variant_cache[key].get(selection[0])
        if not v:
            return
        values = tree.item(selection[0], "values")
        lines = [f"【{values[0]} · {v['when']}】", ""]
        if v.get("meaning"):
            lines.append(f"含义：{v['meaning']}")
        if v.get("scene_effect"):
            lines.append(f"场景体现：{v['scene_effect']}")
        if v.get("text"):
            lines.append(f"原文：{v['text']}")
        effects = v.get("player_effects") or []
        if effects:
            lines += ["", "玩家行为与难度："]
            for e in effects:
                lines.append(f"· {e['behavior']}：{e['modifier']}")
                if e.get("why"):
                    lines.append(f"　　{e['why']}")
        box.insert("end", "\n".join(lines) + "\n")

    # ------------------------------------------------------------------
    # 修正
    # ------------------------------------------------------------------

    def _apply_world(self) -> None:
        deltas = {v: self.manual_world[v].get() for v in WORLD_VARS}
        self.ch.apply_manual_adjustment(deltas, self.escape_value.get())
        for var in WORLD_VARS:
            self.manual_world[var].set(0)
        self._refresh()
        self._render_finale()
        self._status("世界状态与逃亡准备已修正。")

    def _apply_faction(self) -> None:
        label = self.faction_stance.get()
        stance = None
        if label != "不改变":
            stance = next((k for k, v in STANCE_ZH.items() if v == label), None)
        self.ch.adjust_faction(
            self.faction_id.get(),
            self.faction_patience.get(),
            self.faction_capability.get(),
            stance,
        )
        self.faction_patience.set(0)
        self.faction_capability.set(0)
        self.faction_stance.set("不改变")
        self._refresh()
        self._render_finale()
        self._status("派系状态已修正。")

    def _apply_mortal_capability(self) -> None:
        label = self.mortal_combo.get()
        fid = label.split("｜", 1)[0] if label else ""
        if not fid:
            self._status("先选一个人类阵营。")
            return
        report = self.ch.change_mortal_capability(fid, self.mortal_delta.get())
        self.mortal_delta.set(0)
        self._refresh()
        self._render_finale()
        self._status(
            f"{report['阵营']} 合法能力 → {report['合法能力']}"
            f"（累计 {report['累计修正']:+d}）"
        )

    def _sync_mortal_widgets(self) -> None:
        parts = []
        for st in self.ch.mortal.values():
            delta = self.ch.mortal_capability_delta.get(st.faction_id, 0)
            parts.append(
                f"{st.zh} {st.capability['legal']}（{delta:+d}）"
                if delta
                else f"{st.zh} {st.capability['legal']}"
            )
        self.mortal_note.set(
            "　".join(parts)
            + "　—— 效果 = 能力 × 立场烈度 × 世界状态杠杆；每 ±1 就可能换一次议程。"
        )

    # ------------------------------------------------------------------

    def _reset(self) -> None:
        self.ch = Chronicle(self.data)
        self._clear(self.world_tree)
        self._clear(self.kindred_tree)
        for key in ("current", "next"):
            self._clear(self.variant_trees[key])
            self.variant_details[key].delete("1.0", "end")
            self._variant_cache[key].clear()
        self.home_scene.delete("1.0", "end")
        self.finale_text.delete("1.0", "end")
        self.result_details.delete("1.0", "end")
        self.result_summary.set("")
        self.status_text.set("已重置。")
        self._refresh()

    @staticmethod
    def _clear(tree: ttk.Treeview) -> None:
        for item in tree.get_children():
            tree.delete(item)

    def _status(self, text: str) -> None:
        self.status_text.set(text)
        self.root.after(2500, lambda: self.status_text.set(""))


def main() -> None:
    root = tk.Tk()
    ChronicleGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
