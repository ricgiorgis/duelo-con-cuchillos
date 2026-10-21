"""Tests for duel.py. Standard library only: python3 -m unittest discover -s tests -v

They run whole duels through the command line with stand-in sub-agents that write fake outputs,
and check that the two shipped copies of the script (Claude and ChatGPT) are identical."""
import json
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GPT_SCRIPT = REPO / "chatgpt" / "duelo-a-muerte" / "scripts" / "duel.py"
CLAUDE_SKILL = REPO / "skills" / "duelo-a-muerte" / "SKILL.md"
CRITERIA = ["practical", "evidence", "correctness", "completeness", "clarity"]


def embedded_script():
    text = CLAUDE_SKILL.read_text()
    m = re.search(r"```python\n(.*)\n```\s*$", text, flags=re.S)
    assert m, "no python block at the end of the Claude SKILL.md"
    return m.group(1)


class Sandbox:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="duel-test-"))
        shutil.copy(GPT_SCRIPT, self.dir / "duel.py")

    def run(self, *args):
        r = subprocess.run([sys.executable, "duel.py", *args], cwd=self.dir, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


def fake_agent(phase, brief, rng, garbage_attacker=None, fatal_letter=None):
    """Do what a sub-agent would do with its brief, badly but in the right places."""
    b = Path(brief).read_text()
    if phase == "research":
        Path(re.search(r"Write (\S+) with", b).group(1)).write_text("## Facts\n- x | y | 2026 | high\n")
    elif phase == "duel":
        Path(re.search(r"Write your answer to (\S+?)\.\s", b).group(1)).write_text("answer\n")
    elif phase == "attack":
        out = re.search(r"Write to (\S+) in exactly", b).group(1)
        me = re.search(r"ROLE: competitor (d\d+)", b).group(1)
        targets = re.findall(r"^- (d\d+): ", b, flags=re.M)
        if me == garbage_attacker:
            Path(out).write_text("free text with no sections at all\n")
        else:
            Path(out).write_text("".join("=== TARGET %s ===\nATTACK 1 [MINOR] [WRONG] t\nWhere: w\nProblem: p\n" % t for t in targets))
    elif phase == "revise":
        Path(re.search(r"Write your defense to (\S+?),", b).group(1)).write_text("ATTACK 1 from dX: CONCEDE. ok\n")
        Path(re.search(r"Write your revised answer to (\S+?)\.\s", b).group(1)).write_text("revised\n")
    elif phase == "judge":
        out = re.search(r"Write only this JSON to (\S+?),", b).group(1)
        letters = re.findall(r"^Answer (\w):", b, flags=re.M)
        scores = {}
        for L in letters:
            s = {k: rng.randint(2, 10) for k in CRITERIA}
            s["fatal"] = (L == fatal_letter)
            if L == fatal_letter:
                s.update({k: 10 for k in CRITERIA})
            scores[L] = s
        Path(out).write_text("```json\n" + json.dumps({"scores": scores, "top3": letters[:3], "reason": "r"}) + "\n```\n")


def drive(sb, rng, skip_once=(), never=(), garbage_attacker=None, fatal_letter=None, max_steps=60):
    skipped, phases = set(), []
    for _ in range(max_steps):
        code, out = sb.run("next")
        assert code == 0, out
        if "Run: python3 duel.py tally" in out:
            return phases
        m = re.search(r"PHASE (\w+):", out)
        assert m, out
        phase = m.group(1)
        jobs = re.findall(r"^JOB (\S+) \| model=(\S+) \| prompt: .*: (\S+)$", out, flags=re.M)
        phases.append((phase, len(jobs)))
        for jid, _model, brief in jobs:
            key = "%s:%s" % (phase, jid)
            if key in never:
                continue
            if key in skip_once and key not in skipped:
                skipped.add(key)
                continue
            fake_agent(phase, brief, rng, garbage_attacker, fatal_letter)
    raise AssertionError("duel did not reach tally")


class TestCopies(unittest.TestCase):
    def test_embedded_script_matches_chatgpt_copy(self):
        self.assertEqual(embedded_script(), GPT_SCRIPT.read_text().rstrip("\n"))

    def test_version_marker(self):
        self.assertIn("# DUEL_VERSION 1", GPT_SCRIPT.read_text().splitlines()[1])


class TestDuel(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox()
        (self.sb.dir / "task.md").write_text("Pick a database for a personal finance app.\n")
        (self.sb.dir / "old.md").write_text("Use Postgres.\n")

    def tearDown(self):
        self.sb.close()

    def test_groups_are_a_latin_square(self):
        code, out = self.sb.run("init", "--task", "task.md", "--seed", "3")
        self.assertEqual(code, 0, out)
        st = json.loads(next((self.sb.dir / ".duel").glob("*/state.json")).read_text())
        for g in st["groups"]:
            self.assertEqual(sorted(st["duelists"][d]["model"] for d in g), sorted(st["models"]))
            self.assertEqual(sorted(st["duelists"][d]["lens"] for d in g), ["P", "S", "T"])
        seen = [d for g in st["groups"] for d in g]
        self.assertEqual(sorted(seen), sorted(st["duelists"]))

    def test_full_run_with_baseline(self):
        self.sb.run("init", "--task", "task.md", "--baseline", "old.md", "--seed", "7")
        phases = drive(self.sb, random.Random(1))
        self.assertEqual([p for p, _ in phases], ["research", "duel", "attack", "revise", "judge"])
        self.assertEqual(sum(n for _, n in phases), 31)
        code, out = self.sb.run("tally")
        self.assertEqual(code, 0, out)
        self.assertIn("Winner:", out)
        self.assertIn("The rejected answer, judged blind among the others, placed", out)
        self.assertEqual(len(list((self.sb.dir / ".duel").glob("*/judging/*.md"))), 10)
        _, out = self.sb.run("next")
        self.assertTrue(out.startswith("DONE"), out)

    def test_task_is_identical_in_every_brief(self):
        self.sb.run("init", "--task", "task.md", "--seed", "1")
        drive(self.sb, random.Random(2))
        briefs = list((self.sb.dir / ".duel").glob("*/briefs/*.md"))
        self.assertEqual(len(briefs), 31)
        heads = {b.read_text().split("=== END OF THE TASK ===")[0] for b in briefs}
        self.assertEqual(len(heads), 1)

    def test_retry_then_no_output(self):
        self.sb.run("init", "--task", "task.md", "--seed", "5")
        phases = drive(self.sb, random.Random(3), skip_once={"attack:d4"}, never={"duel:d2"})
        self.assertIn(("attack", 1), phases)
        sol = next((self.sb.dir / ".duel").glob("*/solutions/d2.md")).read_text()
        self.assertEqual(sol.strip(), "NO OUTPUT")
        code, out = self.sb.run("tally")
        self.assertEqual(code, 0, out)

    def test_unparseable_attack_file_falls_back_to_full_text(self):
        self.sb.run("init", "--task", "task.md", "--seed", "5")
        drive(self.sb, random.Random(4), garbage_attacker="d1")
        rd = Path((self.sb.dir / ".duel" / "LATEST").read_text().strip())
        st = json.loads((rd / "state.json").read_text())
        victims = [d for g in st["groups"] if "d1" in g for d in g if d != "d1"]
        for v in victims:
            self.assertIn("full file follows", (rd / "attacks_in" / ("%s.md" % v)).read_text())

    def test_dead_judge_is_dropped(self):
        self.sb.run("init", "--task", "task.md", "--seed", "9")
        drive(self.sb, random.Random(5), never={"judge:judge-haiku"})
        code, out = self.sb.run("tally")
        self.assertEqual(code, 0, out)
        self.assertIn("Missing or unreadable verdicts: haiku", out)

    def test_fatal_answer_cannot_win(self):
        self.sb.run("init", "--task", "task.md", "--seed", "11")
        drive(self.sb, random.Random(6), fatal_letter="A")
        code, out = self.sb.run("tally")
        self.assertEqual(code, 0, out)
        rd = Path((self.sb.dir / ".duel" / "LATEST").read_text().strip())
        st = json.loads((rd / "state.json").read_text())
        self.assertNotIn("judging/A.md", out.split("Winning answer:")[1].splitlines()[0])
        self.assertIn("A", st["mapping"])

    def test_custom_models(self):
        code, out = self.sb.run("init", "--task", "task.md", "--models", "low,medium,high")
        self.assertEqual(code, 0, out)
        self.assertIn("research: medium", out)
        code, out = self.sb.run("init", "--task", "task.md", "--models", "a,b")
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
