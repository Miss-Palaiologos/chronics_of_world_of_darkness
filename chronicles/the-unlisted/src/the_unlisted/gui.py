"""《不在册者》主持人图形化推演台。

推荐运行：`python -m the_unlisted.cli gui`
也支持：`python src/the_unlisted/gui.py`
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

from .data import WORLD_VARS, ChronicleData
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
        self.root.geometry("1240x900")
        self.root.minsize(1040, 720)

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
        header = ttk.Frame(self.root, padding=12)
        header.pack(fill="x")
        ttk.Label(header, textvariable=self.act_text, font=("", 15, "bold")).pack(
            anchor="w"
        )
        ttk.Label(header, textvariable=self.escape_text, font=("", 11, "bold")).pack(
            anchor="w", pady=(4, 0)
        )

        state_frame = ttk.LabelFrame(self.root, text="当前世界状态", padding=10)
        state_frame.pack(fill="x", padx=12, pady=(0, 8))
        for col, var in enumerate(WORLD_VARS):
            ttk.Label(state_frame, text=VAR_ZH[var]).grid(
                row=0, column=col, padx=12, sticky="e"
            )
            ttk.Label(
                state_frame,
                textvariable=self.state_text[var],
                font=("", 15, "bold"),
            ).grid(row=1, column=col, padx=12, sticky="w")

        controls = ttk.Frame(self.root, padding=(12, 0))
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
        ttk.Label(controls, textvariable=self.status_text).pack(
            side="left", padx=16
        )

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)
        home_tab = ttk.Frame(notebook)
        result_tab = ttk.Frame(notebook)
        manual_tab = ttk.Frame(notebook)
        notebook.add(home_tab, text="当前局面")
        notebook.add(result_tab, text="本场结算")
        notebook.add(manual_tab, text="手动修正／自定义行动")

        self._build_home_tab(home_tab)
        self._build_result_tab(result_tab)
        self._build_manual_tab(manual_tab)

    def _build_home_tab(self, tab: ttk.Frame) -> None:
        self.home_title = tk.StringVar()
        ttk.Label(tab, textvariable=self.home_title, font=("", 12, "bold")).pack(
            anchor="w", padx=8, pady=(8, 4)
        )

        ttk.Label(tab, text="当前场景描写").pack(anchor="w", padx=8, pady=(4, 2))
        self.home_scene = ScrolledText(tab, wrap="word", height=9, font=("", 11))
        self.home_scene.pack(fill="both", expand=True, padx=8, pady=2)

        ttk.Label(tab, text="当前幕变体（红字 = 当前状态命中）").pack(
            anchor="w", padx=8, pady=(8, 2)
        )
        self.current_variant_tree = ttk.Treeview(
            tab,
            columns=("scene", "when", "text"),
            show="headings",
            height=5,
        )
        for key, label, width in (
            ("scene", "场景", 90),
            ("when", "条件", 180),
            ("text", "变体语句", 760),
        ):
            self.current_variant_tree.heading(key, text=label)
            self.current_variant_tree.column(key, width=width, anchor="center" if key != "text" else "w")
        self.current_variant_tree.tag_configure("triggered", foreground="#c62828")
        self.current_variant_tree.pack(fill="x", padx=8, pady=2)

        ttk.Label(tab, text="下一幕变体条件（红字 = 按当前状态会立即命中）").pack(
            anchor="w", padx=8, pady=(8, 2)
        )
        self.next_variant_tree = ttk.Treeview(
            tab,
            columns=("scene", "when", "text"),
            show="headings",
            height=6,
        )
        for key, label, width in (
            ("scene", "场景", 90),
            ("when", "条件", 180),
            ("text", "变体语句", 760),
        ):
            self.next_variant_tree.heading(key, text=label)
            self.next_variant_tree.column(key, width=width, anchor="center" if key != "text" else "w")
        self.next_variant_tree.tag_configure("triggered", foreground="#c62828")
        self.next_variant_tree.pack(fill="x", padx=8, pady=2)

    def _build_result_tab(self, tab: ttk.Frame) -> None:
        self.result_summary = tk.StringVar()
        ttk.Label(
            tab, textvariable=self.result_summary, font=("", 11, "bold")
        ).pack(anchor="w", padx=8, pady=6)

        self.world_tree = ttk.Treeview(
            tab,
            columns=("var", "before", "pulse", "action", "player", "after"),
            show="headings",
            height=6,
        )
        for key, label, width in (
            ("var", "变量", 110),
            ("before", "起始", 70),
            ("pulse", "固有", 70),
            ("action", "行动", 80),
            ("player", "玩家", 70),
            ("after", "终值", 70),
        ):
            self.world_tree.heading(key, text=label)
            self.world_tree.column(key, width=width, anchor="center")
        self.world_tree.pack(fill="x", padx=8, pady=4)

        self.kindred_tree = ttk.Treeview(
            tab,
            columns=("faction", "stance", "patience", "capability", "change"),
            show="headings",
            height=6,
        )
        for key, label, width in (
            ("faction", "派系", 130),
            ("stance", "立场", 100),
            ("patience", "耐心", 90),
            ("capability", "能力", 90),
            ("change", "变化", 170),
        ):
            self.kindred_tree.heading(key, text=label)
            self.kindred_tree.column(key, width=width, anchor="center")
        self.kindred_tree.pack(fill="x", padx=8, pady=4)

        self.result_details = ScrolledText(tab, wrap="word", height=10)
        self.result_details.pack(fill="both", expand=True, padx=8, pady=6)

    def _build_manual_tab(self, tab: ttk.Frame) -> None:
        pad = {"padx": 10, "pady": 8}

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
            wraplength=980,
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
                f"当前场景：{scene['id']} · {scene['title']}"
            )
        for var in WORLD_VARS:
            self.state_text[var].set(str(self.ch.world[var]))
        self.escape_value.set(self.ch.escape_prep)
        self.escape_text.set(
            f"逃亡准备：{self.ch.escape_prep}/3　"
            f"（存活门槛：{self.data.escape_rules['threshold_survive']}）"
        )
        self._render_home()

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
        for fid, before in res.kindred_before.items():
            after = res.kindred_after[fid]
            changed = []
            if before["stance"] != after["stance"]:
                changed.append("立场")
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
        self.result_details.delete("1.0", "end")
        details = [
            f"逃亡准备：{self.ch.escape_prep}/3",
            "",
            "变化原因：",
        ]
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

    def _render_home(self) -> None:
        self._clear(self.current_variant_tree)
        self._clear(self.next_variant_tree)
        self.home_scene.delete("1.0", "end")

        if self.ch.act_cursor >= len(self.data.acts()):
            self.home_title.set("编年史结束")
            self.home_scene.insert("end", "所有场景已经完成。\n")
            return

        scene = self.data.acts()[self.ch.act_cursor]
        group = self.data.group(scene["act"])
        self.home_title.set(
            f"第 {group['act']} 幕 · {group['title']}　"
            f"当前场景：{scene['id']} · {scene['title']}"
        )
        self.home_scene.insert("end", f"【{scene['id']} · {scene['title']}】\n\n")
        for para in scene.get("scene", []):
            self.home_scene.insert("end", para + "\n\n")

        for s in group["scenes"]:
            for v in s.get("variants", []):
                triggered = variant_triggered(v["when"], self.ch.world)
                self.current_variant_tree.insert(
                    "",
                    "end",
                    values=(s["id"], v["when"], v["text"]),
                    tags=("triggered",) if triggered else (),
                )

        next_group = self.data.groups_by_no.get(group["act"] + 1)
        if next_group:
            for s in next_group["scenes"]:
                for v in s.get("variants", []):
                    triggered = variant_triggered(v["when"], self.ch.world)
                    self.next_variant_tree.insert(
                        "",
                        "end",
                        values=(s["id"], v["when"], v["text"]),
                        tags=("triggered",) if triggered else (),
                    )

    # ------------------------------------------------------------------
    # 修正
    # ------------------------------------------------------------------

    def _apply_world(self) -> None:
        deltas = {v: self.manual_world[v].get() for v in WORLD_VARS}
        self.ch.apply_manual_adjustment(deltas, self.escape_value.get())
        for var in WORLD_VARS:
            self.manual_world[var].set(0)
        self._refresh()
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
        self._status("派系状态已修正。")

    # ------------------------------------------------------------------

    def _reset(self) -> None:
        self.ch = Chronicle(self.data)
        self._clear(self.world_tree)
        self._clear(self.kindred_tree)
        self._clear(self.current_variant_tree)
        self._clear(self.next_variant_tree)
        self.home_scene.delete("1.0", "end")
        self.result_details.delete("1.0", "end")
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
