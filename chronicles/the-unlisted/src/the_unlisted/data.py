"""载入并索引《不在册者》的全部数据。

data/ 下的 JSON 是唯一真相来源。`data/acts/act-NN.json` 每幕一个文件，
文件内可以包含多个场景；引擎仍按场景顺序结算。docs/ 下的生成物请勿手改。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PACKAGE_ROOT / "data"

WORLD_VARS: tuple[str, ...] = ("order", "legitimacy", "feeding", "exposure", "capital")


def scene_label(scene: dict[str, Any]) -> str:
    """Human-facing scene number: 2.1, 3.1, 6.2, etc."""
    return f"{scene.get('act', '?')}.{scene.get('scene_no', 1)}"

# 每个血族派系的行动类型，用来判定世界状态杠杆。
ACTION_TYPE: dict[str, str] = {
    "quiet_court": "conceal",
    "new_blood": "conceal",
    "old_free": "coerce",
    "barricade": "reveal",
    "zealots": "violent",
}

ACTION_TYPE_ZH: dict[str, str] = {
    "conceal": "隐匿",
    "reveal": "揭露",
    "violent": "暴力",
    "coerce": "要挟",
}


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class ChronicleData:
    """四个 JSON 的合并视图，附带各种按 id 的索引。"""

    chronicle: dict[str, Any]
    acts_doc: dict[str, Any]
    kindred: dict[str, Any]
    mortal: dict[str, Any]
    props_doc: dict[str, Any]

    @classmethod
    def load(cls, data_dir: Path | str = DEFAULT_DATA_DIR) -> "ChronicleData":
        d = Path(data_dir)
        acts_dir = d / "acts"
        groups = [
            _read(f)
            for f in sorted(acts_dir.glob("act-*.json"))
        ]
        groups.sort(key=lambda g: g["act"])
        scenes = [scene for group in groups for scene in group["scenes"]]
        scenes.sort(key=lambda a: (a.get("act", a["index"]), a.get("scene_no", 1)))
        acts_doc = {
            "act_groups": groups,
            "acts": scenes,
        }
        return cls(
            chronicle=_read(d / "chronicle.json"),
            acts_doc=acts_doc,
            kindred=_read(d / "kindred.json"),
            mortal=_read(d / "mortal.json"),
            props_doc=_read(d / "props.json"),
        )

    # ---- 索引 ----------------------------------------------------------

    def __post_init__(self) -> None:
        self.kindred_factions: dict[str, dict] = {
            f["id"]: f for f in self.kindred["factions"]
        }
        self.mortal_factions: dict[str, dict] = {
            f["id"]: f for f in self.mortal["factions"]
        }

        # 人物索引：正式人物 + 替补（替补也是可被引用的人物）
        self.kindred_chars: dict[str, dict] = {
            c["id"]: {**c, "_kind": "kindred"} for c in self.kindred["characters"]
        }
        self.mortal_chars: dict[str, dict] = {}
        for c in self.mortal["characters"]:
            self.mortal_chars[c["id"]] = {**c, "_kind": "mortal", "_substitute": False}
            for s in c.get("substitutes", []):
                self.mortal_chars[s["id"]] = {
                    **s,
                    "_kind": "mortal",
                    "_substitute": True,
                    "faction": c.get("faction"),
                    "principal": c["id"],
                }

        self.act_groups: list[dict] = self.acts_doc["act_groups"]
        self.act_list: list[dict] = self.acts_doc["acts"]
        self.acts_by_id: dict[str, dict] = {a["id"]: a for a in self.act_list}
        self.acts_by_label: dict[str, dict] = {
            scene_label(a): a for a in self.act_list
        }
        self.groups_by_no: dict[int, dict] = {
            g["act"]: g for g in self.act_groups
        }
        self.rooms: dict[str, dict] = self.chronicle["venues"]["room_meta"]
        self.key_props: list[dict] = self.props_doc["key_props"]
        self.ambient_props: list[dict] = self.props_doc["ambient_props"]
        self.props_by_id: dict[str, dict] = {
            p["id"]: p for p in self.key_props + self.ambient_props
        }

    # ---- 便捷取值 ------------------------------------------------------

    @property
    def initial_world(self) -> dict[str, int]:
        return dict(self.chronicle["world_state"]["initial"])

    @property
    def collapse_tracks(self) -> list[dict]:
        return self.chronicle["collapse_tracks"]

    @property
    def escape_rules(self) -> dict:
        return self.chronicle["escape"]

    @property
    def elysium(self) -> dict:
        return self.chronicle["elysium"]

    @property
    def venues(self) -> list[dict]:
        return self.chronicle["venues"]["list"]

    @property
    def venue_of_room(self) -> dict[str, str]:
        return self.chronicle["venues"]["rooms"]

    @property
    def mortal_lever_rows(self) -> list[dict]:
        """人类行动的世界状态杠杆表。数值只写在 mortal.json 里。"""
        return self.mortal.get("levers", {}).get("rows", [])

    @property
    def mortal_tie_priority(self) -> dict[str, int]:
        """平局时谁先拿到议程。数字越小越优先。"""
        order = self.mortal.get("tie_break", {}).get("priority", [])
        return {fid: i for i, fid in enumerate(order)}

    @property
    def archive_prop(self) -> dict:
        for p in self.key_props:
            if p["id"] == "trusteeship_archive":
                return p
        return {}

    @property
    def archive_options(self) -> list[dict]:
        """托管档案的所有可能去向（含数值影响）。唯一真相来源是 props.json。"""
        return self.archive_prop.get("outcomes", [])

    @property
    def archive_default_line(self) -> dict[str, str]:
        """默认世界线：每一幕档案本来会在哪里。"""
        return self.archive_prop.get("default_line", {})

    def archive_label(self, value: str) -> str:
        for opt in self.archive_options:
            if opt["id"] == value:
                return opt["action"]
        for opt in self.chronicle["world_state"]["discrete"]["archive_location"][
            "options"
        ]:
            if opt["id"] == value:
                return opt["zh"]
        return value

    def acts(self) -> list[dict]:
        return self.act_list

    def groups(self) -> list[dict]:
        return self.act_groups

    def group(self, act_no: int) -> dict:
        return self.groups_by_no[act_no]

    def act(self, ident: str | int) -> dict:
        if isinstance(ident, int):
            return self.act_list[ident - 1]
        key = str(ident)
        if key in self.acts_by_label:
            return self.acts_by_label[key]
        return self.acts_by_id[key.upper()]

    def mortal_phase_stance(self, act_id: str) -> dict[str, str]:
        table = self.mortal["phase_stance"]
        idx = self.act_list.index(self.acts_by_id[act_id.upper()])
        return {fid: row[idx] for fid, row in table["table"].items()}

    def cluster(self, act_id: str) -> list[dict]:
        return self.act(act_id)["elysium"]["rooms"]

    def name_of(self, char_id: str) -> str:
        for pool in (self.kindred_chars, self.mortal_chars):
            if char_id in pool:
                return pool[char_id]["zh"]
        return char_id

    def unknown_ids(self) -> list[tuple[str, str]]:
        """回传所有被引用却找不到的人物 id，方便校对同步。"""
        missing: list[tuple[str, str]] = []
        for act in self.act_list:
            pools = [
                ("attendance.mortal", act["attendance"]["mortal"], self.mortal_chars),
                ("attendance.kindred", act["attendance"]["kindred"], self.kindred_chars),
            ]
            for label, ids, pool in pools:
                for cid in ids:
                    if cid not in pool:
                        missing.append((f"{act['id']}.{label}", cid))
            for room in act["elysium"]["rooms"]:
                for key in ("present", "added"):
                    for entry in room.get(key, []):
                        cid = entry if isinstance(entry, str) else entry["id"]
                        if cid not in self.kindred_chars:
                            missing.append((f"{act['id']}.{room['room']}.{key}", cid))
                for entry in room.get("absent", []):
                    cid = entry if isinstance(entry, str) else entry["id"]
                    if cid not in self.kindred_chars:
                        missing.append((f"{act['id']}.{room['room']}.absent", cid))
        return missing
