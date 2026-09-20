"""命令行接口。

用法示例：

  python -m the_unlisted.cli check
  python -m the_unlisted.cli act 3
  python -m the_unlisted.cli scene 3.1
  python -m the_unlisted.cli advance --scene 3.1 --quality 3 --alloc legitimacy=2,exposure=2 --witnessed 1
  python -m the_unlisted.cli run --quality 2 --seed 7
  python -m the_unlisted.cli render
  python -m the_unlisted.cli verify
  python -m the_unlisted.cli gui
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    # 支持直接运行 `python src/the_unlisted/cli.py ...`。
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "the_unlisted"

from .data import WORLD_VARS, ChronicleData, scene_label
from .engine import Chronicle, PlayerMods
from .render import render_all

VAR_ZH = {
    "order": "秩序",
    "legitimacy": "正当性",
    "feeding": "猎食条件",
    "exposure": "暴露度",
    "capital": "资本信心",
}


PROFILES: dict[str, dict[str, Any]] = {
    "careful": {
        "quality": 3, "agitation": 0, "witnessed": 0, "escape": 1,
        "prefer": ("order", "legitimacy", "capital"),
        "zh": "谨慎：只做人类能做的事，把资源投向秩序与正当性",
    },
    "normal": {
        "quality": 2, "agitation": 0, "witnessed": 0, "escape": 0,
        "prefer": ("order", "legitimacy", "capital", "feeding"),
        "zh": "正常：偶尔用一次律能，两边都不得罪",
    },
    "sloppy": {
        "quality": 1, "agitation": 1, "witnessed": 1, "escape": 0,
        "prefer": ("order", "legitimacy"),
        "zh": "冒失：每次都靠律能解决问题，被人看见过",
    },
    "reckless": {
        "quality": 1, "agitation": 2, "witnessed": 2, "escape": 0,
        "prefer": ("order",),
        "zh": "整烂活：在人群里动手，把两边的火都点着",
    },
}


def _fmt_world(w: dict[str, int]) -> str:
    return "  ".join(f"{VAR_ZH[v]} {w[v]}" for v in WORLD_VARS)


def _parse_alloc(text: str | None) -> dict[str, int]:
    if not text:
        return {}
    out: dict[str, int] = {}
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        key, _, val = part.partition("=")
        key = key.strip()
        if key not in WORLD_VARS:
            raise SystemExit(f"未知变量：{key}（可用：{', '.join(WORLD_VARS)}）")
        out[key] = int(val)
    return out


# --------------------------------------------------------------------------


def cmd_check(args: argparse.Namespace) -> int:
    data = ChronicleData.load()
    missing = data.unknown_ids()
    print(f"幕数：{len(data.groups())}　场数：{len(data.acts())}")
    print(f"血族派系：{len(data.kindred['factions'])}")
    print(f"血族人物：{len(data.kindred_chars)}")
    print(f"人类阵营：{len(data.mortal['factions'])}")
    print(f"人类人物（含替补）：{len(data.mortal_chars)}")
    subs = sum(1 for c in data.mortal_chars.values() if c.get("_substitute"))
    print(f"其中替补：{subs}")
    if missing:
        print("\n无法解析的人物 id：")
        for where, cid in missing:
            print(f"  {where} -> {cid}")
        return 1
    print("\n所有人物 id 均可解析。")
    return 0


def cmd_act(args: argparse.Namespace) -> int:
    data = ChronicleData.load()
    group = data.group(args.act)
    print(f"第 {group['act']} 幕 · {group['title']}")
    print(f"\n{group['summary']}\n")
    print("场景：")
    for scene in group["scenes"]:
        print(f"  {scene_label(scene)} · {scene['title']} · {scene['time']}")
        print(f"    {scene['premise']}\n")
    return 0


def cmd_scene(args: argparse.Namespace) -> int:
    data = ChronicleData.load()
    act = data.act(args.scene)
    print(
        f"【{scene_label(act)}】{act['title']}　{act['phase']}　{act['time']}"
    )
    print(f"\n前提：{act['premise']}")
    print(f"\n钩子：{act['hook']}")
    print(f"\n默认结果：{act['default_outcome']}")
    print("\n固有脉冲：" + "  ".join(
        f"{VAR_ZH[v]} {act['inherent_pulse'].get(v, 0):+d}" for v in WORLD_VARS
    ))
    print("\n脱出条件：")
    for i, c in enumerate(act["exit_conditions"], 1):
        print(f"  {i}. {c}")
    print("\n人类立场（常量）：")
    for fid, s in data.mortal_phase_stance(act["id"]).items():
        print(f"  {data.mortal_factions[fid]['zh']}：{s}")
    print("\n极乐境密室：")
    for room in act["elysium"]["rooms"]:
        meta = data.rooms[room["room"]]
        fac = data.kindred_factions[room["faction"]]["zh"]
        present = "、".join(data.name_of(c) for c in room["present"]) or "（空）"
        print(f"  {meta['zh']}｜{fac}｜门={room.get('door')}｜{present}")
        for e in room.get("absent", []):
            print(f"      缺席：{data.name_of(e['id'])}——{e.get('why', '')}")
        for e in room.get("added", []):
            print(f"      新出现：{data.name_of(e['id'])}——{e.get('why', '')}")
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    data = ChronicleData.load()
    ch = Chronicle(data)
    scenes = data.acts()
    try:
        target_scene = data.act(args.scene)
    except (KeyError, IndexError):
        raise SystemExit(f"未知场景：{args.scene}") from None
    target = scenes.index(target_scene)
    for i in range(target):
        ch.act_cursor = i
        ch.advance(PlayerMods())
    ch.act_cursor = target
    mods = PlayerMods(
        outcome_quality=args.quality,
        allocations=_parse_alloc(args.alloc),
        witnessed_supernatural=args.witnessed,
        escape_delta=args.escape,
        agitation=args.agitation,
    )
    res = ch.advance(mods)
    _print_result(ch, res)
    return 0


def _print_result(ch: Chronicle, res: Any) -> None:
    print(f"══ {res.act_id} · {res.title}（{res.phase}）══\n")
    print("【血族行动】")
    print(f"  {'派系':<10}{'立场':<8}{'耐心':>4}{'L':>3}{'能力':>5}{'类型':>6}{'效果E':>8}")
    for a in res.actions:
        print(
            f"  {a.zh:<10}{a.stance:<8}{a.patience:>4}{a.coefficient:>3}"
            f"{a.capability:>5}{a.action_type:>6}{a.effect:>8}"
        )
        if a.levers:
            print(f"      杠杆：{'；'.join(a.levers)}")
    print(f"\n  烈度 = {res.intensity}（{res.intensity_band}）")

    print("\n【人类】立场与行动效果（谁会定议程）")
    for m in sorted(res.mortal_effects, key=lambda x: -x.effect):
        lever = f"　杠杆：{'；'.join(m.levers)}" if m.levers else ""
        print(
            f"  {m.zh:<8}{m.stance:<8}烈度{m.severity}　能力{m.capability_score:<5}"
            f"效果 {m.effect:<7}{lever}"
        )
    ag = ch.agenda_holder()
    print(f"  → 在议程上的是：{ag['zh']}（效果 {ag['effect']}）")

    print("\n【世界状态结算】")
    print(f"  {'变量':<8}{'起始':>5}{'脉冲':>6}{'行动':>8}{'玩家':>6}{'终值':>6}")
    for v in WORLD_VARS:
        print(
            f"  {VAR_ZH[v]:<8}{res.world_before[v]:>5}{res.inherent_pulse.get(v, 0):>6}"
            f"{res.action_delta[v]:>8.1f}{res.player_delta[v]:>6}{res.world_after[v]:>6}"
        )
    if res.clamps_applied:
        print("  上限保护：" + "；".join(res.clamps_applied))

    if res.kindred_changes:
        print("\n【血族状态变化】")
        for fid, before in res.kindred_before.items():
            after = res.kindred_after[fid]
            print(
                f"  {before['zh']:<8} 立场 {before['stance']}→{after['stance']}　"
                f"耐心 {before['patience']}→{after['patience']}　"
                f"能力 {before['capability']}→{after['capability']}"
            )
        print("\n【变化原因】")
        for line in res.kindred_changes:
            print(f"  · {line}")

    print("\n【崩盘检查】")
    tracks = ch.data.collapse_tracks
    for t in tracks:
        print(f"  {t['zh']}：{t['driver']}")
    if res.collapse:
        print(f"\n  >>> 触发：{res.collapse['zh']}")
        print(f"  >>> {res.collapse['narrative']}")
        print(f"  >>> 结果：{res.collapse['outcome']}；幸存条件：{res.collapse['survivors']}")
        print(f"  >>> {res.collapse['why_players_should_fear']}")
        print(f"\n  >>> 逃亡准备 = {ch.escape_prep} → {ch.escape_outcome()}")
    else:
        print("\n  未触发。")
    if res.notes:
        print("\n【提示】")
        for n in res.notes:
            print(f"  · {n}")

    _print_finale(ch, projection=True)


def _print_finale(ch: Chronicle, projection: bool = False) -> None:
    """把「谁在议程上／谁是替罪羊／事件如何被定性」打到主持人控制台。"""
    r = ch.finale_resolution()
    title = "【终局推演 · 若此刻收束】" if projection else "【终局判定】"
    print(f"\n{title}")
    print("  人类各派力量对比（能力 × 立场烈度 × 世界状态杠杆）：")
    for row in r["agenda"]["table"]:
        print(
            f"    {row['zh']:<8}立场 {row['stance']:<8}合法能力 {row['legal']:<3}"
            f"效果 {row['effect']:<7}"
            + ("  ← 在议程上" if row["zh"] == r["agenda"]["zh"] else "")
        )
    sc = r["scapegoat"]
    inst = r["institutional"]
    print(f"\n  在议程上的阵营：{r['agenda']['zh']}（效果 {r['agenda']['effect']}）")
    print(f"  制度侧提名（{inst['nominated_by']}）：{inst['who']}｜{inst['means']}")
    print(f"    那句话：「{inst['line']}」")
    if r["street_override"]:
        print(
            f"  ※ 街头否决生效：旧自由邦能力 {r['street_capability']}"
            f" ≥ 制度侧赢家合法能力 {r['agenda']['legal']}。"
        )
        print(f"  最终写进《事件说明》第一条的人：{sc['who']}｜{sc['means']}")
        print(f"    那句话：「{sc['line']}」")
    else:
        print(f"  最终写进《事件说明》第一条的人：{sc['who']}｜{sc['means']}")
    print(f"  事件如何被定性：{r['characterization']['zh']}——{r['characterization']['text']}")
    print(f"  附则十九由谁处理：{r['annex']['who']}（{r['annex']['how']}）")
    print(f"  联合开发区条款：{r['zone']['result']}")
    print(f"  逃亡准备：{r['escape']['value']}/3 → {r['escape']['text']}")
    if r["collapse"]:
        print(f"  >>> 崩盘轨道：{r['collapse']['zh']}——{r['collapse']['outcome']}")


def cmd_run(args: argparse.Namespace) -> int:
    data = ChronicleData.load()
    ch = Chronicle(data)
    for cursor, act in enumerate(data.acts()):
        ch.act_cursor = cursor
        prof = PROFILES[args.profile]
        quality = prof["quality"] if args.quality is None else args.quality
        alloc: dict[str, int] = {}
        pool = quality * 2
        choices = [v for v in prof["prefer"] if v in WORLD_VARS] or ["order"]
        for i in range(pool):
            var = choices[i % len(choices)]
            alloc[var] = alloc.get(var, 0) + 1
        mods = PlayerMods(
            outcome_quality=quality,
            allocations=alloc,
            witnessed_supernatural=prof["witnessed"],
            escape_delta=prof["escape"],
            agitation=prof["agitation"] if args.agitation is None else args.agitation,
        )
        res = ch.advance(mods)
        _print_result(ch, res)
        if res.collapse:
            print("\n>>> 编年史在此结束。")
            break
        print("\n" + "─" * 60 + "\n")
    print("\n【最终局势】")
    print("  " + _fmt_world(ch.world))
    print(f"  逃亡准备：{ch.escape_prep}")
    print("  " + json.dumps(ch.snapshot()["kindred"], ensure_ascii=False, indent=2))
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    data = ChronicleData.load()
    missing = data.unknown_ids()
    if missing:
        print("警告：以下人物 id 无法解析——")
        for where, cid in missing:
            print(f"  {where} -> {cid}")
    for p in render_all():
        print(f"已生成 {p}")
    return 0


def _simulate_profile(profile: str, seed: int = 5) -> tuple[Chronicle, Any]:
    data = ChronicleData.load()
    ch = Chronicle(data)
    prof = PROFILES[profile]
    for cursor, _act in enumerate(data.acts()):
        ch.act_cursor = cursor
        quality = prof["quality"]
        pool = quality * 2
        choices = [v for v in prof["prefer"] if v in WORLD_VARS] or ["order"]
        alloc: dict[str, int] = {}
        for i in range(pool):
            var = choices[i % len(choices)]
            alloc[var] = alloc.get(var, 0) + 1
        res = ch.advance(
            PlayerMods(
                outcome_quality=quality,
                allocations=alloc,
                witnessed_supernatural=prof["witnessed"],
                escape_delta=prof["escape"],
                agitation=prof["agitation"],
            )
        )
        if res.collapse:
            return ch, res
    return ch, res


def cmd_verify(args: argparse.Namespace) -> int:
    """回归验证：谨慎/普通存活，冒失/整烂活触发审判庭。"""
    expected = {
        "careful": None,
        "normal": None,
        "sloppy": "inquisition",
        "reckless": "inquisition",
    }
    ok = True
    print("档案        结果        预期")
    print("----------  ----------  ----------")
    for profile, expected_track in expected.items():
        _ch, last = _simulate_profile(profile, seed=args.seed)
        actual = last.collapse.get("id") if last.collapse else None
        passed = actual == expected_track
        ok = ok and passed
        print(
            f"{profile:<10}  {str(actual or 'survive'):<10}  "
            f"{str(expected_track or 'survive'):<10}  "
            f"{'PASS' if passed else 'FAIL'}"
        )
    return 0 if ok else 1


def cmd_gui(args: argparse.Namespace) -> int:
    try:
        from .gui import main as run_gui
    except ImportError as exc:  # pragma: no cover - 环境问题
        print(f"无法载入图形界面：{exc}")
        print("请确认当前 Python 带有 tkinter（conda / 官方安装版通常自带）。")
        return 1
    try:
        run_gui()
    except Exception as exc:  # tkinter.TclError 等
        print(f"无法启动图形界面：{exc}")
        print(
            "当前 Python 缺少可用的 Tcl/Tk。可以改用命令行推演：\n"
            "  python -m the_unlisted.cli advance --scene 3.1 --quality 2\n"
            "  python -m the_unlisted.cli finale"
        )
        return 1
    return 0


def cmd_finale(args: argparse.Namespace) -> int:
    """只输出终局判定：谁在议程上、谁是替罪羊、事件如何被定性。"""
    data = ChronicleData.load()
    ch = Chronicle(data)
    mods = _profile_player_mods(args.profile) if args.profile else PlayerMods()
    if args.scene:
        try:
            target = data.acts().index(data.act(args.scene))
        except (KeyError, IndexError):
            raise SystemExit(f"未知场景：{args.scene}") from None
        for i in range(target):
            ch.act_cursor = i
            res = ch.advance(mods)
            if res.collapse:
                break
    else:
        for i in range(len(data.acts())):
            ch.act_cursor = i
            res = ch.advance(mods)
            if res.collapse:
                break
    print(f"当前局势：{_fmt_world(ch.world)}")
    _print_finale(ch)
    return 0


def _profile_player_mods(profile: str) -> PlayerMods:
    """把预设玩家画像换算成一次循环的修正池。"""
    prof = PROFILES[profile]
    quality = prof["quality"]
    choices = [v for v in prof["prefer"] if v in WORLD_VARS] or ["order"]
    alloc: dict[str, int] = {}
    for i in range(quality * 2):
        var = choices[i % len(choices)]
        alloc[var] = alloc.get(var, 0) + 1
    return PlayerMods(
        outcome_quality=quality,
        allocations=alloc,
        witnessed_supernatural=prof["witnessed"],
        escape_delta=prof["escape"],
        agitation=prof["agitation"],
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="the_unlisted", description="《不在册者》局势引擎")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("check", help="检查数据完整性")
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("act", help="显示某一幕的总览（1–6）")
    sp.add_argument("act", type=int)
    sp.set_defaults(func=cmd_act)

    sp = sub.add_parser("scene", help="显示某个场景的完整资料")
    sp.add_argument("scene", type=str)
    sp.set_defaults(func=cmd_scene)

    sp = sub.add_parser("advance", help="推进到某个场景并结算一次循环")
    sp.add_argument("--scene", type=str, required=True)
    sp.add_argument("--quality", type=int, default=0, help="玩家结果质量 0–3")
    sp.add_argument("--alloc", type=str, default="", help="如 legitimacy=2,exposure=1")
    sp.add_argument("--witnessed", type=int, default=0, help="超自然能力被目击次数")
    sp.add_argument("--escape", type=int, default=0, help="本幕提升的逃亡准备")
    sp.add_argument("--agitation", type=int, default=0, help="本幕玩家制造的混乱 0–3（秩序−n，暴露度+n）")
    sp.set_defaults(func=cmd_advance)

    sp = sub.add_parser("run", help="跑完整个剧本")
    sp.add_argument("--quality", type=int, default=None)
    sp.add_argument("--seed", type=int, default=0)
    sp.add_argument("--agitation", type=int, default=None)
    sp.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="normal",
        help="玩家画像：careful / normal / sloppy / reckless",
    )
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("render", help="从 data/ 生成 docs/")
    sp.set_defaults(func=cmd_render)

    sp = sub.add_parser("verify", help="运行四种玩家档案做回归验证")
    sp.add_argument("--seed", type=int, default=5)
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("gui", help="打开本地图形化推演界面")
    sp.set_defaults(func=cmd_gui)

    sp = sub.add_parser("finale", help="输出终局判定（替罪羊、事件定性）")
    sp.add_argument(
        "--scene",
        type=str,
        default="",
        help="只推进到该场景为止再判定；省略则跑完全剧",
    )
    sp.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="",
        help="用预设玩家画像预演（省略则不做任何玩家修正）",
    )
    sp.set_defaults(func=cmd_finale)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
