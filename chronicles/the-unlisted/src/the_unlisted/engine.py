"""《不在册者》的局势引擎。

一个循环 = 一次大事件。流程：

  1. 读人类常量（每阶段固定，不因玩家而改变方向）
  2. 读世界状态
  3. 由血族态度推导行动（方向 / 烈度 / 规模 / 破例）
  4. 乘上能力矩阵与世界状态杠杆
  5. 玩家介入（修正池）
  6. 结算世界状态：Δ = 固有脉冲 + Σ行动效果 + 玩家修正
  7. 由新世界状态更新血族态度
  8. 进入下一阶段，人类常量直接跳到下一列
"""

from __future__ import annotations

import copy
import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .data import ACTION_TYPE, ACTION_TYPE_ZH, WORLD_VARS, ChronicleData

MAX_SCALAR_DELTA_PER_ACT = 3
MAX_PATIENCE_DELTA_PER_ACT = 1
MAX_CAPABILITY_DELTA_PER_ACT = 1


# --------------------------------------------------------------------------
# 世界状态杠杆
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class LeverRule:
    var: str
    op: str
    threshold: int
    action_type: str | None  # None = 作用于全部行动
    factor: float
    why: str

    def applies(self, world: dict[str, int], action_type: str) -> bool:
        value = world[self.var]
        if self.op == "<=" and not value <= self.threshold:
            return False
        if self.op == ">=" and not value >= self.threshold:
            return False
        return self.action_type is None or self.action_type == action_type


LEVER_RULES: tuple[LeverRule, ...] = (
    LeverRule("legitimacy", "<=", 3, "reveal", 2.0, "正当性≤3：揭露类行动×2"),
    LeverRule("order", "<=", 3, "violent", 2.0, "秩序≤3：暴力类行动×2，失控概率上升"),
    LeverRule("feeding", "<=", 3, None, 0.5, "猎食条件≤3：血族全部行动×0.5（饿的人做不成事）"),
    LeverRule("exposure", ">=", 7, "conceal", 2.0, "暴露度≥7：隐匿类行动×2"),
    LeverRule("capital", "<=", 3, "coerce", 2.0, "资本信心≤3：要挟类行动×2"),
)

CRITICAL_BAND = (0, 3, 7, 10)
CRITICAL_FACTOR = 1.5

# 恐惧被触发时的破例方向（派系 → 新的立场）
FLIP_STANCE: dict[str, str] = {
    "quiet_court": "public",
    "new_blood": "abstain",
    "old_free": "delay",
    "barricade": "abstain",
    "zealots": "chaos",
}


def critical_pressure(value: int) -> bool:
    """变量进入极端区间时，系统在翻转前先变得不稳定。"""
    return value <= CRITICAL_BAND[1] or value >= CRITICAL_BAND[2]


# --------------------------------------------------------------------------
# 状态
# --------------------------------------------------------------------------


@dataclass
class KindredFactionState:
    faction_id: str
    zh: str
    stance: str
    patience: int
    capability: int
    abilities: dict[str, int]
    fears: list[dict]
    triggered_fears: set[str] = field(default_factory=set)

    @property
    def intensity_coefficient(self) -> int:
        """烈度系数 L = 6 − 耐心。"""
        return 6 - self.patience

    @property
    def action_type(self) -> str:
        return ACTION_TYPE.get(self.faction_id, "conceal")


@dataclass
class MortalFactionState:
    faction_id: str
    zh: str
    stance: str  # 本阶段的常量，来自 phase_stance 表
    capability: dict[str, int]


@dataclass
class PlayerMods:
    """玩家对本次循环的修正。这是说书人唯一需要手填的东西。"""

    outcome_quality: int = 0  # 0–3
    allocations: dict[str, int] = field(default_factory=dict)  # var -> delta
    witnessed_supernatural: int = 0
    escape_delta: int = 0
    agitation: int = 0
    note: str = ""

    @property
    def pool(self) -> int:
        return max(0, min(3, self.outcome_quality)) * 2

    def spent(self) -> int:
        return sum(abs(v) for v in self.allocations.values())

    def validate(self) -> list[str]:
        problems: list[str] = []
        if self.spent() > self.pool:
            problems.append(
                f"修正池只有 {self.pool} 点，但分配了 {self.spent()} 点"
            )
        for var in self.allocations:
            if var not in WORLD_VARS:
                problems.append(f"未知的世界状态变量：{var}")
        return problems


