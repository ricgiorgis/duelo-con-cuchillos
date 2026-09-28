#!/usr/bin/env python3
# DUEL_VERSION 1
"""duel.py - bookkeeping for the knife duel (duelo a muerte con cuchillos).
Standard library only. State lives in .duel/<run>/state.json; .duel/LATEST points at the run.

  python3 duel.py init --task task.md [--baseline old.md] [--models haiku,sonnet,opus] [--seed N]
  python3 duel.py next      # writes the briefs for the current phase and prints the jobs to launch
  python3 duel.py tally     # after the judges: scores, winner, result.md
  python3 duel.py status
"""
import argparse, json, random, re, sys, time
from pathlib import Path

ROOT = Path(".duel")
LENSES = {
    "P": ("Practical",
          "Solve it the way someone with the asker's real resources, time and skills would execute it tomorrow. "
          "Prefer the simplest option that fully works, name concrete next steps, costs and effort, and drop "
          "anything that is clever but will not get adopted."),
    "T": ("Technical",
          "Aim for the most correct and robust solution: sound architecture or method, edge cases, failure modes, "
          "how it scales or holds up over time. Depth is welcome, but it must still fit the task's stated constraints."),
    "S": ("Skeptic",
          "Trust nothing you cannot back. Check every claim against the dossier, surface the risks and the ways the "
          "obvious answer goes wrong, and build the answer that still holds in the worst realistic case. Say plainly "
          "what is unknown."),
}
WEIGHTS = {"practical": 30, "evidence": 25, "correctness": 20, "completeness": 15, "clarity": 10}
MAX_TRIES = {"research": 2, "duel": 2, "attack": 2, "revise": 2, "judge": 3}
PHASES = ["research", "duel", "attack", "revise", "judge", "tally"]

SHARED = """=== THE TASK (identical for every participant) ===
{task}
=== END OF THE TASK ===
"""

T_RESEARCH = SHARED + """
ROLE: researcher. You do not solve the task. You build the evidence dossier that nine competitors will work from, so that nobody has to make facts up.

1. List the factual questions the answer depends on: current facts, prices, versions, rules, numbers, how things work in this specific context, what the files named in the task actually contain. Skip stable common knowledge.
2. Answer each one with web search or by reading the files the task names. Prefer primary sources and note each source's date.
3. Write {out} with these sections:
## Facts
- claim | source (URL or file path) | date | confidence high/med/low
## Conflicts
- where sources disagree, and how
## Not found
- what you looked for and could not confirm
## Context
- constraints from the task that any answer must respect
Keep it under about 1500 words. No recommendation and no solution.
4. If the task needs no outside facts, say so in one line under Facts and list the key facts stated in the task itself.
Create or edit no file except {out}.

When the file is written, reply with one line and nothing else: DOSSIER <number of facts>
"""

T_DUEL = SHARED + """
Evidence dossier for this task (same for all nine competitors): {dossier}

ROLE: competitor {id}, one of nine. Everyone has the same task and dossier. What makes you different is your lens. Two rivals will attack your answer, you will get one chance to revise it, and then three blind judges score all answers.

LENS: {lens_name}. {lens_how}

Rules:
- Evidence. Every factual claim comes from the dossier, the task, or a check you run yourself (at most 3 web searches). Mark anything else [ASSUMPTION]. An invented fact that is not marked is the fastest way to lose.
- Useful beats sophisticated. The judges put practical usefulness for the person who asked above technical elegance. Respect every constraint the task states: resources, time, audience, format, language.
- Where the task is ambiguous, take the most reasonable reading and state it in one short Assumptions line.
- If the task is about code or files, put the exact changes in your answer (full files or a diff). Do not apply them.
- Write for the person who asked, in the task's language. Say nothing about the duel, your lens or your id.
- Create or edit nothing outside {run_dir}.

Write your answer to {out}. As long as it needs to be and no longer.
When the file is written, reply with one line and nothing else: DONE {id} <word count>
"""

