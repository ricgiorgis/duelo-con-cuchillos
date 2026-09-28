---
name: duelo-a-muerte
description: Knife duel (duelo a muerte con cuchillos): 9 sub-agents (haiku, sonnet, opus crossed with practical, technical and skeptic lenses) answer one task from a shared research dossier, attack each other in groups of three, revise, and three blind judges (one per model) pick the most useful, evidence-backed answer. Run it only when the user explicitly asks (duelo, duelo a muerte, knife duel, knife fight). Otherwise, when a question is high-stakes, has several defensible options, or depends on facts that may be stale, only suggest it in one line in the user's language (Spanish or English) and wait for a yes.
---

# Duelo a muerte con cuchillos / Knife duel

Nine sub-agents answer the same task. They are the three models (haiku, sonnet, opus) crossed with three lenses (Practical, Technical, Skeptic). All nine work from one shared research dossier. They attack each other in groups of three, revise once, and then three blind judges, one per model, score every answer. The winner is the answer with the highest combined score, which favors answers that are useful to the asker and backed by evidence over answers that are merely sophisticated.

Cost: 31 sub-agent calls (1 research, 9 answers, 9 attacks, 9 revisions, 3 judges). You are the orchestrator. You never compete, attack or judge, and you never pick the winner.

## 0. When to run it and when to suggest it

Run it only when the user explicitly asks. Phrases that count as asking: "duelo", "duelo a muerte", "duelo con cuchillos", "hacé un duelo", "ponelos a pelear", "knife duel", "knife fight", "make them fight", or naming this skill.

Otherwise, never run it on your own. Suggest it in one line at the end of your normal answer when at least one of these holds:
- the decision has real consequences: money, architecture, a purchase, hiring, strategy, a legal or contractual choice;
- there are several defensible options and the right one depends on the asker's constraints;
- the answer depends on current facts (prices, versions, rules, market data) that you are unsure of or that may have changed;
- the user has pushed back on two answers in a row for the same request.

Do not suggest it for quick facts, casual chat, taste-only creative work, emotional or wellbeing conversations, or anything urgent. Suggest it at most once per topic. If the user declines, do not bring it up again for that topic.

Write the suggestion in the language of the user's last message:
- Spanish: `Men, esto pide un duelo a muerte con cuchillos: 9 respuestas de 3 modelos se atacan entre sí y 3 jueces eligen la mejor (31 subagentes). ¿Le damos?`
- English: `This one calls for a knife fight to the death: 9 answers from 3 models attack each other and 3 judges pick the best one (31 sub-agents). Want me to run it?`

Wait for a yes before you spend anything.

## 1. Write the task file

Sub-agents cannot see this conversation. The file is the only thing they know. Write `duel-task.md` in the working directory so it stands on its own:
- The request, in the user's words where possible.
- Every requirement and constraint the user stated anywhere in the conversation: audience, budget, time, available resources, stack, format, length, language, and what must not change.
- The context a stranger would need: absolute paths of the relevant files, pasted data, what the product or situation is.
- What "done" looks like, if the user said.
- If the user rejected an earlier answer: what they disliked, in their words.

Do not add requirements the user never gave, and do not write your own view of the right answer into the file, because that pushes all nine the same way. If the task is too vague to be worth 31 calls, ask one clarifying question first.

If the user rejected an earlier answer, write that answer word for word to `duel-baseline.md`. The judges will score it blind alongside the nine answers.

## 2. Install the tool and start the run

If `duel.py` is not already in the working directory with the line `# DUEL_VERSION 1` at the top, write the script from the end of this skill to `duel.py`, verbatim. Then run:

```bash
python3 duel.py init --task duel-task.md [--baseline duel-baseline.md]
```

Tell the user in one line that the duel has started and that it uses 31 sub-agents.

## 3. The loop

Drive everything with `python3 duel.py next`. Each time, it prints the current phase and one `JOB` line per sub-agent to launch:

`JOB <id> | model=<haiku|sonnet|opus> | prompt: <text>`

For each phase:
1. Launch every JOB of the phase in a single message, in parallel, with one Agent call per job: `subagent_type` general-purpose, `model` exactly as printed, `description` "duel <id>", and `prompt` set to the text after `prompt:`, verbatim.
2. When all of them have replied, run `python3 duel.py next` again. If an output is missing, it relaunches only that job. After the retry limit it marks the job NO OUTPUT and moves on. A judge that keeps failing is dropped, and the tally says so.
3. When it prints `PHASE tally`, run `python3 duel.py tally`.