@dataclass
class ActionEffect:
    faction_id: str
    zh: str
    stance: str
    patience: int
    coefficient: int
    capability: int
    action_type: str
    levers: list[str]
    effect: float
    push: dict[str, float]


@dataclass
class MortalEffect:
    """人类一侧的行动效果。立场按阶段固定，但『这个立场能做成多少事』
    取决于该阵营的能力与世界状态。"""

    faction_id: str
    zh: str
    stance: str
    severity: int
    capability_score: float
    levers: list[str]
    effect: float
    push: dict[str, float]


@dataclass
class ActResult:
    act_id: str
    title: str
    phase: str
    intensity: float
    intensity_band: str
    actions: list[ActionEffect]
    inherent_pulse: dict[str, int]
    action_delta: dict[str, float]
    player_delta: dict[str, int]
    world_before: dict[str, int]
    world_after: dict[str, int]
    clamps_applied: list[str]
    collapse: dict | None
    kindred_changes: list[str]
    kindred_before: dict[str, dict[str, Any]]
    kindred_after: dict[str, dict[str, Any]]
    mortal_stance: dict[str, str]
    mortal_effects: list[MortalEffect] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# 引擎
# --------------------------------------------------------------------------


class Chronicle:
    def __init__(self, data: ChronicleData) -> None:
        self.data = data
        self.world: dict[str, int] = data.initial_world
        self.archive_location: str = data.chronicle["world_state"]["discrete"][
            "archive_location"
        ]["initial"]
        self.hunting_grounds: dict[str, str] = {
            k: v["initial"]
            for k, v in data.chronicle["world_state"]["discrete"]["hunting_grounds"][
                "districts"
            ].items()
        }
        self.kindred: dict[str, KindredFactionState] = {}
        for f in data.kindred["factions"]:
            init = f["initial"]
            self.kindred[f["id"]] = KindredFactionState(
                faction_id=f["id"],
                zh=f["zh"],
                stance=init["stance"],
                patience=init["patience"],
                capability=init["capability"],
                abilities=dict(f["abilities"]),
                fears=copy.deepcopy(f["fears"]),
            )
        self.mortal: dict[str, MortalFactionState] = {}
        self.act_cursor: int = 0
        self.history: list[ActResult] = []
        self.escape_prep: int = 0
        self.dead_mortals: list[str] = []
        self.lost_kindred: list[str] = []
        # 人类能力不会自己变。只有玩家能让它变——这是第七幕三根杠杆的电源。
        self.mortal_capability_delta: dict[str, int] = {}
        self._sync_mortal(self.current_act()["id"])

    # ---- 基本查询 ------------------------------------------------------

    def current_act(self) -> dict:
        idx = min(self.act_cursor, len(self.data.acts()) - 1)
        return self.data.acts()[idx]

    def current_act_id(self) -> str:
        return self.current_act()["id"]

    def _sync_mortal(self, act_id: str) -> None:
        stances = self.data.mortal_phase_stance(act_id)
        for f in self.data.mortal["factions"]:
            cap = dict(f["capability"])
            delta = self.mortal_capability_delta.get(f["id"], 0)
            cap["legal"] = max(0, min(6, cap["legal"] + delta))
            self.mortal[f["id"]] = MortalFactionState(
                faction_id=f["id"],
                zh=f["zh"],
                stance=stances[f["id"]],
                capability=cap,
            )

    def change_mortal_capability(self, faction_id: str, delta: int) -> dict[str, Any]:
        """玩家通过密室交易抬高或压低一个人类阵营的制度能力。

        **人类能力不会自己变。** 这是第七幕三根杠杆的电源：
        谁在议程上，取决于各阵营的行动效果，而效果里唯一能被玩家直接扳动的乘数就是它。
        累计修正每幕最多 ±1，总上限 ±3。
        """
        cur = self.mortal_capability_delta.get(faction_id, 0)
        self.mortal_capability_delta[faction_id] = max(-3, min(3, cur + delta))
        self._sync_mortal(self.current_act_id())
        st = self.mortal[faction_id]
        return {
            "阵营": st.zh,
            "合法能力": st.capability["legal"],
            "累计修正": self.mortal_capability_delta[faction_id],
        }

    def agenda_holder(self) -> dict[str, Any]:
        """谁在议程上 ＝ 本幕行动效果最高的制度阵营。"""
        acts = self.mortal_actions()
        best = max(acts, key=lambda a: a.effect)
        return {
            "faction": best.faction_id,
            "zh": best.zh,
            "stance": best.stance,
            "effect": best.effect,
            "table": [
                {"zh": a.zh, "effect": a.effect, "capability": a.capability_score}
                for a in sorted(acts, key=lambda a: -a.effect)
            ],
        }

    # ---- 终局判定 ------------------------------------------------------

    def finale_resolution(self) -> dict[str, Any]:
        """按当前局势推演终局：谁在议程上、替罪羊是谁、事件如何被定性。

        规则全部来自 `data/acts/act-06.json` 的 `levers`：

        - **谁在议程上** = 本幕人类行动效果最高者（能力 × 立场烈度 × 杠杆）。
        - **替罪羊** = 制度侧赢家提名的那句话；若旧自由邦的能力 ≥ 赢家的合法能力，
          街头否决生效，换成吴文辉那句。
        - **事件定性** = 按世界状态依次取第一条命中的定性语气。

        任何一幕结算后都可以调用它，用来告诉说书人此刻收束会落到哪里。
        """
        scenes = {a["id"]: a for a in self.data.acts()}
        levers = scenes["6.1"].get("levers", {})
        sc = levers.get("scapegoat", {})

        ranked = sorted(self.mortal_actions(), key=lambda a: -a.effect)
        winner = ranked[0]
        narratives = {
            n["nominated_by"]: n
            for n in sc.get("institutional", {}).get("narratives", [])
        }
        nominated = narratives.get(winner.zh, {})

        old_free = self.kindred["old_free"]
        winner_legal = self.mortal[winner.faction_id].capability["legal"]
        street = sc.get("street", {})
        street_override = old_free.capability >= winner_legal
        if street_override:
            scapegoat = {
                "who": street.get("who", "—"),
                "nominated_by": "旧自由邦（街头否决）",
                "line": street.get("line", ""),
                "means": street.get("means", ""),
                "why": street.get("why", ""),
            }
        else:
            scapegoat = {
                "who": nominated.get("who", "—"),
                "nominated_by": winner.zh,
                "line": nominated.get("line", ""),
                "means": nominated.get("means", ""),
                "why": nominated.get("why", ""),
            }
        institutional = {
            "who": nominated.get("who", "—"),
            "nominated_by": winner.zh,
            "line": nominated.get("line", ""),
            "means": nominated.get("means", ""),
            "why": nominated.get("why", ""),
        }

        annex_lever = levers.get("annex", {})
        annex_ranking = sorted(
            self.mortal.values(),
            key=lambda st: (-st.capability["legal"], st.faction_id != winner.faction_id),
        )
        annex_holder = annex_ranking[0]
        annex = next(
            (
                h
                for h in annex_lever.get("handlers", [])
                if h["who"] == annex_holder.zh
            ),
            {},
        )

        zone_lever = levers.get("zone", {})
        if old_free.capability >= 4:
            zone = zone_lever.get("table", [{}])[0].get("result", "—")
        elif old_free.capability == 3:
            zone = zone_lever.get("table", [{}, {}])[1].get("result", "—")
        else:
            zone = zone_lever.get("table", [{}, {}, {}])[2].get("result", "—")

        charac_lever = levers.get("characterization", {})
        charac = None
        for row in charac_lever.get("table", []):
            if row.get("when") == "其他":
                charac = charac or row
                continue
            if self._condition_hit(row.get("when", "")):
                charac = row
                break
        charac = charac or {"zh": "—", "text": "—"}

        return {
            "agenda": {
                "zh": winner.zh,
                "stance": winner.stance,
                "effect": winner.effect,
                "legal": winner_legal,
                "table": [
                    {
                        "zh": a.zh,
                        "stance": a.stance,
                        "effect": a.effect,
                        "legal": self.mortal[a.faction_id].capability["legal"],
                    }
                    for a in ranked
                ],
            },
            "scapegoat": scapegoat,
            "institutional": institutional,
            "street_override": street_override,
            "street_capability": old_free.capability,
            "street_rule": street.get("rule", ""),
            "annex": {
                "who": annex_holder.zh,
                "legal": annex_holder.capability["legal"],
                "how": annex.get("how", "—"),
            },
            "zone": {"who": "旧自由邦", "capability": old_free.capability, "result": zone},
            "characterization": charac,
            "collapse": self.check_collapse(),
            "escape": {"value": self.escape_prep, "text": self.escape_outcome()},
        }

    def _condition_hit(self, when: str) -> bool:
        """解析变体／定性条件，例如『暴露度 ≥ 8』『秩序 ≤ 3』。"""
        match = re.search(r"(秩序|正当性|猎食条件|暴露度|资本信心)\s*([≤≥])\s*(\d+)", when)
        if not match:
            return False
        var = {
            "秩序": "order",
            "正当性": "legitimacy",
            "猎食条件": "feeding",
            "暴露度": "exposure",
            "资本信心": "capital",
        }[match.group(1)]
        value = self.world[var]
        threshold = int(match.group(3))
        return value <= threshold if match.group(2) == "≤" else value >= threshold

    # ---- 杠杆 ----------------------------------------------------------

    def levers_for(self, action_type: str) -> tuple[float, list[str]]:
        factor = 1.0
        applied: list[str] = []
        for rule in LEVER_RULES:
            if rule.applies(self.world, action_type):
                factor *= rule.factor
                applied.append(rule.why)
        return factor, applied

    def critical_multiplier(self) -> float:
        if any(critical_pressure(v) for v in self.world.values()):
            return CRITICAL_FACTOR
        return 1.0

    # ---- 血族行动 ------------------------------------------------------

    def kindred_actions(self) -> list[ActionEffect]:
        crit = self.critical_multiplier()
        out: list[ActionEffect] = []
        for fid, st in self.kindred.items():
            faction = self.data.kindred_factions[fid]
            lever, applied = self.levers_for(st.action_type)
            effect = st.intensity_coefficient * st.capability * lever * crit
            vector = faction["vector"]
            push = {
                var: round(effect * vector.get(var, 0) / 60.0, 3)
                for var in WORLD_VARS
            }
            out.append(
                ActionEffect(
                    faction_id=fid,
                    zh=st.zh,
                    stance=st.stance,
                    patience=st.patience,
                    coefficient=st.intensity_coefficient,
                    capability=st.capability,
                    action_type=st.action_type,
                    levers=applied,
                    effect=round(effect, 2),
                    push=push,
                )
            )
        return out

    # ---- 人类行动 ------------------------------------------------------

    def mortal_levers(self, faction_id: str) -> tuple[float, list[str]]:
        """人类行动的世界状态杠杆。"""
        factor = 1.0
        applied: list[str] = []
        w = self.world
        if w["legitimacy"] <= 3 and faction_id in ("sovereign", "union"):
            factor *= 1.5
            applied.append("正当性≤3：主权派与联盟派 ×1.5（两边都更容易动员）")
        if w["order"] <= 3 and faction_id == "continuity":
            factor *= 0.5
            applied.append("秩序≤3：技术官僚派 ×0.5（国家自己都乱了，管不了）")
        if w["capital"] <= 3 and faction_id == "union":
            factor *= 1.5
            applied.append("资本信心≤3：联盟派 ×1.5（『我们别无选择』变得可信）")
        if w["capital"] >= 7 and faction_id == "sovereign":
            factor *= 1.5
            applied.append("资本信心≥7：主权派 ×1.5（『我们撑得住』变得可信）")
        if w["exposure"] >= 7:
            factor *= 1.5
            applied.append("暴露度≥7：全体人类 ×1.5（人人紧张，任何事都更容易引爆）")
        return factor, applied

    def mortal_actions(self) -> list[MortalEffect]:
        """人类行动效果 = 立场烈度 × 能力 × 世界状态杠杆。

        立场来自阶段常量表，永远不变；变的是『这个立场此刻能做成多少事』。
        """
        sev_map = self.data.chronicle["stance_severity"]["map"]
        out: list[MortalEffect] = []
        for fid, st in self.mortal.items():
            defn = self.data.mortal_factions[fid]
            sev = sev_map.get(st.stance, 1)
            cap = st.capability["legal"] + 0.5 * st.capability["illegal"]
            lever, applied = self.mortal_levers(fid)
            effect = sev * cap * lever
            vector = defn.get("vector", {})
            push = {
                var: round(effect * vector.get(var, 0) / 60.0, 3)
                for var in WORLD_VARS
            }
            out.append(
                MortalEffect(
                    faction_id=fid,
                    zh=st.zh,
                    stance=st.stance,
                    severity=sev,
                    capability_score=round(cap, 2),
                    levers=applied,
                    effect=round(effect, 2),
                    push=push,
                )
            )
        return out

    def consequence_ladder(self, faction_id: str, action: str) -> dict[str, Any]:
        """玩家干预人类世界之后，这个阵营能对他做什么。

        这不是"拦住玩家"的墙，而是"你干预之后会发生什么"的清单。
        action: show_face | coerce | supernatural | kill | leak
        """
        st = self.mortal[faction_id]
        leg, ill = st.capability["legal"], st.capability["illegal"]
        can: list[str] = []
        cannot: list[str] = [
            "感知超自然。全体人类的超自然能力恒为 0：看不穿模糊术、读不出支配术、发现不了被吸过血的人。"
        ]
        note = ""
        if action == "supernatural":
            can.append("只能通过痕迹反推：失踪人口、监控空档、行为异常、尸检报告、时间上的规律")
            if leg >= 4:
                can.append("用合法手段把零散痕迹串成模式")
            if leg >= 5:
                can.append("把模式升级为跨部门行动——**一套已经归档的记录，支配术撤不回来**")
            note = "血族的超自然优势是完整的，也是脆弱的：它有效，直到有人开始记录。"
        elif action == "show_face":
            if leg >= 4:
                can.append("传票、许可证审查、账户冻结、遣返程序")
            if leg >= 3:
                can.append("议会质询、媒体动员、工会施压")
            if ill >= 2:
                can.append("便衣与线人网")
            note = "公开身份等于把可被记录的东西交给对方。"
        elif action == "coerce":
            if ill >= 3:
                can.append("反向监视、找你的血锚、动你的牧群")
            if leg >= 4:
                can.append("把你恐吓过的人变成证人")
            note = "恐吓能压住一个人，压不住一个机构。"
        elif action == "kill":
            can.append("立刻有人补位——人类的职位不随人死（立场不变）")
            if leg >= 3:
                can.append("把死者变成符号或论据")
            if leg >= 4:
                can.append("全力侦办，并顺着死者的合法身份查到你的合法身份")
            note = "杀人不解决人类，只会给这个阵营一个更好的理由。"
        elif action == "leak":
            if leg >= 4:
                can.append("追查泄露源；而追查本身会产生新的记录")
            note = "泄密改变时序，不改变立场。"
        else:
            note = "未知行为类型。"
        return {
            "阵营": st.zh,
            "玩家行为": action,
            "合法能力": leg,
            "非法能力": ill,
            "能做什么": can,
            "不能做什么": cannot,
            "说明": note,
        }

    def intensity(
        self,
        actions: Sequence[ActionEffect] | None = None,
        mortal: Sequence[MortalEffect] | None = None,
    ) -> float:
        """烈度 = 血族行动效果均值与人类行动效果均值的平均。

        人类一侧按阶段固定，所以烈度的下限随阶段自动抬高——
        危机后期即使血族什么都不做，烈度也已经很高。
        """
        k = list(actions if actions is not None else self.kindred_actions())
        m = list(mortal if mortal is not None else self.mortal_actions())
        parts = [
            sum(a.effect for a in k) / len(k) if k else 0.0,
            sum(a.effect for a in m) / len(m) if m else 0.0,
        ]
        return round(sum(parts) / len(parts), 2)

    def intensity_band(self, value: float) -> str:
        th = self.data.chronicle["intensity"]["thresholds"]
        if value >= th["alarm"]:
            return "警报"
        if value >= th["watch"]:
            return "警戒"
        return "平稳"

    # ---- 结算 ----------------------------------------------------------

    def advance(
        self,
        player: PlayerMods | None = None,
        inherent_pulse: dict[str, int] | None = None,
    ) -> ActResult:
        player = player or PlayerMods()
        act = self.current_act()
        act_id = act["id"]
        # 人类立场按阶段重载：这是"历史大势"，每幕跳到下一列，不因玩家而改变。
        self._sync_mortal(act_id)
        before = dict(self.world)
        kindred_before = {
            fid: {
                "zh": st.zh,
                "stance": st.stance,
                "patience": st.patience,
                "capability": st.capability,
            }
            for fid, st in self.kindred.items()
        }
        notes: list[str] = []

        problems = player.validate()
        notes.extend(f"玩家修正警告：{p}" for p in problems)

        actions = self.kindred_actions()
        mortals = self.mortal_actions()
        intensity = self.intensity(actions, mortals)
        band = self.intensity_band(intensity)

        pulse = dict(inherent_pulse or act["inherent_pulse"])

        action_delta = {var: 0.0 for var in WORLD_VARS}
        for a in actions:
            for var, value in a.push.items():
                action_delta[var] += value
        for m in mortals:
            for var, value in m.push.items():
                action_delta[var] += value

        player_delta = {var: int(player.allocations.get(var, 0)) for var in WORLD_VARS}
        if player.witnessed_supernatural > 0:
            player_delta["exposure"] += min(3, player.witnessed_supernatural)
        if player.agitation:
            player_delta["order"] -= player.agitation
            player_delta["exposure"] += player.agitation

        raw = {
            var: pulse.get(var, 0) + action_delta[var] + player_delta[var]
            for var in WORLD_VARS
        }
        clamped, clamps = self._clamp(raw, before)
        self.world = clamped
        notes.extend(self._stabilize(player.witnessed_supernatural, intensity, pulse))
        if intensity >= self.data.chronicle["intensity"]["thresholds"]["alarm"]:
            if self.world["order"] > 0:
                self.world["order"] -= 1
            if self.world["exposure"] < 10:
                self.world["exposure"] += 1
            notes.append("烈度进入警报区间：秩序 −1、暴露度 +1")

        if player.escape_delta:
            self.escape_prep = max(
                0, min(self.data.escape_rules["range"][1], self.escape_prep + player.escape_delta)
            )

        collapse = self.check_collapse(intensity)
        if collapse:
            notes.append(f"崩盘轨道触发：{collapse['zh']}")

        kindred_changes = self._update_kindred(act_id)
        kindred_after = {
            fid: {
                "zh": st.zh,
                "stance": st.stance,
                "patience": st.patience,
                "capability": st.capability,
            }
            for fid, st in self.kindred.items()
        }
        self._update_hunting_grounds(act)

        result = ActResult(
            act_id=act_id,
            title=act["title"],
            phase=act["phase"],
            intensity=intensity,
            intensity_band=band,
            actions=actions,
            inherent_pulse=pulse,
            action_delta={k: round(v, 2) for k, v in action_delta.items()},
            player_delta=player_delta,
            world_before=before,
            world_after=dict(self.world),
            clamps_applied=clamps,
            collapse=collapse,
            kindred_changes=kindred_changes,
            kindred_before=kindred_before,
            kindred_after=kindred_after,
            mortal_stance=self.data.mortal_phase_stance(act_id),
            mortal_effects=mortals,
            notes=notes,
        )
        self.history.append(result)
        return result

    def apply_manual_adjustment(
        self,
        world_delta: dict[str, int] | None = None,
        escape_value: int | None = None,
    ) -> None:
        """主持人手动结算：允许在世界状态结算后做最后修正。"""
        scale = self.data.chronicle["world_state"]["scale"]
        lo, hi = scale["min"], scale["max"]
        for var, delta in (world_delta or {}).items():
            if var in WORLD_VARS:
                self.world[var] = max(lo, min(hi, self.world[var] + int(delta)))
        if escape_value is not None:
            escape_hi = self.data.escape_rules["range"][1]
            self.escape_prep = max(0, min(escape_hi, int(escape_value)))

    def adjust_faction(
        self,
        faction_id: str,
        patience_delta: int = 0,
        capability_delta: int = 0,
        stance: str | None = None,
    ) -> None:
        """主持人手动调整一个血族派系的下一幕状态。"""
        st = self.kindred[faction_id]
        st.patience = max(1, min(5, st.patience + int(patience_delta)))
        st.capability = max(0, min(5, st.capability + int(capability_delta)))
        if stance:
            st.stance = stance

    def _stabilize(
        self, witnessed: int, intensity: float, pulse: dict[str, int]
    ) -> list[str]:
        """城市会在安静的时候自己恢复一点。秩序与暴露度都不是单向棘轮。"""
        notes: list[str] = []
        alarm = self.data.chronicle["intensity"]["thresholds"]["alarm"]
        calm = pulse.get("order", 0) == 0 and intensity < alarm
        if calm and self.world["order"] < 10:
            self.world["order"] += 1
            notes.append("本幕没有大规模冲突：秩序自行恢复 +1")
        if witnessed == 0 and self.world["order"] >= 6 and self.world["exposure"] > 2:
            self.world["exposure"] -= 1
            notes.append("本幕没有超自然能力被目击，且秩序尚可：暴露度 −1")
        return notes

    def _clamp(
        self, raw: dict[str, float], before: dict[str, int]
    ) -> tuple[dict[str, int], list[str]]:
        scale = self.data.chronicle["world_state"]["scale"]
        lo, hi = scale["min"], scale["max"]
        cap = scale["max_delta_per_act"]
        out: dict[str, int] = {}
        clamps: list[str] = []
        for var in WORLD_VARS:
            delta = raw[var]
            if delta > cap:
                clamps.append(f"{var}: +{delta:.1f} 被压到 +{cap}")
                delta = cap
            elif delta < -cap:
                clamps.append(f"{var}: {delta:.1f} 被压到 -{cap}")
                delta = -cap
            value = int(round(before[var] + delta))
            out[var] = max(lo, min(hi, value))
        return out, clamps

    @staticmethod
    def _apply_kindred_effect(
        effect: str,
        patience: int,
        capability: int,
        stance: str,
    ) -> tuple[int, int, str]:
        if effect.startswith("patience "):
            return patience + int(effect.split()[1].replace("+", "")), capability, stance
        if effect.startswith("capability "):
            return patience, capability + int(effect.split()[1].replace("+", "")), stance
        if effect == "stance -> delay":
            return patience, capability, "delay"
        if effect == "stance -> destroy":
            return patience, capability, "destroy"
        if effect == "stance radicalize":
            return patience, capability, "destroy" if stance != "destroy" else stance
        return patience, capability, stance

    def _update_kindred(self, act_id: str) -> list[str]:
        """世界状态 → 下一阶段的血族态度。注意：耐心比立场先动。"""
        changes: list[str] = []
        faction_defs = self.data.kindred_factions
        for fid, st in self.kindred.items():
            defn = faction_defs[fid]
            new_patience, new_capability, new_stance = st.patience, st.capability, st.stance

            # 本场锚点：保证关键叙事节点一定会改变态度。
            for anchor in self.data.kindred.get("act_anchors", {}).get(act_id, []):
                if anchor["faction"] != fid:
                    continue
                new_patience, new_capability, new_stance = self._apply_kindred_effect(
                    anchor["effect"], new_patience, new_capability, new_stance
                )
                changes.append(f"{st.zh}：锚点 {anchor['effect']}（{anchor['why']}）")

            for sens in defn.get("sensitivity", []):
                var = sens["var"]
                direction = sens["when"]
                v = self.world[var]
                hit = (direction == "down" and v <= 3) or (direction == "up" and v >= 7)
                if not hit:
                    continue
                new_patience, new_capability, new_stance = self._apply_kindred_effect(
                    sens["effect"], new_patience, new_capability, new_stance
                )
                changes.append(f"{st.zh}：{sens['effect']}（{sens['why']}）")

            # 恐惧被触发 → 破例：做出与立场矛盾的行动
            for fear in st.fears:
                if fear["id"] in st.triggered_fears:
                    new_stance = FLIP_STANCE.get(fid, new_stance)
                    changes.append(f"{st.zh}：恐惧「{fear['zh']}」被触发，破例行动")

            new_patience = max(1, min(5, new_patience))
            new_capability = max(0, min(5, new_capability))
            if new_patience <= 2:
                new_capability -= 1
                changes.append(
                    f"{st.zh}：耐心降至 {new_patience}，过度动员导致能力 −1"
                )
            new_capability = max(0, min(5, new_capability))
            st.patience = max(
                st.patience - MAX_PATIENCE_DELTA_PER_ACT,
                min(st.patience + MAX_PATIENCE_DELTA_PER_ACT, new_patience),
            )
            st.capability = max(
                0,
                min(
                    5,
                    max(
                        st.capability - MAX_CAPABILITY_DELTA_PER_ACT,
                        min(
                            st.capability + MAX_CAPABILITY_DELTA_PER_ACT,
                            new_capability,
                        ),
                    ),
                ),
            )
            st.stance = new_stance
        return changes

    def _update_hunting_grounds(self, act: dict) -> None:
        if self.world["order"] <= 5:
            for key in ("teluk_saga",):
                if self.hunting_grounds.get(key) == "可控":
                    self.hunting_grounds[key] = "紧张"
        if self.world["order"] <= 2:
            self.hunting_grounds = {k: "关闭" for k in self.hunting_grounds}

    # ---- 破例与崩盘 ----------------------------------------------------

    def trigger_fear(self, faction_id: str, fear_id: str) -> None:
        """某个派系的恐惧条目被触发。它会做出与立场矛盾的行动。"""
        self.kindred[faction_id].triggered_fears.add(fear_id)

    def check_collapse(self, intensity: float | None = None) -> dict | None:
        intensity = self.intensity() if intensity is None else intensity
        w = self.world
        checks = {
            "martial_law": (w["order"] <= 2 and intensity >= 12) or w["order"] <= 1,
            "inquisition": w["exposure"] >= 10,
            "capital_collapse": w["capital"] <= 1,
        }
        for track in self.data.collapse_tracks:
            if checks.get(track["id"]):
                return track
        return None

    def escape_outcome(self) -> str:
        rules = self.data.escape_rules["resolution"]
        return rules[str(max(0, min(3, self.escape_prep)))]

    # ---- 外部接口：改变状态 --------------------------------------------

    def change_world(self, **deltas: int) -> dict[str, int]:
        """直接改动世界状态（说书人手动裁定用）。"""
        scale = self.data.chronicle["world_state"]["scale"]
        for var, delta in deltas.items():
            if var not in WORLD_VARS:
                raise KeyError(f"未知变量 {var}")
            self.world[var] = max(
                scale["min"], min(scale["max"], self.world[var] + delta)
            )
        return dict(self.world)

    def change_mortal_stance(self, faction_id: str, stance: str) -> list[str]:
        """人类立场**不允许**被改变方向——这里只记录一次形式上的调整。

        返回警告，说明为什么它不会生效。
        """
        f = self.mortal[faction_id]
        return [
            f"{f.zh} 的立场是历史大势的表征，不因玩家介入而改变方向。"
            f"（请求：{f.stance} → {stance}，已忽略；可改变的是时序、形式与代价承担者。）"
        ]

    def change_kindred(
        self,
        faction_id: str,
        *,
        stance: str | None = None,
        patience_delta: int = 0,
        capability_delta: int = 0,
    ) -> dict[str, Any]:
        st = self.kindred[faction_id]
        if stance is not None:
            st.stance = stance
        st.patience = max(1, min(5, st.patience + patience_delta))
        st.capability = max(0, min(5, st.capability + capability_delta))
        return {
            "faction": st.zh,
            "stance": st.stance,
            "patience": st.patience,
            "capability": st.capability,
        }

    def kill_mortal(self, char_id: str) -> dict[str, Any]:
        """杀死一个人类。职位会自动由替补接任，立场不变。"""
        char = self.data.mortal_chars[char_id]
        self.dead_mortals.append(char_id)
        subs = [
            s
            for s in char.get("substitutes", [])
            if s["id"] not in self.dead_mortals
        ]
        if not subs:
            return {
                "killed": char["zh"],
                "replacement": None,
                "note": char.get(
                    "substitute_note",
                    "没有替补。这个位置与这个人一起消失。",
                ),
            }
        return {
            "killed": char["zh"],
            "replacement": subs[0]["zh"],
            "note": subs[0].get("promotion", "立即接任，立场不变。"),
            "warning": "杀死人类领袖永远不会解决问题：立场属于职位，不属于人。",
        }

    def kill_kindred(self, char_id: str) -> dict[str, Any]:
        """杀死一个血族。能力、人脉、债务与记忆一起消失，没有任何东西可被继承。"""
        char = self.data.kindred_chars[char_id]
        self.lost_kindred.append(char_id)
        fid = char.get("faction")
        if fid and fid in self.kindred:
            self.kindred[fid].capability = max(0, self.kindred[fid].capability - 1)
        return {
            "killed": char["zh"],
            "replacement": None,
            "note": "血族的权力长在血里。没有任何东西可以被继承。",
            "capability_delta": -1 if fid else 0,
        }

    # ---- 输出 ----------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        return {
            "act": self.current_act_id(),
            "world": dict(self.world),
            "archive_location": self.archive_location,
            "hunting_grounds": dict(self.hunting_grounds),
            "kindred": {
                fid: {
                    "zh": st.zh,
                    "stance": st.stance,
                    "patience": st.patience,
                    "capability": st.capability,
                    "abilities": dict(st.abilities),
                }
                for fid, st in self.kindred.items()
            },
            "mortal_stance": {
                fid: st.stance for fid, st in self.mortal.items()
            },
            "escape_prep": self.escape_prep,
            "intensity": self.intensity(),
        }