T_ATTACK = SHARED + """
Evidence dossier: {dossier}

ROLE: competitor {id}, lens {lens_name}. Attack the two rival answers in your group:
- {t1}: {p1}
- {t2}: {p2}
Your own answer, for reference only: {own}. Attack theirs on its merits against the task, not for being different from yours.

Look through your lens ({lens_name}: {lens_how}) for:
- WRONG: factual or logic errors, bugs, false claims.
- UNSUPPORTED: a factual claim that is not in the dossier or the task and is not marked [ASSUMPTION]. Check the dossier before you call it.
- IMPRACTICAL: the person could not realistically execute it with their stated resources and constraints, or a simpler option gets the same result.
- MISSING: a requirement the task states that it skips. Quote the requirement.
- BREAKS: a concrete scenario or input where it fails.

At most 5 attacks per rival, strongest first, each specific and checkable, labelled FATAL, MAJOR or MINOR. No praise, no summary, no style nitpicks, no requirements the task never stated. Fewer real attacks beat padding.

Write to {out} in exactly this format:
=== TARGET {t1} ===
ATTACK 1 [MAJOR] [UNSUPPORTED] <one-line title>
Where: <quote or location>
Problem: <what is wrong and why, with the counterexample>
=== TARGET {t2} ===
ATTACK 1 [...]
Create or edit no file except {out}.
When the file is written, reply with one line and nothing else: ATTACKED {id} <attacks on {t1}>/<attacks on {t2}>
"""

T_REVISE = SHARED + """
Evidence dossier: {dossier}

ROLE: competitor {id}, lens {lens_name}. Keep your lens: {lens_how}
Your answer: {own}
The attacks your two rivals made on it: {attacks_in}

1. Take each attack in turn. CONCEDE if it is right, and fix it. REBUT if it is wrong, with evidence: a dossier line, a quote from the task, or a concrete check. Insisting is not rebutting; an unsupported rebuttal counts as a concession.
2. Write your complete revised answer, standalone, with every conceded point fixed and anything the attacks made you notice. Do not start over and do not copy a rival. The same evidence rule applies: facts from the dossier, the task or your own check, everything else marked [ASSUMPTION].
3. If the attacks file is empty or says NO OUTPUT, write NO ATTACKS RECEIVED as your defense and resubmit with only the fixes you know it needs.
Say nothing about the duel, your lens or your id in the answer. Create or edit nothing outside {run_dir}.

Write your defense to {defense_out}, one line per attack: ATTACK <n> from <rival>: CONCEDE|REBUT. <one to three lines>
Write your revised answer to {out}.
When both files are written, reply with one line and nothing else: REVISED {id} conceded <n> rebutted <n>
"""

T_JUDGE = SHARED + """
Evidence dossier: {dossier}

ROLE: one of three independent judges. Below are {k} anonymous answers to the task above, labelled {letters}. You are not told who or what wrote them and you must not guess.

{answer_list}

How to judge:
1. Read every answer in full before you score any of them.
2. Check the factual claims that matter against the dossier. Claims that are not in the dossier or the task and are not marked as assumptions cut the evidence score. A wrong claim that changes the recommendation is fatal.
3. Score each criterion from 0 to 10:
   practical (30%): could the person who asked act on it with the resources and constraints the task states, and is it the most useful option rather than the most sophisticated one?
   evidence (25%): claims backed by the dossier or the task, or clearly flagged as assumptions.
   correctness (20%): free of factual, logical and technical errors.
   completeness (15%): meets every requirement the task states.
   clarity (10%): the person could follow it without guessing.
   Anchors: 10 nothing to improve, 7 solid with minor gaps, 5 usable with real gaps, 3 serious problems, 0 missing or unusable.
4. fatal is true only for a flaw you verified that makes the answer wrong or unusable for the task.
5. Length is not quality. Judge the work, not the confidence of the writing.
Create or edit no file except {out}.

Write only this JSON to {out}, with one entry per answer:
{{
  "scores": {{
    "A": {{"practical": 0, "evidence": 0, "correctness": 0, "completeness": 0, "clarity": 0, "fatal": false, "note": "the decisive strength or flaw, one line"}}
  }},
  "top3": ["best letter", "second", "third"],
  "reason": "one sentence on why your first place beats your second"
}}
When the file is written, reply with one line and nothing else: JUDGED {judge} top <letter> <letter> <letter>
"""