The phases in order: research (1), duel (9), attack (9), revise (9), judge (3), tally.

After each phase, give the user one short line of progress, for example "Ataques listos, van las revisiones." Never paste answers, attacks or verdicts into the chat. Do not read them during the run: the state is on disk, and `python3 duel.py status` tells you where the run stands. If your context gets compacted, run `status` and then `next`, and carry on.

## 4. The result

Read `result.md` and the winning answer at the path it gives. Those are the only run files you read. Then give the user:
1. The winning answer, in full. You may adapt its formatting to the user's known preferences (language, no reference links, and so on), but do not change its substance.
2. Why it won: two to four short points taken from the judges' reasons and notes.
3. A compact scoreboard: the winner's model and lens, the judges' first places, and whether the verdict was unanimous, a two-to-one dissent or split. Add one line on the model × lens averages if they show a clear pattern, for example "the Practical lens won across all three models".
4. If there was a rejected answer, where it placed, stated honestly. If it beat the nine, say so plainly.
5. The run folder, in case they want the full record.

If the winning answer changes the user's files or systems, do not apply it. Ask first.

## Rules
- The task reaches every sub-agent through the briefs that `duel.py` builds from the one task file. Never paraphrase it for one agent or add a hint to one agent's call.
- Every brief puts the task first and the role last, so each agent reuses as much cached prefix as the platform allows. Do not reorder the briefs.
- Sub-agents write only inside `.duel/`. If one wrote anywhere else, tell the user.
- If the user says stop, stop. `python3 duel.py status` shows where the run got to, and `python3 duel.py next` resumes it.
- The judges are models too. The result is the strongest answer this duel found, not a proof that it is right. That is why the scoreboard and the dissent are shown.

## The script (write verbatim to duel.py)

