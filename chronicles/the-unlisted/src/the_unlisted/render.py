"""从 data/ 生成 markdown 文档。

生成的文档与 JSON 数值完全一致——它们不是手写的，所以不会漂移。
用法：python -m the_unlisted.cli render
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from .data import ACTION_TYPE, ACTION_TYPE_ZH, WORLD_VARS, ChronicleData, scene_label
from .engine import Chronicle

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DOCS = PACKAGE_ROOT / "docs"

HEADER = (
    "<!-- 本文件由 `python -m the_unlisted.cli render` 从 data/*.json 生成。 -->\n\n"
)


def _w(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _stance_zh(data: ChronicleData, sid: str) -> str:
    return data.chronicle["elysium"].get("_stance", {}).get(sid, sid)


STANCE_ZH = {
    "destroy": "守土",
    "public": "开门",
    "delay": "拖字",
    "abstain": "旁观",
    "chaos": "搅局",
}

ROLE_ORDER = ["代表", "副手", "变数", "极乐境守护者"]


# --------------------------------------------------------------------------
# 幕文件
# --------------------------------------------------------------------------


def render_act(
    data: ChronicleData, act: dict, include_header: bool = True, include_scene: bool = True
) -> str:
    act_id = act["id"]
    L: list[str] = [HEADER] if include_header else []
    if include_header:
        L.append(f"# 第 {act['act']} 幕 · {scene_label(act)} {act['title']}\n\n")
        L.append(f"**阶段**：{act['phase']}　**时间**：{act['time']}\n\n")
        L.append(f"**场景编号**：{scene_label(act)}\n\n")
        L.append("---\n\n")

    # 说书人视角
    L.append("## 一、说书人视角\n\n")
    loadout = act.get("loadout", {})
    if loadout:
        L.append("### 本幕只需准备\n\n")
        L.append(f"{loadout.get('prepare', '')}\n\n")
        if loadout.get("ignore"):
            L.append(f"> {loadout['ignore']}\n\n")
    truth = act.get("truth", {})
    if truth:
        L.append("### 事件真相\n\n")
        L.append(f"{truth.get('what', '')}\n\n")
        if truth.get("patterns"):
            L.append("**它借的骨架——真实历史里反复出现的形状**\n\n")
            for x in truth["patterns"]:
                L.append(f"- {x}\n")
            L.append("\n")
        if truth.get("causes"):
            L.append("**引信是什么——说书人从三条里选一条**\n\n")
            for c in truth["causes"]:
                L.append(f"**{c['zh']}**：{c['text']}\n\n")
            if truth.get("choice"):
                L.append(f"{truth['choice']}\n\n")
        if truth.get("vampire_layer"):
            L.append(f"**血族在这一幕做什么**：{truth['vampire_layer']}\n\n")
        if truth.get("faction_logic"):
            L.append(
                "**各派系以为自己在做什么，以及实际发生了什么**\n\n"
                "| 派系 | 他们以为 | 实际作用 | 玩家接口 |\n"
                "| --- | --- | --- | --- |\n"
            )
            for row in truth["faction_logic"]:
                L.append(
                    f"| **{row['who']}** | {row['thinks']} | "
                    f"{row['actually']} | {row['player_lever']} |\n"
                )
            L.append("\n")
        for line in truth.get("sides_believe", []):
            L.append(f"- {line}\n")
        L.append(f"\n**不是真的**：{truth.get('not_true', '')}\n\n")
        L.append(f"**玩家能改变**：{truth.get('players_can', '')}\n\n")
        L.append(f"**玩家不能改变**：{truth.get('players_cannot', '')}\n\n")
    intents = act.get("intents", [])
    if intents:
        L.append("### 各方在做什么（以及为什么）\n\n")
        L.append("| 侧 | 谁 | 想要 | 在做 |\n| --- | --- | --- | --- |\n")
        for it in intents:
            L.append(
                f"| {it['side']} | **{it['who']}** | {it['wants']} | {it['does']} |\n"
            )
        L.append("\n")
    pacing = act.get("pacing", {})
    if pacing:
        L.append("### 推进节奏\n\n")
        L.append(f"**开场**：{pacing.get('opening', '')}\n\n")
        for i, b in enumerate(pacing.get("beats", []), 1):
            L.append(f"{i}. {b}\n")
        L.append(f"\n**卡住时**：{pacing.get('if_stalled', '')}\n\n")
        L.append(f"**收尾**：{pacing.get('closing', '')}\n\n")

    variants = act.get("variants", [])
    if variants:
        L.append("### 局势变体\n\n")
        L.append(
            "**开场前读一遍世界状态，只应用命中的那几条。** "
            "没命中的不要提——玩家不需要知道自己错过了什么。\n\n"
        )
        L.append("| 条件 | 改什么 | 改成 |\n| --- | --- | --- |\n")
        for v in variants:
            L.append(f"| {v['when']} | {v['kind']} | {v['text']} |\n")
        L.append("\n")

    site = act.get("site")
    if site:
        L.append(f"### 场地 · {site['zh']}\n\n")
        for key, label in (
            ("where", "在哪儿"),
            ("grave", "那座墓"),
            ("inside", "里面是什么"),
            ("keeper", "看墓的人"),
            ("clock", "时限"),
            ("danger", "而这就是赌注"),
            ("why_torpor", "他为什么睡着"),
        ):
            if site.get(key):
                L.append(f"- **{label}**：{site[key]}\n")
        L.append("\n")
        if site.get("knowledge"):
            L.append("**谁知道什么**\n\n")
            L.append("| 谁 | 知道多少 |\n| --- | --- |\n")
            for k in site["knowledge"]:
                L.append(f"| **{k['who']}** | {k['knows']} |\n")
            L.append("\n")
    gd = act.get("guardians")
    if gd:
        L.append(f"### {gd['zh']}\n\n")
        L.append(f"- **在哪里**：{gd['where']}\n")
        L.append(f"- **出现条件**：{gd['trigger']}\n")
        L.append(f"- **他们做什么**：{gd['what_they_do']}\n")
        L.append(f"- **这意味着**：{gd['meaning']}\n")
        L.append(f"\n{gd['note']}\n\n")
    searchers = act.get("searchers")
    if searchers:
        L.append(f"### {searchers['zh']}\n\n")
        if searchers.get("logic"):
            L.append(f"{searchers['logic']}\n\n")
        L.append(f"{searchers['note']}\n\n")
        if searchers.get("rows"):
            L.append("| 谁 | 什么时候来 | 怎么发现的 |\n| --- | --- | --- |\n")
            for r in searchers["rows"]:
                L.append(f"| {r['who']} | {r['when']} | {r['how']} |\n")
            L.append("\n")
        if searchers.get("range"):
            L.append(f"{searchers['range']}\n\n")
        if searchers.get("fourth"):
            L.append(f"\n{searchers['fourth']}\n\n")
        if searchers.get("appendix"):
            L.append(f"*{searchers['appendix']}*\n\n")
    timeline = act.get("timeline")
    if timeline:
        L.append(f"### {timeline['zh']}\n\n")
        L.append("| 时间 | 谁 | 查到什么 |\n| --- | --- | --- |\n")
        for r in timeline["rows"]:
            L.append(f"| {r['when']} | **{r['who']}** | {r['what']} |\n")
        L.append(f"\n{timeline['note']}\n\n")
    inf = data.kindred.get("infighting")
    plan = inf["scenes"].get(act_id) if inf else None
    if plan:
        L.append(f"### {inf['zh']}\n\n")
        L.append(f"- **默认归因**：{plan['target']}\n")
        L.append(f"- **本幕怎么推**：{plan['move']}\n")
        L.append(f"- **留下的证据**：{plan['evidence']}\n")
        L.append(f"- **玩家能改什么**：{plan['player_lever']}\n")
        L.append(
            f"\n*这是公开给说书人的内斗规则：暴露度不会下降，"
            f"但调查先落到谁头上可以被改写。完整机制见 `roster.md` 的「{inf['zh']}」。*\n\n"
        )

    levers = act.get("levers", {})
    if levers:
        zh_of = {x["id"]: x["zh"] for x in data.chronicle["world_state"]["variables"]}
        L.append("### 三根杠杆\n\n")
        L.append(f"{levers.get('rule', '')}\n\n")
        for key in ("power", "scapegoat", "annex", "zone"):
            lv = levers.get(key)
            if not lv:
                continue
            L.append(f"#### {lv['zh']}\n\n")
            L.append(f"{lv['rule']}\n\n")
            if key == "power":
                for i, h in enumerate(lv.get("how", []), 1):
                    L.append(f"{i}. {h}\n")
                L.append(f"\n{lv.get('example', '')}\n\n")
                continue
            if key == "scapegoat":
                if lv.get("vehicle"):
                    L.append(f"{lv['vehicle']}\n\n")
                if lv.get("clause"):
                    L.append(f"> {lv['clause']}\n\n")
                inst = lv.get("institutional")
                if inst:
                    L.append(f"**{inst['zh']}**——{inst['rule']}\n\n")
                    L.append("| 谁被写进去 | 谁提名 | 那句话怎么写 | 说的是 | 为什么是他 |\n")
                    L.append("| --- | --- | --- | --- | --- |\n")
                    for c in inst["narratives"]:
                        L.append(
                            f"| **{c['who']}** | {c['nominated_by']} | 「{c['line']}」 | "
                            f"{c['means']} | {c['why']} |\n"
                        )
                    L.append("\n")
                    if inst.get("all_true"):
                        L.append(f"{inst['all_true']}\n\n")
                street = lv.get("street")
                if street:
                    L.append(f"**{street['zh']}**——{street['rule']}\n\n")
                    L.append(
                        "| 谁被写进去 | 那句话怎么写 | 说的是 | 为什么是他 |\n"
                        "| --- | --- | --- | --- |\n"
                        f"| **{street['who']}** | 「{street['line']}」 | {street['means']} | "
                        f"{street['why']} |\n\n"
                    )
            elif key == "annex":
                L.append("| 谁在议程上 | 合法 | 怎么处理附则十九 | 结果 |\n| --- | --- | --- | --- |\n")
                for h in lv["handlers"]:
                    d = h.get("delta", {})
                    eff = "　".join(f"{zh_of.get(k, k)} {v:+d}" for k, v in d.items()) or "—"
                    L.append(f"| **{h['who']}** | {h['legal']} | {h['how']} | {eff} |\n")
            elif key == "zone":
                L.append("| 条件 | 结果 |\n| --- | --- |\n")
                for row in lv["table"]:
                    L.append(f"| {row['when']} | {row['result']} |\n")
            L.append(f"\n{lv.get('note', '')}\n\n")

    # 今夜的地方
    L.append("---\n\n## 二、今夜的地方\n\n")
    L.append(f"> {act['elysium']['note']}\n\n")
    L.append(
        "**三个派系不可能在同一个地方聚会。** 玩家能去哪些地方，"
        "取决于他们的阵营与私人关系。\n\n"
    )
    v_of = data.venue_of_room
    notes = act.get("venue_notes", {})
    by_venue: dict[str, list[dict]] = {}
    for room in act["elysium"]["rooms"]:
        by_venue.setdefault(v_of.get(room["room"], "?"), []).append(room)
    L.append("| 场所 | 归属 | 谁在 | 玩家能不能进 | 本幕 |\n| --- | --- | --- | --- | --- |\n")
    for v in data.venues:
        vid = v["id"]
        can = v["player"].replace("**", "")
        L.append(
            f"| **{v['zh']}** | {v['owner']} | {v['who']} | {can} | "
            f"{notes.get(vid, '—')} |\n"
        )
    L.append("\n")
    L.append("*四个场所的完整描述见 `roster.md` 的「附录与场所」。以下是本幕的到场情况。*\n\n")
    for v in data.venues:
        rooms = by_venue.get(v["id"], [])
        if not rooms:
            continue
        L.append(f"**{v['zh']}**\n\n")
        L.append("| 一方 | 门 | 在场 | 缺席 | 新出现 |\n| --- | --- | --- | --- | --- |\n")
        for room in rooms:
            fac = data.kindred_factions[room["faction"]]["zh"]
            present = "、".join(data.name_of(c) for c in room["present"]) or "—"
            absent = "；".join(
                f"**{data.name_of(e['id'])}**（{e.get('why', '')}）"
                for e in room.get("absent", [])
            ) or "—"
            added = "；".join(
                f"**{data.name_of(e['id'])}**（{e.get('why', '')}）"
                for e in room.get("added", [])
            ) or "—"
            L.append(
                f"| {fac} | {room.get('door', 'open')} | "
                f"{present} | {absent} | {added} |\n"
            )
        L.append("\n")
        for room in rooms:
            if room.get("note"):
                L.append(
                    f"- {data.kindred_factions[room['faction']]['zh']}：{room['note']}\n"
                )
        L.append("\n")
    L.append(
        "**门语、密室可以做的交易、经验与世界状态规则**——全部见 `roster.md`。\n\n"
    )

    # 标志事件
    L.append("---\n\n## 三、标志事件\n\n")
    L.append("### 前提\n\n")
    L.append(f"{act['premise']}\n\n")

    if include_scene:
        L.append("### 场景描写\n\n")
        L.append("*可直接朗读。段落之间留白，不要一口气念完。*\n\n")
        for para in act.get("scene", []):
            L.append(f"{para}\n\n")
    present = {
        e["prop"]: e
        for e in act.get("props_in_scene", [])
        if e["prop"] in data.props_by_id
    }
    focus = [pid for pid in act.get("focus", []) if pid in data.props_by_id]
    ambient_ids = {p["id"] for p in data.ambient_props}
    background_key = [
        e
        for e in act.get("props_in_scene", [])
        if e["prop"] in data.props_by_id
        and e["prop"] not in ambient_ids
        and e["prop"] not in focus
    ]
    ambient = [
        e
        for e in act.get("props_in_scene", [])
        if e["prop"] in ambient_ids and e["prop"] not in focus
    ]
    if present or focus or background_key or ambient:
        L.append("### 本幕道具\n\n")
        if focus:
            L.append("**本幕争抢焦点**（对应正文里的上标）\n\n")
            for i, pid in enumerate(focus, 1):
                e = present.get(pid, {})
                p = data.props_by_id.get(pid)
                name = p["zh"] if p else pid
                L.append(
                    f"<sup>{i}</sup> **{name}** —— 在 **{e.get('holder', '？')}**。"
                    f"*{e.get('note', '')}*\n"
                )
            L.append("\n")
        elif background_key or ambient:
            L.append(
                "*本场景没有争抢焦点。**以下条目只以引用、缺席或布景的方式存在。***\n\n"
            )
        if background_key:
            L.append("**关键道具（本幕不可直接取得）**\n\n")
            for e in background_key:
                p = data.props_by_id.get(e["prop"])
                name = p["zh"] if p else e["prop"]
                note = f"　*{e['note']}*" if e.get("note") else ""
                L.append(f"- {name} —— **{e['holder']}**{note}\n")
            L.append("\n")
        if ambient:
            L.append("**其他在场道具**（无机制，只是布景）\n\n")
            for e in ambient:
                p = data.props_by_id.get(e["prop"])
                name = p["zh"] if p else e["prop"]
                note = f"　*{e['note']}*" if e.get("note") else ""
                L.append(f"- {name} —— **{e['holder']}**{note}\n")
            L.append("\n")

    L.append("### 三种入口\n\n")
    for ep in act["entry_points"]:
        L.append(f"- **{ep['type']}**：{ep['text']}\n")
    L.append("\n")

    player_hooks = act.get("player_hooks", [])
    if player_hooks:
        L.append("### 玩家支点\n\n")
        L.append("| 支点 | 关联角色 | 具体做法 | 为什么重要 |\n")
        L.append("| --- | --- | --- | --- |\n")
        for hook in player_hooks:
            L.append(
                f"| **{hook['zh']}** | {hook['who']} | {hook['hook']} | "
                f"{hook['why_matters']} |\n"
            )
        L.append("\n")

    L.append("### 支点\n\n")
    for lv in act["leverage"]:
        L.append(f"- **{lv['zh']}**——{lv['note']}\n")
    L.append("\n")

    L.append("### 默认结果\n\n")
    L.append(f"> {act['default_outcome']}\n\n")
    L.append(
        "如果玩家完全不介入，事情按这个结果收束。世界状态照常更新，下一幕照常开场。\n\n"
    )

    L.append("### 钩子\n\n")
    L.append(f"> {act['hook']}\n\n")

    L.append("### 脱出条件\n\n")
    L.append("本幕结束时，以下条件必须全部满足，否则不要推进到下一幕：\n\n")
    for i, cond in enumerate(act["exit_conditions"], 1):
        L.append(f"{i}. {cond}\n")
    L.append("\n")

    L.append("### 出场人物\n\n")
    L.append("**人类**：" + "、".join(
        data.name_of(c) for c in act["attendance"]["mortal"]
    ) + "\n\n")
    L.append("**血族**：" + "、".join(
        data.name_of(c) for c in act["attendance"]["kindred"]
    ) + "\n\n")

    newcomers = [c for c in act["attendance"]["kindred"] if first_appearance(data, c) == act_id]
    newcomers += [
        c for c in act["attendance"]["mortal"]
        if first_appearance(data, c) == act_id and c in data.kindred_chars
    ]
    if newcomers:
        L.append("### 本幕首次出场\n\n")
        L.append(
            "**以下人物是第一次登场。先把形象和说话方式念出来，再让他们开口。**"
            "（完整档案见 `roster.md` 的「血族派系与人物」）\n\n"
        )
        for cid in newcomers:
            c = data.kindred_chars[cid]
            clan = data.kindred.get("clans", {}).get(c["clan"], c["clan"])
            L.append(f"**{c['zh']}**　{c['role']}｜{clan}｜血权 {c['blood_potency']}\n\n")
            L.append(f"- **形象**：{c.get('appearance', '')}\n")
            if c.get("speech"):
                L.append(f"- **语言风格**：{c['speech']}\n")
            if c.get("disciplines"):
                L.append(f"- **律能**：{c['disciplines']}\n")
            L.append("\n")

    ambush = act.get("ambush")
    hunt = act.get("hunting")
    combat = act.get("combat")
    vfight = act.get("vampire_fight")
    zh_of = {x["id"]: x["zh"] for x in data.chronicle["world_state"]["variables"]}
    if ambush or hunt or combat or vfight:
        L.append("---\n\n## 四、暴力\n\n")
        cons = act.get("constraints")
        if cons:
            L.append(f"### {cons['zh']}\n\n")
            L.append(f"{cons['note']}\n\n")
            L.append("| 被拿走的东西 | 怎么拿走的 |\n| --- | --- |\n")
            for r in cons["rows"]:
                L.append(f"| **{r['zh']}** | {r['text']} |\n")
            L.append(f"\n{cons['summary']}\n\n")
        rp = (
            act.get("real_problem")
            or (combat or {}).get("real_problem")
            or (vfight or {}).get("real_problem")
        )
        fn = (
            act.get("fire_note")
            or (combat or {}).get("fire_note")
            or (vfight or {}).get("fire_note")
        )
        if rp:
            L.append(f"### 这一场真正的问题（不是打倒对手）\n\n{rp}\n\n")
        if fn:
            L.append(f"**关于「燃烧瓶」**：{fn}\n\n")
        L.append(
            "> **这一段的存在理由**：模糊术加燃烧瓶能解决掉任何一个「一屋子你打不过、"
            "又不该杀的人」的场景。所以每一场暴力的问题都刻意**不是**打倒对手——"
            "**打倒对手永远有更快的办法，而那样办法解决不了这一场。**\n\n"
        )
        if ambush:
            L.append(f"### {ambush['zh']}\n\n")
            L.append(f"{ambush['unavoidable']}\n\n")
            L.append("**发现它的方式——三条**\n\n")
            for d in ambush["discovery"]:
                L.append(f"- **{d['sense']}**：{d['text']}\n")
            L.append(f"\n{ambush['hook']}\n\n")
            L.append(f"#### 真相（说书人限定）\n\n{ambush['truth']}\n\n")
            L.append(f"**注意**：{ambush['note']}\n\n")
        if hunt:
            L.append(f"### {hunt['zh']}\n\n")
            L.append(f"{hunt['why']}\n\n")
            L.append(f"**规则**：{hunt['rule']}\n\n")
            L.append(f"**陷阱**：{hunt['trap']}\n\n")
            L.append(f"**必须做的选择**：{hunt['choice']}\n\n")
        if combat:
            L.append(f"### {combat['zh']}\n\n")
            L.append(f"{combat['unavoidable']}\n\n")
            L.append(f"{combat['why_now']}\n\n")
            opp = combat["opposition"]
            L.append(f"#### 对手\n\n")
            L.append(f"**是谁**：{opp['who']}\n\n")
            L.append(f"**真相**：{opp['truth']}\n\n")
            st = opp["stat"]
            L.append(f"- **模板**：{st['template']}\n")
            L.append(f"- **属性**：{st['attributes']}\n")
            L.append(f"- **技能**：{st['skills']}\n")
            L.append(f"- **备注**：{st['note']}\n\n")
            L.append(f"**人数**：{opp['count']}\n\n")
            mech = combat["mechanic"]
            L.append(f"#### {mech['zh']}\n\n")
            for key, label in (
                ("rousal", "激励检定"),
                ("hunger", "饥渴之后不会降下来"),
                ("blood", "打完之后满地是血"),
                ("frenzy", "必须做的狂乱检定"),
            ):
                if mech.get(key):
                    L.append(f"- **{label}**：{mech[key]}\n")
            L.append("\n#### 四种收场\n\n")
            zh_of = {x["id"]: x["zh"] for x in data.chronicle["world_state"]["variables"]}
            L.append("| 收场 | 代价 | 世界状态 |\n| --- | --- | --- |\n")
            for oc in combat["outcomes"]:
                d = oc.get("delta", {})
                eff = "　".join(f"{zh_of.get(k, k)} {v:+d}" for k, v in d.items()) or "—"
                L.append(f"| **{oc['zh']}** | {oc['cost']} | {eff} |\n")
            L.append(f"\n**奖励**：{combat['reward']}\n\n")
            L.append(f"**说书人注意**：{combat['note']}\n\n")
        if vfight:
            L.append(f"### {vfight['zh']}\n\n")
            L.append(f"**什么时候会打起来**：{vfight['when']}\n\n")
            L.append(f"**谁对谁**：{vfight['who']}\n\n")
            L.append(f"**为什么**：{vfight['why']}\n\n")
            L.append(f"**引信**：{vfight['fuse']}\n\n")
            L.append(f"**它长什么样**：{vfight['how']}\n\n")
            L.append(f"**它怎么停**：{vfight['blood']}\n\n")
            L.append(f"**真正的危险**：{vfight['frenzy']}\n\n")
            if vfight.get("awakening"):
                L.append(f"{vfight['awakening']}\n\n")
            L.append("**玩家能做什么**\n\n")
            L.append("| 选择 | 代价 | 世界状态 |\n| --- | --- | --- |\n")
            for ch in vfight["choices"]:
                d = ch.get("delta", {})
                eff = "　".join(
                    f"{zh_of.get(k, k)} {v:+d}" for k, v in d.items()
                ) or "—"
                L.append(f"| **{ch['zh']}** | {ch['cost']} | {eff} |\n")
            L.append(f"\n**结果**：{vfight['outcome']}\n\n")
            L.append(f"**说书人注意**：{vfight['note']}\n\n")

    # 数值
    L.append("---\n\n## 五、数值影响\n\n")
    p = act["inherent_pulse"]
    L.append("### 人类固有脉冲（固定）\n\n")
    L.append("| 变量 | 变化 |\n| --- | --- |\n")
    for var in WORLD_VARS:
        zh = next(v["zh"] for v in data.chronicle["world_state"]["variables"] if v["id"] == var)
        L.append(f"| {zh} | {p.get(var, 0):+d} |\n")
    L.append("\n")

    L.append("### 人类立场（本阶段常量）\n\n")
    L.append("| 阵营 | 立场 | 烈度 | 合法 | 非法 | 超自然 | 本阶段行动效果 |\n")
    L.append("| --- | --- | --- | --- | --- | --- | --- |\n")
    stances = data.mortal_phase_stance(act_id)
    sev_map = data.chronicle["stance_severity"]["map"]
    for fid, stance in stances.items():
        cap = data.mortal_factions[fid]["capability"]
        sev = sev_map.get(stance, 1)
        score = cap["legal"] + 0.5 * cap["illegal"]
        L.append(
            f"| {data.mortal_factions[fid]['zh']} | {stance} | {sev} | "
            f"{cap['legal']} | {cap['illegal']} | {cap['supernatural']} | "
            f"{sev} × {score:g} = **{sev * score:g}** |\n"
        )
    L.append("\n")
    L.append(
        "**立场按阶段固定，永远不变。变的是『这个立场此刻能做成多少事』——"
        "那由能力与世界状态决定。** 这就是人类能力矩阵的全部用途：\n"
        "它不是『他们想不想』，而是『他们做得到多少』。\n\n"
    )
    L.append(
        "| 世界状态 | 对人类的杠杆 |\n| --- | --- |\n"
        "| 正当性 ≤ 3 | 主权派与联盟派 ×1.5（两边都更容易动员） |\n"
        "| 秩序 ≤ 3 | 技术官僚派 ×0.5（国家自己都乱了，管不了） |\n"
        "| 资本信心 ≤ 3 | 联盟派 ×1.5（『我们别无选择』变得可信） |\n"
        "| 资本信心 ≥ 7 | 主权派 ×1.5（『我们撑得住』变得可信） |\n"
        "| 暴露度 ≥ 7 | 全体人类 ×1.5（人人紧张，任何事都更容易引爆） |\n\n"
    )

    anchors = data.kindred.get("act_anchors", {}).get(act_id, [])
    if anchors:
        L.append("### 血族态度锚点\n\n")
        L.append(
            "本场结束时，无论世界状态是否越过阈值，以下变化都会触发：\n\n"
            "| 派系 | 变化 | 原因 |\n| --- | --- | --- |\n"
        )
        for anchor in anchors:
            faction = data.kindred_factions[anchor["faction"]]["zh"]
            L.append(
                f"| {faction} | `{anchor['effect']}` | {anchor['why']} |\n"
            )
        L.append("\n")

    L.append("### 血族默认行动\n\n")
    L.append("| 派系 | 本幕行动 |\n| --- | --- |\n")
    for kd in act["kindred_defaults"]:
        L.append(
            f"| {data.kindred_factions[kd['faction']]['zh']} | {kd['action']} |\n"
        )
    L.append("\n")
    L.append(
        "以上是**默认行动**。实际行动由局势引擎按各派系当前的立场、耐心与能力推导。\n\n"
    )

    # 局势卡
    L.append("---\n\n## 六、本幕局势卡\n\n")
    L.append("```text\n")
    L.append(
        f"第 {act['act']} 幕 · {scene_label(act)} {act['title']} · {act['time']}\n\n"
    )
    L.append("世界状态（进入时）\n")
    L.append("  秩序 __ / 正当性 __ / 猎食条件 __ / 暴露度 __ / 资本信心 __\n")
    L.append("  档案位置：______________\n")
    L.append("  本幕猎场：______________\n\n")
    L.append("血族（四步推导）\n")
    L.append("  派系 | 立场 | 耐心 | 烈度 L | 能力 | 效果 E | 本幕行动\n")
    for f in data.kindred["factions"]:
        L.append(f"  {f['zh']:<8}|      |      |        |      |        |\n")
    L.append("\n玩家介入\n")
    L.append("  结果质量 __（0–3） → 修正池 __ 点\n")
    L.append("  分配：秩序 __ 正当性 __ 猎食条件 __ 暴露度 __ 资本信心 __\n")
    L.append("  目击超自然：__ 次（每次 +1 暴露度）\n")
    L.append("  逃亡准备：__\n\n")
    L.append("结算\n")
    L.append("  秩序 → __ / 正当性 → __ / 猎食条件 → __\n")
    L.append("  暴露度 → __ / 资本信心 → __\n")
    L.append("  烈度 __ （平稳 / 警戒≥8 / 警报≥12）\n\n")
    L.append("崩盘检查\n")
    L.append("  戒严    ：秩序≤2 且烈度≥12，或秩序≤1\n")
    L.append("  审判庭  ：暴露度≥10\n")
    L.append("  资本崩溃：资本信心≤1\n")
    L.append("```\n\n")
    L.append("---\n\n*经验与世界状态规则见 `roster.md`。本幕结束语：填写一句新闻标题。*\n\n")
    L.append(f"```text\n{act['hook']}\n```\n")
    return "".join(L)


# --------------------------------------------------------------------------
# 名册
# --------------------------------------------------------------------------


def render_kindred(data: ChronicleData) -> str:
    L: list[str] = [HEADER]
    L.append("# 血族派系与人物表\n\n")
    L.append(
        "> **血族的权力属于人身。** 杀死一个血族领袖，他的能力、人脉、债务与记忆一起消失，"
        "没有任何东西可以被继承。**因此血族没有替补。**\n\n"
    )
    inf = data.kindred.get("infighting")
    if inf:
        L.append(f"## {inf['zh']}\n\n")
        L.append(f"{inf['premise']}\n\n")
        L.append(f"**{inf['law']}**\n\n")
        L.append(f"**判定**：{inf['rule']}\n\n")
        L.append(
            "*逐幕默认归因、栽赃手法与玩家接口见 `roster.md` 的同名一节。*\n\n"
        )
    L.append("---\n\n## 一、两条轴上的五个派系\n\n")
    L.append("| 派系 | 年龄轴 | 派系轴 | 一句话 | 立场 | 耐心 | 能力 |\n")
    L.append("| --- | --- | --- | --- | --- | --- | --- |\n")
    for f in data.kindred["factions"]:
        init = f["initial"]
        L.append(
            f"| **{f['zh']}** | {f['axis_age']} | {f['axis_sect']} | {f['one_line']} | "
            f"{STANCE_ZH.get(init['stance'], init['stance'])} | {init['patience']} | {init['capability']} |\n"
        )
    L.append("\n")

    L.append("## 二、派系详表\n\n")
    for f in data.kindred["factions"]:
        init = f["initial"]
        ab = f["abilities"]
        L.append(f"### {f['zh']}（{f['id']}）\n\n")
        L.append(f"**一句话**：{f['one_line']}\n\n")
        L.append(f"**想要**：{f['wants']}\n\n")
        L.append(f"**真正想要**：{f['secret_want']}\n\n")
        L.append(f"**不愿承认**：{f['unwilling_to_admit']}\n\n")
        L.append(f"**行动方式**：{f['method']}\n\n")
        L.append(f"**托管三年留下的旧账**：{f['trusteeship_debt']}\n\n")
        L.append(
            f"**初始**：立场 {STANCE_ZH.get(init['stance'], init['stance'])}"
            f"　耐心 {init['patience']}　能力 {init['capability']}\n\n"
        )
        L.append(
            f"**行动能力**：合法 {ab['legal']}　非法 {ab['illegal']}　超自然 {ab['supernatural']}"
            f"　（行动类型：{ACTION_TYPE_ZH.get(ACTION_TYPE.get(f['id'], 'conceal'), '') or ''}）\n\n"
        )
        L.append(
            "**方向向量**：" + "　".join(f"{k} {v:+d}" for k, v in f["vector"].items()) + "\n\n"
        )
        if f.get("fears"):
            L.append("**恐惧**：" + "；".join(x["zh"] for x in f["fears"]) + "\n\n")
        else:
            L.append("**恐惧**：无。他们没有可失去的。\n\n")
        L.append("**敏感度**：\n\n")
        for s in f.get("sensitivity", []):
            L.append(f"- {s['var']} {s['when']} → `{s['effect']}`（{s['why']}）\n")
        L.append("\n")
        L.append(f"**改变条件**：{f['flip_condition']}\n\n")
        L.append(
            f"**密室**：{data.rooms[f['room']]['zh']}"
            f"　**代表**：{data.name_of(f['leader'])}"
            f"　**副手**：{data.name_of(f['second'])}"
            f"　**变数**：{data.name_of(f['wildcard']) if f['wildcard'] else '无'}\n\n"
        )
        L.append("---\n\n")

    anchors = data.kindred.get("act_anchors", {})
    if anchors:
        L.append("## 三、逐场态度锚点\n\n")
        L.append(
            "| 场景 | 派系 | 强制变化 | 原因 |\n| --- | --- | --- | --- |\n"
        )
        for act_id, rows in anchors.items():
            for anchor in rows:
                faction = data.kindred_factions[anchor["faction"]]["zh"]
                L.append(
                    f"| {act_id} | {faction} | `{anchor['effect']}` | "
                    f"{anchor['why']} |\n"
                )
        L.append("\n")

    L.append("## 四、人物表\n\n")
    by_faction: dict[str, list[dict]] = {}
    for c in data.kindred["characters"]:
        by_faction.setdefault(c.get("faction") or "_neutral", []).append(c)

    for f in data.kindred["factions"]:
        L.append(f"### {f['zh']}\n\n")
        for c in by_faction.get(f["id"], []):
            L.append(_kindred_char_block(data, c))
        L.append("\n")

    neutrals = by_faction.get("_neutral", [])
    if neutrals:
        L.append("### 中立\n\n")
        for c in neutrals:
            L.append(_kindred_char_block(data, c))
    return "".join(L)


def first_appearance(data: ChronicleData, char_id: str) -> str | None:
    """这个人物第一次出现在哪一幕——用来把形象与语言风格放在初次登场处。"""
    for a in data.acts():
        if char_id in a["attendance"]["kindred"]:
            return a["id"]
        if char_id in a["attendance"]["mortal"] and char_id in data.kindred_chars:
            return a["id"]
        for room in a["elysium"].get("rooms", []):
            ids = list(room.get("present", []))
            ids += [e["id"] for e in room.get("added", [])]
            if char_id in ids:
                return a["id"]
    return None


def _kindred_char_block(data: ChronicleData, c: dict) -> str:
    clan = data.kindred["clans"].get(c["clan"], c["clan"])
    L = [f"#### {c['zh']}　<span>{c['role']}</span>\n\n"]
    L.append(
        f"- **氏族**：{clan}　**血权**：{c['blood_potency']}　"
        f"**外貌年龄**：{c['apparent_age']}\n"
    )
    L.append(f"- **初拥**：{c['embraced']}\n")
    L.append(f"- **形象**：{c['appearance']}\n")
    if c.get("speech"):
        L.append(f"- **语言风格**：{c['speech']}\n")
    if c.get("disciplines"):
        L.append(f"- **律能**：{c['disciplines']}\n")
    L.append(f"- **动机**：{c['motive']}\n")
    L.append(f"- **秘密**：{c['secret']}\n")
    L.append(f"- **钩子**：{c['hook']}\n\n")
    return "".join(L)


def render_mortal(data: ChronicleData) -> str:
    L: list[str] = [HEADER]
    L.append("# 人类派系与人物表（含替补）\n\n")
    note = data.mortal["design_note"]
    L.append(f"> **{note['zh']}**\n>\n> {note['explain']}\n>\n> {note['consequence']}\n\n")
    L.append("---\n\n## 一、三个固定阵营\n\n")
    L.append("| 阵营 | 立场 | 合法 | 非法 | 超自然 |\n| --- | --- | --- | --- | --- |\n")
    for f in data.mortal["factions"]:
        cap = f["capability"]
        L.append(
            f"| **{f['zh']}** | {f['position']} | {cap['legal']} | {cap['illegal']} | {cap['supernatural']} |\n"
        )
    L.append("\n")
    L.append("**三个阵营的立场在整个剧本中不变。** 这是历史大势的表征。\n\n")
    for f in data.mortal["factions"]:
        L.append(f"### {f['zh']}\n\n")
        L.append(f"**立场**：{f['position']}\n\n")
        if f.get("scale"):
            L.append(f"**它是哪一种东西**：{f['scale']}\n\n")
        L.append(f"**核心论据**：{f['core_argument']}\n\n")
        L.append(f"**支持者**：{f['supporters']}\n\n")
        L.append(f"**弱点**：{f['weakness']}\n\n")
        L.append(f"**代言人**：{data.name_of(f['spokesperson'])}\n\n")
        if f.get("special"):
            L.append(f"**备注**：{f['special']}\n\n")
    L.append("---\n\n## 二、各阶段立场表（常量）\n\n")
    table = data.mortal["phase_stance"]["table"]
    acts = data.acts()
    L.append("| 阵营 | " + " | ".join(f"{a['id']}" for a in acts) + " |\n")
    L.append("| --- |" + " --- |" * len(acts) + "\n")
    for fid, row in table.items():
        L.append(f"| {data.mortal_factions[fid]['zh']} | " + " | ".join(row) + " |\n")
    L.append("\n")
    L.append("| 幕 | 阶段 |\n| --- | --- |\n")
    for a in acts:
        L.append(f"| {a['id']} | {a['phase']} |\n")
    L.append("\n---\n\n## 三、人物表\n\n")
    for c in data.mortal["characters"]:
        fac = data.mortal_factions[c["faction"]]["zh"] if c.get("faction") else "—"
        L.append(f"### {c['zh']}　<span>{c['role']}</span>\n\n")
        L.append(f"- **年龄**：{c['age'] if c['age'] is not None else '—'}　**阵营**：{fac}\n")
        L.append(f"- **一句话**：{c['one_line']}\n")
        L.append(f"- **裂缝**：{c['crack']}\n")
        subs = c.get("substitutes", [])
        if subs:
            L.append("- **替补**：\n")
            for s in subs:
                L.append(
                    f"  - **{s['zh']}**（{s['age']}，{s['role']}）"
                    f"——晋升条件：{s['promotion']}；{s['note']}\n"
                )
        else:
            L.append(
                f"- **替补**：无。{c.get('substitute_note', '这个位置与这个人一起消失。')}\n"
            )
        L.append("\n")
    return "".join(L)


def render_elysium(data: ChronicleData) -> str:
    L: list[str] = [HEADER]
    L.append(f"# 极乐境座位表（{len(data.groups())} 幕）\n\n")
    L.append(f"> {data.elysium['venue']['zh']}——{data.elysium['venue']['note']}\n\n")
    L.append(f"**守护者**：{data.name_of(data.elysium['keeper'])}\n\n")
    L.append("## 座位即情报\n\n")
    L.append(
        "每一幕密室的分配都会变。某个人消失、某个人出现、某扇门贴上白纸——"
        "这些都直接表示上一幕改变了什么。玩家不需要被告诉，他们只需要看。\n\n"
    )
    L.append("| 幕 | 密室 | 派系 | 门 | 在场 | 缺席 |\n| --- | --- | --- | --- | --- | --- |\n")
    for act in data.acts():
        for room in act["elysium"]["rooms"]:
            meta = data.rooms[room["room"]]
            fac = data.kindred_factions[room["faction"]]["zh"]
            present = "、".join(data.name_of(c) for c in room["present"]) or "—"
            absent = (
                "；".join(
                    f"{data.name_of(e['id'])}：{e.get('why', '')}"
                    for e in room.get("absent", [])
                )
                or "—"
            )
            L.append(
                f"| {act['id']} | {meta['zh']} | {fac} | {room.get('door', 'open')} | "
                f"{present} | {absent} |\n"
            )
    L.append("\n")
    return "".join(L)


_NEGATIVE = ("无关", "没有", "尚未", "不存在", "无人", "未知")


def _mark(status: str) -> str:
    """道具在某一幕是否真的在场。"""
    if not status:
        return "·"
    return "·" if any(k in status for k in _NEGATIVE) else "●"


def _delta_cell(v: int) -> str:
    return "—" if not v else f"**{v:+d}**"


def render_props(data: ChronicleData) -> str:
    L: list[str] = [HEADER]
    L.append("# 托管档案\n\n")
    note = data.props_doc["design_note"]
    L.append(
        f"> **{note['zh']}**\n>\n> {note['explain']}\n>\n"
        f"> **数量预算**：{note['budget']}\n>\n> {note['why_budget']}\n\n"
    )
    chain = data.props_doc.get("link_chain")
    if chain:
        L.append(f"---\n\n## 〇、{chain['zh']}\n\n")
        L.append(f"{chain['what']}\n\n")
        L.append("**附则十九的全文（《过渡安排》第 187 页）**\n\n")
        for line in chain["annex_text"]:
            L.append(f"> {line}\n>\n")
        L.append("\n")
        L.append(f"{chain['why_dangerous']}\n\n")
        L.append(f"**缄默庭的做法**：{chain['quiet_court_method']}\n\n")
        L.append("### 危险程度矩阵\n\n")
        L.append(f"{chain['matrix_note']}\n\n")
        L.append("| 附则十九 | 托管档案在哪 | 暴露度 | 判定 |\n| --- | --- | --- | --- |\n")
        for row in chain["matrix"]:
            exp = row["exposure"]
            cell = f"**+{exp}**" if exp else "0"
            L.append(
                f"| {row['annex']} | {row['archive']} | {cell} | {row['verdict']} |\n"
            )
        L.append(f"\n**为什么两边都得动**：{chain['cannot']}\n\n")
        ladder = chain.get("recognition_ladder")
        if ladder:
            L.append(f"### {ladder['zh']}\n\n")
            L.append("| 幕 | 玩家看到什么 | 应意识到什么 |\n| --- | --- | --- |\n")
            for row in ladder["rows"]:
                L.append(
                    f"| {row['act']} | {row['surface']} | {row['takeaway']} |\n"
                )
            L.append("\n")
    L.append("---\n\n## 一、道具总表\n\n")
    acts = data.acts()
    L.append(
        "`●` = **本幕争抢焦点**　`○` = 在场但不争抢　`·` = 不在场\n\n"
    )

    def where(pid: str) -> list[str]:
        marks: list[str] = []
        for a in acts:
            if pid in a.get("focus", []):
                marks.append("●")
            elif any(e["prop"] == pid for e in a.get("props_in_scene", [])):
                marks.append("○")
            else:
                marks.append("·")
        return marks

    L.append("| 道具 | 类型 | " + " | ".join(a["id"] for a in acts) + " |\n")
    L.append("| --- | --- |" + " --- |" * len(acts) + "\n")
    for p in data.key_props:
        typ = data.props_doc["types"].get(p["type"], p["type"])
        marks = " | ".join(where(p["id"]))
        L.append(f"| **{p['zh']}** | {typ} | {marks} |\n")
    for p in data.ambient_props:
        marks = " | ".join(where(p["id"]))
        L.append(f"| {p['zh']}（氛围） | — | {marks} |\n")
    L.append("\n---\n\n## 二、关键道具逐件详表\n\n")
    for p in data.key_props:
        typ = data.props_doc["types"].get(p["type"], p["type"])
        L.append(f"### {p['zh']}\n\n")
        if p.get("aliases"):
            L.append(f"*别名：{'、'.join(p['aliases'])}　类型：{typ}*\n\n")
        else:
            L.append(f"*类型：{typ}*\n\n")
        L.append(f"> {p['one_line']}\n\n")
        L.append(f"**为什么重要**：{p['why']}\n\n")
        if p.get("result_rule"):
            L.append(f"**不可以被改变的**：{p['result_rule']}\n\n")
        if p.get("package"):
            pk = p["package"]
            L.append(f"**{pk['zh']}**\n\n")
            L.append("| 包裹里的东西 | 说明 |\n| --- | --- |\n")
            for part in pk["parts"]:
                L.append(f"| **{part['zh']}** | {part['note']} |\n")
            L.append(f"\n{pk['why']}\n\n")
        L.append("**逐幕流转**\n\n")
        L.append("| 幕 | 状态 |\n| --- | --- |\n")
        for a in acts:
            st = p["acts"].get(a["id"])
            if st:
                L.append(f"| {a['id']} | {st} |\n")
        L.append("\n**使用结果（量化）**\n\n")
        L.append("| 用法 | 秩序 | 正当性 | 猎食条件 | 暴露度 | 资本信心 | 说明 |\n")
        L.append("| --- | --- | --- | --- | --- | --- | --- |\n")
        for oc in p["outcomes"]:
            d = oc.get("delta", {})
            cells = " | ".join(_delta_cell(d.get(v, 0)) for v in WORLD_VARS)
            L.append(f"| **{oc['action']}** | {cells} | {oc['note']} |\n")
        L.append(f"\n**如果它消失**：{p['if_lost']}\n\n")
        L.append("---\n\n")
    if data.ambient_props:
        L.append("## 三、氛围道具（不携带任何数值）\n\n")
        for p in data.ambient_props:
            L.append(f"### {p['zh']}\n\n")
            L.append(f"> {p['one_line']}\n\n")
            L.append(f"{p['note']}\n\n")
            L.append("| 幕 | 状态 |\n| --- | --- |\n")
            for a in acts:
                st = p["acts"].get(a["id"])
                if st:
                    L.append(f"| {a['id']} | {st} |\n")
            L.append("\n")
    return "".join(L)


_CONSEQUENCE_ACTIONS = (
    ("supernatural", "使用超自然能力（律能、血缚、吸血）"),
    ("show_face", "公开身份插手人类事务"),
    ("coerce", "私下恐吓或收买"),
    ("kill", "杀人"),
    ("leak", "泄露文件或情报"),
)


def render_consequences(data: ChronicleData) -> str:
    ch = Chronicle(data)
    L: list[str] = [HEADER]
    L.append("# 人类反制能力速查\n\n")
    L.append(
        "> **玩家无法被阻止，只能被结算。** 人类没有超自然能力（全体恒为 0），"
        "他们只能看见痕迹。所以拦住玩家的不是墙，是后果。\n\n"
    )
    L.append("---\n\n## 一、唯一的硬规则\n\n")
    L.append("**全体人类的超自然能力恒为 0。** 他们看不穿模糊术、读不出支配术、发现不了被吸过血的人。\n\n")
    L.append("两条推论：\n\n")
    L.append("1. **血族的超自然优势是完整的。** 玩家几乎总能做成他们想做的事——这是对的，别去堵它。\n")
    L.append("2. **但这个优势是脆弱的。** 它有效，直到有人开始记录。而**一套已经归档的记录，支配术撤不回来**。\n\n")
    L.append(
        "所以 GM 的杠杆不是「不让你做」，而是「做完之后，有一份文件开始存在」。\n\n"
    )
    L.append("---\n\n## 二、能力档位对照\n\n")
    L.append("| 能力 | 合法能力意味着 | 非法能力意味着 |\n| --- | --- | --- |\n")
    L.append("| 0 | 无 | 无 |\n")
    L.append("| 1 | 无 | 无 |\n")
    L.append("| 2 | 一般交涉与申诉 | 便衣与线人 |\n")
    L.append("| 3 | 议会质询、媒体动员、工会施压 | 反向监视、找血锚、动牧群 |\n")
    L.append("| 4 | 传票、许可证审查、账户冻结、遣返程序 | 制造证据、收买证人 |\n")
    L.append("| 5 | 跨部门行动、修改规则本身 | —— |\n\n")
    L.append(
        "**注意 4 与 5 这一档。** 合法能力强的人类比非法能力强的人类更可怕，"
        "因为合法的东西会留下文件，而文件不能被杀掉。\n\n"
    )
    L.append("---\n\n## 三、按玩家行为的反制清单\n\n")
    for aid, label in _CONSEQUENCE_ACTIONS:
        L.append(f"### {label}\n\n")
        sample = ch.consequence_ladder(data.mortal["factions"][0]["id"], aid)
        L.append(f"> {sample['说明']}\n\n")
        L.append("| 阵营 | 合法 | 非法 | 能做什么 |\n| --- | --- | --- | --- |\n")
        for f in data.mortal["factions"]:
            r = ch.consequence_ladder(f["id"], aid)
            can = "；".join(r["能做什么"]) or "——"
            L.append(
                f"| {r['阵营']} | {r['合法能力']} | {r['非法能力']} | {can} |\n"
            )
        L.append(f"\n**谁都做不到**：{'；'.join(sample['不能做什么'])}\n\n")
    return "".join(L)


LAYER_TAGS = {
    "quiet_court": "血族·秘盟·老",
    "new_blood": "血族·秘盟·新",
    "old_free": "血族·叛党·老",
    "barricade": "血族·叛党·新",
    "zealots": "血族·魔宴·新",
}

STANCE_DESC = {
    "destroy": "保住自治。不要有人在上面。",
    "public": "接受新秩序，并抢在前面站好位置。",
    "delay": "一直谈。谈不成就是胜利。",
    "abstain": "不表态，只保住自己的东西。（很少用到）",
    "chaos": "让任何趋势都被放大。",
}


def render_glossary(data: ChronicleData) -> str:
    L: list[str] = [HEADER]
    L.append("# 名词辨析表\n\n")
    L.append(
        "> 这个剧本里有四层名字，它们**描述的不是同一件事**。"
        "这一页只有一个用途：读到任何一个名字时，三秒内知道它属于哪一层。\n\n"
    )
    L.append(
        "> **一句话记住：人类的街头阵营在争那份文件，血族的立场在争这块地。**\n\n"
    )
    L.append("---\n\n## 一、最容易搞混的四组\n\n")
    L.append("| 名字 | 属于哪一层 | 一句话 | 别和谁搞混 |\n| --- | --- | --- | --- |\n")
    L.append(
        "| **撕毁方** | 人类·街头 | 要否决《南方架构》、拆解联合机构 | 守土（血族立场） |\n"
        "| **公开方** | 人类·街头 | 要公开《过渡安排》，再用《南方架构》把它合法化 | 开门（血族立场） |\n"
        "| **主权派** | 人类·制度 | 与撕毁方目标相同，但他们是坐在办公室里的人 | 撕毁方（街头） |\n"
        "| **联盟派** | 人类·制度 | 与公开方目标相同，但他们是写文章、开会的人 | 公开方（街头） |\n"
        "| **守土 / 开门** | 血族·立场 | 描述的是**这块地**归谁管 | 撕毁方 / 公开方（那份文件） |\n"
    )
    L.append("\n---\n\n## 二、四层名字\n\n")

    L.append(
        f"### 第一层 · 人类制度阵营（{len(data.mortal['factions'])}）\n\n"
    )
    L.append("坐在议会、部门、编辑部里。**立场按阶段固定，永不改变。** 说书人只读表，不建模。\n\n")
    L.append("| 名字 | 一句话 | 代言人 |\n| --- | --- | --- |\n")
    for f in data.mortal["factions"]:
        L.append(
            f"| **{f['zh']}** | {f['position']} | {data.name_of(f['spokesperson'])} |\n"
        )
    L.append("\n")

    L.append("### 第二层 · 人类街头阵营（2）\n\n")
    L.append("在街上。**会分裂、会重组、会被捕。** 第四幕起登场。\n\n")
    L.append("| 名字 | 一句话 |\n| --- | --- |\n")
    L.append("| **撕毁方** | 要否决《南方架构》，拆解联合机构。主权派主导，老中青混合，纪律严明。 |\n")
    L.append("| **公开方** | 要公开《过渡安排》，再用《南方架构》把它合法化。联盟派主导，年轻为主。 |\n")
    L.append(
        "\n**Titik Api 是第三件东西**：它是学生志愿者网络，出现在第一到第三幕，"
        "早于两个阵营成形。三者不要混为一谈。\n\n"
    )

    L.append("### 第三层 · 血族派系（5）\n\n")
    L.append("**立场会变，而且玩家能改变它。** 括号里的标签就是它的坐标。\n\n")
    L.append("| 名字 | 坐标 | 一句话 | 场所 | 初始立场 |\n| --- | --- | --- | --- | --- |\n")
    venue_of = data.venue_of_room
    for f in data.kindred["factions"]:
        vid = venue_of[f["room"]]
        venue = next(v["zh"] for v in data.venues if v["id"] == vid)
        L.append(
            f"| **{f['zh']}** | {LAYER_TAGS[f['id']]} | {f['one_line']} | "
            f"{venue} | {STANCE_ZH[f['initial']['stance']]} |\n"
        )
    L.append("\n")

    L.append("### 第四层 · 血族立场（5）\n\n")
    L.append("描述的是**这块地**归谁管，不是那份文件。\n\n")
    L.append("| 立场 | 一句话 | 初始是谁 |\n| --- | --- | --- |\n")
    for sid, zh in STANCE_ZH.items():
        who = [f["zh"] for f in data.kindred["factions"] if f["initial"]["stance"] == sid]
        L.append(f"| **{zh}** | {STANCE_DESC[sid]} | {'、'.join(who) or '无人'} |\n")
    L.append("\n")

    L.append("### 附 · 世界状态与崩盘轨道\n\n")
    L.append("| 名字 | 范围 | 一句话 |\n| --- | --- | --- |\n")
    for v in data.chronicle["world_state"]["variables"]:
        L.append(f"| **{v['zh']}** | 0–10 | {v['meaning']} |\n")
    for t in data.collapse_tracks:
        L.append(f"| **{t['zh']}**（崩盘轨道） | — | {t['driver']} |\n")
    L.append("\n")

    L.append("---\n\n## 三、写名册时的约定\n\n")
    L.append(
        "- 血族派系名后面一律带坐标，例如 **旧自由邦（叛党·老）**。\n"
        "- 人类阵营名后面一律带层，例如 **撕毁方（街头）**、**主权派（制度）**。\n"
        "- 人名不带标签——是人就不用解释。\n"
        "- 血族立场名（守土 / 开门 / 拖字 / 旁观 / 搅局）只出现在数值与动机栏，不出现在组织名里。\n"
    )
    inf = data.kindred.get("infighting")
    if inf:
        L.append(f"\n---\n\n## 四、{inf['zh']}\n\n")
        L.append(f"{inf['premise']}\n\n")
        L.append(f"**原则**：{inf['law']}\n\n")
        L.append(f"**判定**：{inf['rule']}\n\n")
        L.append("### 做法\n\n| 做法 | 一句话 |\n| --- | --- |\n")
        for m in inf["methods"]:
            L.append(f"| **{m['zh']}** | {m['text']} |\n")
        L.append(f"\n**玩家怎么改归因**：{inf['counterplay']}\n\n")
        L.append(f"**什么时候失效**：{inf['limits']}\n\n")
        L.append(
            "### 逐幕默认归因\n\n"
            "| 幕 | 默认落点 | 怎么推 | 留下的证据 | 玩家能改什么 |\n"
            "| --- | --- | --- | --- | --- |\n"
        )
        for a in data.acts():
            plan = inf["scenes"].get(a["id"])
            if plan:
                L.append(
                    f"| {a['id']} | **{plan['target']}** | {plan['move']} | "
                    f"{plan['evidence']} | {plan['player_lever']} |\n"
                )
        L.append("\n")
    return "".join(L)


def render_appendix(data: ChronicleData) -> str:
    ap = data.chronicle["appendix"]
    L: list[str] = [HEADER]
    L.append(f"# {ap['zh']}\n\n")
    L.append(f"{ap['purpose']}\n\n")

    L.append("---\n\n## 一、场所\n\n")
    for v in data.venues:
        L.append(f"### {v['zh']}\n\n")
        L.append(f"- **归属**：{v['owner']}　**谁在**：{v['who']}\n")
        L.append(f"- **在哪儿**：{v['place']}\n")
        L.append(f"- **准入**：{v['access']}\n")
        L.append(f"- **规矩**：{v['rule']}\n")
        L.append(f"- **玩家**：{v['player']}\n")
        L.append(f"- **风险**：{v['risk']}\n\n")
    L.append(f"> **座位即情报**：{data.elysium['seating_rule']['note']}\n\n")

    L.append("---\n\n## 二、密室可以做的交易\n\n")
    for deal in data.elysium["deal_types"]:
        L.append(f"**{deal['zh']}**——{deal['desc']}\n\n")
        L.append(f"- 收益：{'、'.join(deal['payouts'])}\n")
        L.append(f"- 代价：{deal['cost']}\n\n")

    L.append("---\n\n## 三、通用规则\n\n")
    for r in ap["rules"]:
        L.append(f"- {r}\n")
    L.append("\n")

    L.append("---\n\n## 四、" + ap["interested"]["zh"] + "\n\n")
    L.append(f"{ap['interested']['note']}\n\n")
    L.append("| 谁 | 想要 | 为什么 | 靠什么找到 |\n| --- | --- | --- | --- |\n")
    for r in ap["interested"]["rows"]:
        L.append(f"| **{r['who']}** | {r['wants']} | {r['why']} | {r['can']} |\n")
    L.append("\n")
    return "".join(L)


def render_numbers(data: ChronicleData) -> str:
    """数值总表：这是剧本、角色表与 JSON 保持一致的凭据。"""
    L: list[str] = [HEADER]
    L.append("# 数值总表（自动生成）\n\n")
    L.append("本表与 `data/*.json` 完全一致。剧本与角色表中的数值均由同一份数据生成。\n\n")

    L.append("## 世界状态\n\n")
    init = data.chronicle["world_state"]["initial"]
    sc = data.chronicle["world_state"]["scale"]
    L.append("| 变量 | 初始 | 范围 | 每幕最大变化 |\n| --- | --- | --- | --- |\n")
    for v in data.chronicle["world_state"]["variables"]:
        L.append(
            f"| {v['zh']} | {init[v['id']]} | {sc['min']}–{sc['max']} | ±{sc['max_delta_per_act']} |\n"
        )
    L.append("\n")

    L.append("## 崩盘轨道\n\n")
    L.append("| 轨道 | 驱动 | 触发 | 结果 | 幸存条件 |\n| --- | --- | --- | --- | --- |\n")
    for t in data.collapse_tracks:
        L.append(
            f"| **{t['zh']}** | {t['driver']} | {json.dumps(t['trigger'], ensure_ascii=False)} | "
            f"{t['outcome']} | {t['survivors']} |\n"
        )
    L.append("\n")

    L.append("## 逃亡准备\n\n")
    e = data.escape_rules
    L.append(f"- 范围：{e['range'][0]}–{e['range'][1]}；幸存门槛：**{e['threshold_survive']}**\n")
    L.append(f"- 必须公开：{'是' if e['disclosure_required'] else '否'}——{e['disclosure_note']}\n\n")
    L.append("| 准备度 | 结果 |\n| --- | --- |\n")
    for k, v in e["resolution"].items():
        L.append(f"| {k} | {v} |\n")
    L.append("\n")

    L.append("## 血族派系\n\n")
    L.append("| 派系 | 立场 | 耐心 | 能力 | 合法 | 非法 | 超自然 |\n")
    L.append("| --- | --- | --- | --- | --- | --- | --- |\n")
    for f in data.kindred["factions"]:
        init_ = f["initial"]
        ab = f["abilities"]
        L.append(
            f"| {f['zh']} | {STANCE_ZH.get(init_['stance'], init_['stance'])} | "
            f"{init_['patience']} | {init_['capability']} | "
            f"{ab['legal']} | {ab['illegal']} | {ab['supernatural']} |\n"
        )
    L.append("\n")

    L.append("## 人类阵营\n\n")
    L.append("| 阵营 | 合法 | 非法 | 超自然 |\n| --- | --- | --- | --- |\n")
    for f in data.mortal["factions"]:
        cap = f["capability"]
        L.append(
            f"| {f['zh']} | {cap['legal']} | {cap['illegal']} | {cap['supernatural']} |\n"
        )
    L.append("\n")

    L.append("## 公式\n\n")
    L.append(f"- {data.chronicle['intensity']['formula']}\n")
    L.append(
        f"- 烈度阈值：警戒 ≥ {data.chronicle['intensity']['thresholds']['watch']}，"
        f"警报 ≥ {data.chronicle['intensity']['thresholds']['alarm']}\n"
    )
    L.append("- 玩家修正池 = 结果质量（0–3）× 2\n")
    L.append("- 目击超自然：每次 +1 暴露度（上限 +3）\n")
    L.append("- 临界区间：任一变量 ≤3 或 ≥7 → 全行动 ×1.5\n")
    return "".join(L)


# --------------------------------------------------------------------------


def render_dashboard(data: ChronicleData) -> str:
    world = data.chronicle["world_state"]["initial"]
    var_zh = {v["id"]: v["zh"] for v in data.chronicle["world_state"]["variables"]}
    state_cards = "".join(
        f'<div class="card"><small>{html.escape(var_zh[v])}</small>'
        f"<strong>{world[v]}</strong></div>"
        for v in WORLD_VARS
    )
    act_cards = []
    for group in data.groups():
        scene_ids = " / ".join(s["id"] for s in group["scenes"])
        act_cards.append(
            f'<article class="act"><h3>第 {group["act"]} 幕 · '
            f'{html.escape(group["title"])}</h3>'
            f'<p>{html.escape(group["summary"])}</p>'
            f'<small>{html.escape(scene_ids)}</small></article>'
        )
    kindred_rows = "".join(
        f"<tr><td>{html.escape(f['zh'])}</td>"
        f"<td>{html.escape(f['axis_age'])}</td>"
        f"<td>{html.escape(f['axis_sect'])}</td>"
        f"<td>{html.escape(f['one_line'])}</td></tr>"
        for f in data.kindred["factions"]
    )
    mortal_rows = "".join(
        f"<tr><td>{html.escape(f['zh'])}</td>"
        f"<td>{html.escape(f['position'])}</td></tr>"
        for f in data.mortal["factions"]
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<title>《不在册者》· 局势看板</title>
<style>
:root {{ color-scheme: dark; font-family: Georgia, "Noto Serif SC", serif; }}
body {{ margin:0; background:#171414; color:#e8dfd2; }}
header {{ padding:36px max(5vw,24px); background:linear-gradient(120deg,#2d1919,#191414); }}
h1 {{ margin:0 0 8px; font-size:36px; }}
main {{ max-width:1180px; margin:auto; padding:28px 20px 60px; }}
.state, .acts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }}
.card, .act {{ background:#221d1d; border:1px solid #463333; border-radius:12px; padding:16px; }}
.card strong {{ display:block; font-size:30px; color:#ffd28f; }}
.act h3 {{ margin:0 0 8px; color:#ffd28f; }}
table {{ width:100%; border-collapse:collapse; margin:18px 0 34px; }}
th, td {{ text-align:left; padding:9px; border-bottom:1px solid #463333; vertical-align:top; }}
th {{ color:#ffd28f; }}
code {{ background:#2d2727; padding:2px 6px; border-radius:5px; }}
</style>
<header>
  <h1>《不在册者》</h1>
  <p>2040 · 新加坡 · VTM V5 现代之夜</p>
  <p><code>python -m the_unlisted.cli run --profile normal --seed 5</code>　
     <code>python -m the_unlisted.cli gui</code></p>
</header>
<main>
  <h2>世界状态</h2><section class="state">{state_cards}</section>
  <h2>六幕</h2><section class="acts">{''.join(act_cards)}</section>
  <h2>人类三方</h2>
  <table><tr><th>阵营</th><th>立场</th></tr>{mortal_rows}</table>
  <h2>血族五方</h2>
  <table><tr><th>派系</th><th>年龄轴</th><th>派系轴</th><th>一句话</th></tr>{kindred_rows}</table>
</main>
</html>
"""