def die(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def run_dir():
    latest = ROOT / "LATEST"
    if not latest.exists():
        die("no run found. Run init first, from the same directory.")
    return Path(latest.read_text().strip())


def load(rd):
    return json.loads((rd / "state.json").read_text())


def save(rd, st):
    (rd / "state.json").write_text(json.dumps(st, indent=2))


def has_output(p):
    p = Path(p)
    return p.exists() and p.stat().st_size > 0


def build_grid(models):
    """Nine duelists, every model x every lens: d1-d3 are the first model, d4-d6 the second, d7-d9 the third.
    The groups form a Latin square, so each group of three has one duelist per model and one per lens."""
    lenses = list(LENSES)
    duelists = {f"d{mi * 3 + li + 1}": {"model": m, "lens": lk}
                for mi, m in enumerate(models) for li, lk in enumerate(lenses)}
    groups = [[f"d{mi * 3 + (mi + g) % 3 + 1}" for mi in range(3)] for g in range(3)]
    return duelists, groups


def cmd_init(args):
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if len(models) != 3:
        die("--models needs exactly three names, weakest to strongest, e.g. haiku,sonnet,opus")
    task = Path(args.task)
    if not has_output(task):
        die(f"task file missing or empty: {task}")
    if args.baseline and not has_output(args.baseline):
        die(f"baseline file missing or empty: {args.baseline}")
    seed = args.seed if args.seed is not None else random.randrange(10 ** 6)
    rd = ROOT / time.strftime("%Y%m%d-%H%M%S")
    for sub in ["solutions", "attacks", "attacks_in", "defense", "revised", "judging", "verdicts", "briefs"]:
        (rd / sub).mkdir(parents=True, exist_ok=True)
    (rd / "task.md").write_text(task.read_text())
    if args.baseline:
        (rd / "baseline.md").write_text(Path(args.baseline).read_text())
    duelists, groups = build_grid(models)
    st = {"seed": seed, "models": models, "duelists": duelists, "groups": groups,
          "baseline": bool(args.baseline), "tries": {}, "mapping": None, "done": False}
    save(rd, st)
    (ROOT / "LATEST").write_text(str(rd.resolve()))
    print(f"RUN {rd.resolve()}  seed {seed}")
    print(f"models (weak->strong): {', '.join(models)} | research: {models[1]} | judges: {', '.join(models)}")
    for i, g in enumerate(groups, 1):
        print(f"group {i}: " + ", ".join(f"{d}={duelists[d]['model']}/{LENSES[duelists[d]['lens']][0]}" for d in g))
    print("calls: 1 research + 9 answers + 9 attacks + 9 revisions + 3 judges = 31")
    print("Next: python3 duel.py next")


def rivals(st, d):
    group = next(g for g in st["groups"] if d in g)
    return [x for x in group if x != d]


def split_attacks(rd, st):
    """Cut every attacker's file into per-target sections, so a defender reads only what hit it."""
    received = {d: [] for d in st["duelists"]}
    for attacker in st["duelists"]:
        p = rd / "attacks" / f"{attacker}.md"
        text = p.read_text() if p.exists() else "NO OUTPUT"
        parts = re.split(r"^===\s*TARGET\s+(d\d+)\s*===\s*$", text, flags=re.M)
        sections = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
        for target in rivals(st, attacker):
            body = sections.get(target)
            if body is None:
                body = "NO OUTPUT" if text.strip() == "NO OUTPUT" else \
                    "(attacker's file had no clean section for you; full file follows)\n" + text
            received[target].append(f"### Attacks from {attacker}\n{body}")
    for d, chunks in received.items():
        (rd / "attacks_in" / f"{d}.md").write_text("\n\n".join(chunks) + "\n")


def anonymize(rd, st):
    """Shuffle the revised answers (and the baseline) into judging/A.md, B.md, ... and record who is who."""
    entries = list(st["duelists"]) + (["baseline"] if st["baseline"] else [])
    random.Random(st["seed"]).shuffle(entries)
    mapping = {}
    for i, entry in enumerate(entries):
        letter = chr(ord("A") + i)
        if entry == "baseline":
            src = rd / "baseline.md"
        else:
            src = rd / "revised" / f"{entry}.md"
            if not has_output(src) or src.read_text().strip() == "NO OUTPUT":
                src = rd / "solutions" / f"{entry}.md"
        (rd / "judging" / f"{letter}.md").write_text(src.read_text() if src.exists() else "NO OUTPUT")
        mapping[letter] = entry
    st["mapping"] = mapping
    save(rd, st)


def expected_outputs(rd, st, phase):
    """The one place that says which files each job of a phase must write. Judges given up on are left out."""
    ds = list(st["duelists"])
    if phase == "research":
        return {"research": [rd / "dossier.md"]}
    if phase == "duel":
        return {d: [rd / "solutions" / f"{d}.md"] for d in ds}
    if phase == "attack":
        return {d: [rd / "attacks" / f"{d}.md"] for d in ds}
    if phase == "revise":
        return {d: [rd / "revised" / f"{d}.md", rd / "defense" / f"{d}.md"] for d in ds}
    if phase == "judge":
        skip = rd / "verdicts" / ".skip"
        skipped = skip.read_text().split(",") if skip.exists() else []
        return {f"judge-{m}": [rd / "verdicts" / f"judge-{m}.json"] for m in st["models"]
                if f"judge-{m}" not in skipped}
    return {}


def brief_text(rd, st, phase, jid, outs):
    """Fill the phase's template for one job."""
    common = {"task": (rd / "task.md").read_text(), "dossier": (rd / "dossier.md").resolve(),
              "run_dir": rd.resolve(), "out": outs[0].resolve()}
    if phase == "research":
        return T_RESEARCH.format(**common)
    if phase == "judge":
        letters = sorted(st["mapping"])
        answer_list = "\n".join(f"Answer {L}: {(rd / 'judging' / f'{L}.md').resolve()}" for L in letters)
        return T_JUDGE.format(k=len(letters), letters=", ".join(letters), answer_list=answer_list,
                              judge=jid[len("judge-"):], **common)
    lens_name, lens_how = LENSES[st["duelists"][jid]["lens"]]
    duelist = {"id": jid, "lens_name": lens_name, "lens_how": lens_how,
               "own": (rd / "solutions" / f"{jid}.md").resolve()}
    if phase == "duel":
        return T_DUEL.format(**duelist, **common)
    if phase == "attack":
        t1, t2 = rivals(st, jid)
        return T_ATTACK.format(t1=t1, t2=t2, p1=(rd / "solutions" / f"{t1}.md").resolve(),
                               p2=(rd / "solutions" / f"{t2}.md").resolve(), **duelist, **common)
    return T_REVISE.format(attacks_in=(rd / "attacks_in" / f"{jid}.md").resolve(),
                           defense_out=outs[1].resolve(), **duelist, **common)


def job_model(st, phase, jid):
    if phase == "research":
        return st["models"][1]
    if phase == "judge":
        return jid[len("judge-"):]
    return st["duelists"][jid]["model"]


def pending(rd, st, phase):
    return {jid: outs for jid, outs in expected_outputs(rd, st, phase).items()
            if not all(has_output(o) for o in outs)}


def current_phase(rd, st):
    if st.get("done"):
        return "done"
    return next((p for p in PHASES[:-1] if pending(rd, st, p)), "tally")


def cmd_next(args):
    rd = run_dir()
    st = load(rd)
    phase = current_phase(rd, st)
    if phase == "done":
        print(f"DONE. Read {(rd / 'result.md').resolve()} and the winning answer it names.")
        return
    if phase == "tally":
        print("PHASE tally: all judges are in. Run: python3 duel.py tally")
        return
    if phase == "revise" and not any((rd / "attacks_in").iterdir()):
        split_attacks(rd, st)
    if phase == "judge" and not st.get("mapping"):
        anonymize(rd, st)
    runnable, gave_up = [], []
    for jid, outs in pending(rd, st, phase).items():
        key = f"{phase}:{jid}"
        tries = st["tries"].get(key, 0)
        if tries >= MAX_TRIES[phase]:
            gave_up.append(jid)
            if phase != "judge":
                for o in outs:
                    if not has_output(o):
                        o.write_text("NO OUTPUT\n")
            continue
        st["tries"][key] = tries + 1
        brief = rd / "briefs" / f"{phase}-{jid}.md"
        brief.write_text(brief_text(rd, st, phase, jid, outs))
        runnable.append((jid, job_model(st, phase, jid), brief.resolve()))
    save(rd, st)
    if gave_up:
        print(f"gave up on {', '.join(gave_up)} after the retry limit (marked NO OUTPUT; judges that fail are skipped).")
    if not runnable:
        if phase == "judge":
            (rd / "verdicts" / ".skip").write_text(",".join(gave_up))
            print("Run: python3 duel.py tally")
            return
        return cmd_next(args)
    print(f"PHASE {phase}: launch these {len(runnable)} sub-agents in ONE message, in parallel, then run next again.")
    for jid, model, brief in runnable:
        print(f"JOB {jid} | model={model} | prompt: You are part of a structured multi-agent review. "
              f"Your whole brief is in this file; read it and follow it exactly: {brief}")


def parse_json(p):
    """Read a verdict, tolerating a code fence or stray text around the JSON object."""
    raw = Path(p).read_text()
    for candidate in (raw, (re.search(r"\{.*\}", raw, flags=re.S) or [None])[0]):
        if candidate:
            try:
                return json.loads(candidate)
            except ValueError:
                pass
    return None


def weighted_total(scores):
    t = 0.0
    for criterion, weight in WEIGHTS.items():
        try:
            v = float(scores.get(criterion, 0))
        except (TypeError, ValueError):
            v = 0.0
        t += weight * max(0.0, min(10.0, v)) / 10.0
    return round(t, 1)


def cmd_tally(args):
    rd = run_dir()
    st = load(rd)
    mapping = st.get("mapping")
    if not mapping:
        die("no judging yet. Run next.")
    letter_of = {entry: L for L, entry in mapping.items()}
    verdicts = {}
    for m in st["models"]:
        p = rd / "verdicts" / f"judge-{m}.json"
        v = parse_json(p) if has_output(p) else None
        if v and isinstance(v.get("scores"), dict):
            verdicts[m] = v
    if not verdicts:
        die("no readable verdicts. Re-run next to retry the judges.")

    rows = {}
    for L, entry in mapping.items():
        per, fatal = {}, 0
        for m, v in verdicts.items():
            s = v["scores"].get(L) or v["scores"].get(L.lower()) or {}
            per[m] = weighted_total(s)
            fatal += str(s.get("fatal", False)).lower() == "true"
        rows[L] = {"entry": entry, "per": per, "sum": round(sum(per.values()), 1), "fatal": fatal}
    firsts = {m: v["top3"][0] for m, v in verdicts.items() if v.get("top3")}
    fatal_bar = 2 if len(verdicts) >= 2 else 1
    strongest = st["models"][2]
    ranked = sorted(rows, reverse=True, key=lambda L: (
        rows[L]["fatal"] < fatal_bar,                       # a fatal answer cannot beat a non-fatal one
        rows[L]["sum"],
        sum(1 for f in firsts.values() if f == L),          # tie: more first places
        rows[L]["per"].get(strongest, 0)))                  # then the strongest judge's score
    win = ranked[0]
    winner = rows[win]["entry"]
    win_path = (rd / "baseline.md") if winner == "baseline" else (rd / "judging" / f"{win}.md")
    maxsum = 100 * len(verdicts)

    def label(entry):
        if entry == "baseline":
            return "rejected answer (baseline)"
        v = st["duelists"][entry]
        return f"{entry} {v['model']}/{LENSES[v['lens']][0]}"

    out = ["# Duel result", "",
           f"Winner: {label(winner)}, {rows[win]['sum']} of {maxsum} points.",
           f"Winning answer: {win_path.resolve()}"]
    if winner != "baseline":
        out.append(f"Its defense: {(rd / 'defense' / f'{winner}.md').resolve()}")
    out += ["", "Judges' first places: " + ", ".join(f"{m} -> {label(mapping.get(L, L))}" for m, L in firsts.items())]
    picks = list(firsts.values())
    if len(picks) == 3 and len(set(picks)) == 3:
        out.append("Split verdict: the three judges each picked a different winner. Treat the result as close.")
    elif len(picks) == 3 and len(set(picks)) == 2:
        odd = next(m for m, L in firsts.items() if picks.count(L) == 1)
        out.append(f"Dissent: the {odd} judge picked differently from the other two.")
    missing = [m for m in st["models"] if m not in verdicts]
    if missing:
        out.append(f"Missing or unreadable verdicts: {', '.join(missing)}. Result uses {len(verdicts)} judge(s).")
    out += [f"- {m} judge: {v['reason']}" for m, v in verdicts.items() if v.get("reason")]

    out += ["", "| rank | entry | " + " | ".join(verdicts) + " | total | fatal flags |",
            "|---|---|" + "---|" * len(verdicts) + "---|---|"]
    for i, L in enumerate(ranked, 1):
        r = rows[L]
        out.append(f"| {i} | {label(r['entry'])} | " + " | ".join(str(r["per"][m]) for m in verdicts)
                   + f" | {r['sum']} | {r['fatal']} |")

    def cell(model, lens):
        d = next(d for d, v in st["duelists"].items() if v["model"] == model and v["lens"] == lens)
        return rows[letter_of[d]]["sum"]

    lenses = list(LENSES)
    out += ["", f"Average total by model x lens (out of {maxsum}):",
            "| model | " + " | ".join(LENSES[k][0] for k in lenses) + " | model avg |",
            "|---|" + "---|" * (len(lenses) + 1)]
    for m in st["models"]:
        cells = [cell(m, k) for k in lenses]
        out.append(f"| {m} | " + " | ".join(str(c) for c in cells) + f" | {sum(cells) / len(cells):.1f} |")
    lens_avg = [sum(cell(m, k) for m in st["models"]) / 3 for k in lenses]
    out.append("| lens avg | " + " | ".join(f"{a:.1f}" for a in lens_avg) + " | |")
    if st["baseline"]:
        out += ["", f"The rejected answer, judged blind among the others, placed "
                    f"{ranked.index(letter_of['baseline']) + 1} of {len(ranked)}."]

    (rd / "result.md").write_text("\n".join(out) + "\n")
    st["done"] = True
    save(rd, st)
    print("\n".join(out))


def cmd_status(args):
    rd = run_dir()
    st = load(rd)
    print(f"run {rd} | phase {current_phase(rd, st)}")
    for phase in PHASES[:-1]:
        expected = expected_outputs(rd, st, phase)
        print(f"  {phase:<8} {len(expected) - len(pending(rd, st, phase))}/{len(expected)}")


def main():
    ap = argparse.ArgumentParser(description="knife duel bookkeeping")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("init")
    p.add_argument("--task", required=True)
    p.add_argument("--baseline")
    p.add_argument("--models", default="haiku,sonnet,opus")
    p.add_argument("--seed", type=int)
    p.set_defaults(fn=cmd_init)
    for name, fn in (("next", cmd_next), ("tally", cmd_tally), ("status", cmd_status)):
        sp.add_parser(name).set_defaults(fn=fn)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