```python
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
    print("ERROR: " + msg)
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
    """9 duelists: every model x every lens. Groups form a Latin square, so each group of three has
    one duelist per model and one per lens."""
    keys = list(LENSES)
    duelists, groups = {}, []
    n = 0
    for mi, m in enumerate(models):
        for li, lk in enumerate(keys):
            n += 1
            duelists["d%d" % n] = {"model": m, "lens": lk, "mi": mi, "li": li}
    for g in range(3):
        members = []
        for mi in range(3):
            li = (mi + g) % 3
            members.append(next(d for d, v in duelists.items() if v["mi"] == mi and v["li"] == li))
        groups.append(members)
    return duelists, groups


def cmd_init(a):
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    if len(models) != 3:
        die("--models needs exactly three names, weakest to strongest, e.g. haiku,sonnet,opus")
    task = Path(a.task)
    if not has_output(task):
        die("task file missing or empty: %s" % task)
    seed = a.seed if a.seed is not None else random.randrange(10 ** 6)
    rd = ROOT / time.strftime("%Y%m%d-%H%M%S")
    for sub in ["solutions", "attacks", "attacks_in", "defense", "revised", "judging", "verdicts", "briefs", "scratch"]:
        (rd / sub).mkdir(parents=True, exist_ok=True)
    (rd / "task.md").write_text(task.read_text())
    has_base = False
    if a.baseline:
        b = Path(a.baseline)
        if not has_output(b):
            die("baseline file missing or empty: %s" % b)
        (rd / "baseline.md").write_text(b.read_text())
        has_base = True
    duelists, groups = build_grid(models)
    st = {"seed": seed, "models": models, "duelists": duelists, "groups": groups,
          "baseline": has_base, "tries": {}, "mapping": None, "done": False}
    save(rd, st)
    (ROOT / "LATEST").write_text(str(rd.resolve()))
    print("RUN %s  seed %d" % (rd.resolve(), seed))
    print("models (weak->strong): %s | research: %s | judges: %s" % (", ".join(models), models[1], ", ".join(models)))
    for i, g in enumerate(groups, 1):
        print("group %d: " % i + ", ".join("%s=%s/%s" % (d, duelists[d]["model"], LENSES[duelists[d]["lens"]][0]) for d in g))
    print("calls: 1 research + 9 answers + 9 attacks + 9 revisions + 3 judges = 31")
    print("Next: python3 duel.py next")


def rivals(st, d):
    g = next(g for g in st["groups"] if d in g)
    return [x for x in g if x != d]


def split_attacks(rd, st):
    """Cut every attacker's file into per-target sections, so a defender reads only what hit it."""
    got = {d: [] for d in st["duelists"]}
    for att in st["duelists"]:
        p = rd / "attacks" / ("%s.md" % att)
        text = p.read_text() if p.exists() else "NO OUTPUT"
        parts = re.split(r"^===\s*TARGET\s+(d\d+)\s*===\s*$", text, flags=re.M)
        found = {}
        for i in range(1, len(parts) - 1, 2):
            found[parts[i]] = parts[i + 1].strip()
        for tgt in rivals(st, att):
            body = found.get(tgt)
            if body is None:
                body = "NO OUTPUT" if text.strip() == "NO OUTPUT" else "(attacker's file had no clean section for you; full file follows)\n" + text
            got[tgt].append("### Attacks from %s\n%s" % (att, body))
    for d, chunks in got.items():
        (rd / "attacks_in" / ("%s.md" % d)).write_text("\n\n".join(chunks) + "\n")


def anonymize(rd, st):
    rng = random.Random(st["seed"])
    entries = list(st["duelists"])
    if st["baseline"]:
        entries.append("baseline")
    rng.shuffle(entries)
    mapping = {}
    for i, e in enumerate(entries):
        letter = chr(ord("A") + i)
        if e == "baseline":
            src = rd / "baseline.md"
        else:
            src = rd / "revised" / ("%s.md" % e)
            if not has_output(src) or src.read_text().strip() == "NO OUTPUT":
                src = rd / "solutions" / ("%s.md" % e)
        (rd / "judging" / ("%s.md" % letter)).write_text(src.read_text() if src.exists() else "NO OUTPUT")
        mapping[letter] = e
    st["mapping"] = mapping
    save(rd, st)


def jobs_for(rd, st, phase):
    task = (rd / "task.md").read_text()
    dossier = str((rd / "dossier.md").resolve())
    common = {"task": task, "dossier": dossier, "run_dir": str(rd.resolve())}
    jobs = []
    if phase == "research":
        out = rd / "dossier.md"
        jobs.append(("research", st["models"][1], T_RESEARCH.format(out=out.resolve(), **common), [out]))
    elif phase in ("duel", "attack", "revise"):
        for d, v in st["duelists"].items():
            ln, lh = LENSES[v["lens"]]
            own = (rd / "solutions" / ("%s.md" % d)).resolve()
            if phase == "duel":
                out = rd / "solutions" / ("%s.md" % d)
                txt = T_DUEL.format(id=d, lens_name=ln, lens_how=lh, out=out.resolve(), **common)
                jobs.append((d, v["model"], txt, [out]))
            elif phase == "attack":
                t1, t2 = rivals(st, d)
                out = rd / "attacks" / ("%s.md" % d)
                txt = T_ATTACK.format(id=d, lens_name=ln, lens_how=lh, t1=t1, t2=t2, own=own,
                                      p1=(rd / "solutions" / ("%s.md" % t1)).resolve(),
                                      p2=(rd / "solutions" / ("%s.md" % t2)).resolve(),
                                      out=out.resolve(), **common)
                jobs.append((d, v["model"], txt, [out]))
            else:
                out = rd / "revised" / ("%s.md" % d)
                dout = rd / "defense" / ("%s.md" % d)
                txt = T_REVISE.format(id=d, lens_name=ln, lens_how=lh, own=own,
                                      attacks_in=(rd / "attacks_in" / ("%s.md" % d)).resolve(),
                                      defense_out=dout.resolve(), out=out.resolve(), **common)
                jobs.append((d, v["model"], txt, [out, dout]))
    elif phase == "judge":
        letters = sorted(st["mapping"])
        answer_list = "\n".join("Answer %s: %s" % (L, (rd / "judging" / ("%s.md" % L)).resolve()) for L in letters)
        for m in st["models"]:
            out = rd / "verdicts" / ("judge-%s.json" % m)
            txt = T_JUDGE.format(k=len(letters), letters=", ".join(letters), answer_list=answer_list,
                                 judge=m, out=out.resolve(), **common)
            jobs.append(("judge-%s" % m, m, txt, [out]))
    return jobs


def current_phase(rd, st):
    if st.get("done"):
        return "done"
    for phase in PHASES[:-1]:
        pending = [j for j in jobs_for_check(rd, st, phase) if not all(has_output(o) for o in j[1])]
        if pending:
            return phase
    return "tally"


def jobs_for_check(rd, st, phase):
    ds = list(st["duelists"])
    if phase == "research":
        return [("research", [rd / "dossier.md"])]
    if phase == "duel":
        return [(d, [rd / "solutions" / ("%s.md" % d)]) for d in ds]
    if phase == "attack":
        return [(d, [rd / "attacks" / ("%s.md" % d)]) for d in ds]
    if phase == "revise":
        return [(d, [rd / "revised" / ("%s.md" % d), rd / "defense" / ("%s.md" % d)]) for d in ds]
    if phase == "judge":
        skip = rd / "verdicts" / ".skip"
        skipped = skip.read_text().split(",") if skip.exists() else []
        return [("judge-%s" % m, [rd / "verdicts" / ("judge-%s.json" % m)]) for m in st["models"]
                if "judge-%s" % m not in skipped]
    return []


def cmd_next(a):
    rd = run_dir()
    st = load(rd)
    phase = current_phase(rd, st)
    if phase == "done":
        print("DONE. Read %s and the winning answer it names." % (rd / "result.md").resolve())
        return
    if phase == "tally":
        print("PHASE tally: all judges are in. Run: python3 duel.py tally")
        return
    if phase == "revise" and not any((rd / "attacks_in").iterdir()):
        split_attacks(rd, st)
    if phase == "judge" and not st.get("mapping"):
        anonymize(rd, st)
        st = load(rd)
    jobs = [j for j in jobs_for(rd, st, phase) if not all(has_output(o) for o in j[3])]
    runnable, gave_up = [], []
    for jid, model, text, outs in jobs:
        key = "%s:%s" % (phase, jid)
        tries = st["tries"].get(key, 0)
        if tries >= MAX_TRIES[phase]:
            if phase == "judge":
                gave_up.append(jid)
                continue
            for o in outs:
                if not has_output(o):
                    Path(o).write_text("NO OUTPUT\n")
            gave_up.append(jid)
            continue
        st["tries"][key] = tries + 1
        brief = rd / "briefs" / ("%s-%s.md" % (phase, jid))
        brief.write_text(text)
        runnable.append((jid, model, brief.resolve()))
    save(rd, st)
    if gave_up:
        print("gave up on %s after the retry limit (marked NO OUTPUT; judges that fail are skipped)." % ", ".join(gave_up))
    if not runnable:
        if phase == "judge" and gave_up:
            (rd / "verdicts" / ".skip").write_text(",".join(gave_up))
            print("Run: python3 duel.py tally")
            return
        return cmd_next(a)
    print("PHASE %s: launch these %d sub-agents in ONE message, in parallel, then run next again." % (phase, len(runnable)))
    for jid, model, brief in runnable:
        print("JOB %s | model=%s | prompt: You are part of a structured multi-agent review. Your whole brief is in this file; read it and follow it exactly: %s" % (jid, model, brief))


def parse_json(p):
    raw = Path(p).read_text()
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


def total(s):
    t = 0.0
    for k, w in WEIGHTS.items():
        try:
            v = float(s.get(k, 0))
        except (TypeError, ValueError):
            v = 0.0
        t += w * max(0.0, min(10.0, v)) / 10.0
    return round(t, 1)


def cmd_tally(a):
    rd = run_dir()
    st = load(rd)
    mapping = st.get("mapping") or die("no judging yet. Run next.")
    verdicts = {}
    for m in st["models"]:
        p = rd / "verdicts" / ("judge-%s.json" % m)
        if has_output(p):
            v = parse_json(p)
            if v and isinstance(v.get("scores"), dict):
                verdicts[m] = v
    if not verdicts:
        die("no readable verdicts. Re-run next to retry the judges.")
    rows = {}
    for L, who in mapping.items():
        per, fatal = {}, 0
        for m, v in verdicts.items():
            s = v["scores"].get(L) or v["scores"].get(L.lower()) or {}
            per[m] = total(s)
            fatal += 1 if str(s.get("fatal", False)).lower() == "true" else 0
        rows[L] = {"who": who, "per": per, "sum": round(sum(per.values()), 1), "fatal": fatal}
    firsts = {}
    for m, v in verdicts.items():
        t3 = v.get("top3") or []
        if t3:
            firsts[m] = t3[0]
    need = 2 if len(verdicts) >= 2 else 1
    eligible = [L for L in rows if rows[L]["fatal"] < need] or list(rows)
    ranked = sorted(rows, key=lambda L: (L in eligible,
                                         rows[L]["sum"],
                                         sum(1 for f in firsts.values() if f == L),
                                         rows[L]["per"].get(st["models"][2], 0)), reverse=True)
    win = ranked[0]
    who = rows[win]["who"]
    if who == "baseline":
        win_path = (rd / "baseline.md").resolve()
    else:
        win_path = (rd / "judging" / ("%s.md" % win)).resolve()
    maxsum = 100 * len(verdicts)

    def label(w):
        if w == "baseline":
            return "rejected answer (baseline)"
        v = st["duelists"][w]
        return "%s %s/%s" % (w, v["model"], LENSES[v["lens"]][0])

    out = ["# Duel result", ""]
    out.append("Winner: %s, %s of %d points." % (label(who), rows[win]["sum"], maxsum))
    out.append("Winning answer: %s" % win_path)
    if who != "baseline":
        out.append("Its defense: %s" % (rd / "defense" / ("%s.md" % who)).resolve())
    out.append("")
    out.append("Judges' first places: " + ", ".join("%s -> %s" % (m, label(mapping.get(L, L))) for m, L in firsts.items()))
    uniq = set(firsts.values())
    if len(firsts) == 3 and len(uniq) == 3:
        out.append("Split verdict: the three judges each picked a different winner. Treat the result as close.")
    elif len(firsts) == 3 and len(uniq) == 2:
        odd = [m for m, L in firsts.items() if list(firsts.values()).count(L) == 1]
        out.append("Dissent: the %s judge picked differently from the other two." % odd[0])
    missing = [m for m in st["models"] if m not in verdicts]
    if missing:
        out.append("Missing or unreadable verdicts: %s. Result uses %d judge(s)." % (", ".join(missing), len(verdicts)))
    for m, v in verdicts.items():
        if v.get("reason"):
            out.append("- %s judge: %s" % (m, v["reason"]))
    out.append("")
    out.append("| rank | entry | " + " | ".join(verdicts) + " | total | fatal flags |")
    out.append("|---|---|" + "---|" * len(verdicts) + "---|---|")
    for i, L in enumerate(ranked, 1):
        r = rows[L]
        out.append("| %d | %s | %s | %s | %d |" % (i, label(r["who"]), " | ".join(str(r["per"][m]) for m in verdicts), r["sum"], r["fatal"]))
    out.append("")
    out.append("Average total by model x lens (out of %d):" % maxsum)
    lk = list(LENSES)
    out.append("| model | " + " | ".join(LENSES[k][0] for k in lk) + " | model avg |")
    out.append("|---|" + "---|" * (len(lk) + 1))
    for m in st["models"]:
        cells = []
        for k in lk:
            d = next(d for d, v in st["duelists"].items() if v["model"] == m and v["lens"] == k)
            L = next(L for L, w in mapping.items() if w == d)
            cells.append(rows[L]["sum"])
        out.append("| %s | %s | %.1f |" % (m, " | ".join(str(c) for c in cells), sum(cells) / len(cells)))
    lens_avg = []
    for k in lk:
        vals = [rows[next(L for L, w in mapping.items() if w == d)]["sum"] for d, v in st["duelists"].items() if v["lens"] == k]
        lens_avg.append("%.1f" % (sum(vals) / len(vals)))
    out.append("| lens avg | " + " | ".join(lens_avg) + " | |")
    if st["baseline"]:
        pos = ranked.index(next(L for L, w in mapping.items() if w == "baseline")) + 1
        out.append("")
        out.append("The rejected answer, judged blind among the others, placed %d of %d." % (pos, len(ranked)))
    (rd / "result.md").write_text("\n".join(out) + "\n")
    st["done"] = True
    save(rd, st)
    print("\n".join(out))


def cmd_status(a):
    rd = run_dir()
    st = load(rd)
    print("run %s | phase %s" % (rd, current_phase(rd, st)))
    for phase in PHASES[:-1]:
        js = jobs_for_check(rd, st, phase)
        ok = sum(1 for j in js if all(has_output(o) for o in j[1]))
        print("  %-8s %d/%d" % (phase, ok, len(js)))


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
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
```