def render_roster(data: ChronicleData) -> str:
    parts: list[str] = [HEADER, "# 名册总表\n\n"]
    parts.append(
        "> 本文件由 `python -m the_unlisted.cli render` 生成，"
        "把派系、人物、道具、反制、名词与数值集中在一处。\n\n"
    )
    sections = [
        ("名词与完整派系", render_glossary),
        ("血族派系与人物", render_kindred),
        ("人类派系与人物", render_mortal),
        ("托管档案", render_props),
        ("人类反制速查", render_consequences),
        ("附录与场所", render_appendix),
        ("数值总表", render_numbers),
    ]
    for i, (label, fn) in enumerate(sections):
        body = fn(data).removeprefix(HEADER).lstrip()
        parts.append(f"\n---\n\n<!-- {label} -->\n\n{body}")
        if not body.endswith("\n"):
            parts.append("\n")
    return "".join(parts)


def render_all(data_dir: Path | str | None = None) -> list[Path]:
    data = ChronicleData.load(data_dir) if data_dir else ChronicleData.load()
    written: list[Path] = []
    for group in data.groups():
        act_no = group["act"]
        scenes = sorted(group["scenes"], key=lambda s: s.get("scene_no", 1))
        if len(scenes) == 1:
            s = scenes[0]
            parts = [HEADER]
            parts.append(f"# 第 {act_no} 幕 · {group['title']}\n\n")
            parts.append(f"> {group['summary']}\n\n")
            parts.append(f"**场景编号**：{scene_label(s)}\n\n")
            parts.append(f"**阶段**：{s['phase']}　**时间**：{s['time']}\n\n")
            parts.append("---\n\n## 一、场景描写\n\n")
            parts.append("*可直接朗读。段落之间留白，不要一口气念完。*\n\n")
            for para in s.get("scene", []):
                parts.append(f"{para}\n\n")
            body = render_act(data, s, include_header=False, include_scene=False)
            parts.append(body)
            content = "".join(parts)
        else:
            # 一、场景描写：全部提到最前，每一场单独写
            parts = [HEADER]
            parts.append(
                f"# 第 {act_no} 幕 · {group['title']}\n\n"
            )
            parts.append(f"> {group['summary']}\n\n")
            parts.append(
                f"**阶段**：{scenes[0]['phase']}　**时间**：{scenes[0]['time']}"
                f"　→　{scenes[-1]['time']}　**共 {len(scenes)} 场**\n\n"
            )
            parts.append("---\n\n## 一、场景描写\n\n")
            parts.append("*可直接朗读。每一场单独念，场与场之间不要一口气连上。*\n\n")
            for i, s in enumerate(scenes, 1):
                parts.append(
                    f"### 场景 {scene_label(s)} · {s['title']}（{s['time']}）\n\n"
                )
                for para in s.get("scene", []):
                    parts.append(f"{para}\n\n")
            # 其余小节：逐场，但去掉各自的结算
            for i, s in enumerate(scenes, 1):
                parts.append(
                    f"---\n\n# 场景 {scene_label(s)} · {s['title']}\n\n"
                )
                body = render_act(data, s, include_header=False, include_scene=False)
                for zh in ("一", "二", "三", "四", "五", "六"):
                    body = body.replace(f"## {zh}、", "## ")
                if i < len(scenes):
                    cut = body.find("## 数值影响")
                    if cut > 0:
                        body = body[:cut]
                parts.append(body)
            parts.append(
                "*本幕的局势在最后才结算一次——**不要在任何一场之后结算。***\n\n"
            )
            content = "".join(parts)
        # 各级小标题一律不带序号——避免"暴力"缺席时出现跳号
        for zh in ("一", "二", "三", "四", "五", "六", "七"):
            content = content.replace(f"## {zh}、", "## ")
        written.append(_w(DOCS / "acts" / f"act-{act_no:02d}.md", content))
    written.append(_w(DOCS / "roster.md", render_roster(data)))
    written.append(_w(DOCS / "dashboard.html", render_dashboard(data)))
    return written


def main() -> None:
    data = ChronicleData.load()
    missing = data.unknown_ids()
    if missing:
        print("警告：以下人物 id 无法解析——")
        for where, cid in missing:
            print(f"  {where} -> {cid}")
    written = render_all()
    for p in written:
        print(f"已生成 {p.relative_to(PACKAGE_ROOT)}")


if __name__ == "__main__":
    main()
