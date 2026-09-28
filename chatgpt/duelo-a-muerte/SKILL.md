---
name: duelo-a-muerte
description: Knife duel (duelo a muerte con cuchillos): 9 sub-agents (fast, balanced and strongest model tiers crossed with practical, technical and skeptic lenses) answer one task from a shared research dossier, attack each other in groups of three, revise, and three blind judges (one per tier) pick the most useful, evidence-backed answer. Run it only when the user explicitly asks (duelo, duelo a muerte, knife duel, knife fight). Otherwise, when a question is high-stakes, has several defensible options, or depends on facts that may be stale, only suggest it in one line in the user's language (Spanish or English) and wait for a yes.
---

# Duelo a muerte con cuchillos / Knife duel

Nine sub-agents answer the same task. They are three model tiers (fast, balanced, strongest) crossed with three lenses (Practical, Technical, Skeptic). All nine work from one shared research dossier. They attack each other in groups of three, revise once, and then three blind judges, one per tier, score every answer. The winner is the answer with the highest combined score, which favors answers that are useful to the asker and backed by evidence over answers that are merely sophisticated.

Cost: 31 sub-agent calls (1 research, 9 answers, 9 attacks, 9 revisions, 3 judges). You are the orchestrator. You never compete, attack or judge, and you never pick the winner.

## 0. When to run it and when to suggest it

Run it only when the user explicitly asks. Phrases that count as asking: "duelo", "duelo a muerte", "duelo con cuchillos", "hacé un duelo", "ponelos a pelear", "knife duel", "knife fight", "make them fight", or `$duelo-a-muerte`.

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

## 1. Check what this surface can do

Before the first run in a conversation, check two things:
1. **Parallel sub-agents.** Can you spawn sub-agents here? ChatGPT Work, the ChatGPT desktop app and Codex can. A plain chat may not.
2. **Model choice per sub-agent.** Can you give each sub-agent its own model? Pick three models that are available to you, from fastest to strongest. These are the three tiers.

Then use one of three modes, and tell the user in one line which one you are using:
- **Full mode.** You have sub-agents and three different models. Pass the three model names, weakest to strongest, to `init --models`.
- **Effort mode.** You have sub-agents but cannot pick a model per agent. Use the same model at low, medium and high reasoning effort, and pass `--models low,medium,high`. Tell the user that the diversity comes from reasoning effort, not from different models.
- **Solo mode.** You have no sub-agents. Run every job yourself, one after another, and treat each brief as a fresh start: do not reuse what you wrote for another job. Tell the user before you start that this mode is weaker, because one context sees everything, so the judging is not truly blind and the answers are less independent. Ask whether they still want it.

## 2. Write the task file

Sub-agents cannot see this conversation. The file is the only thing they know. Write `duel-task.md` in the working directory so it stands on its own:
- The request, in the user's words where possible.
- Every requirement and constraint the user stated anywhere in the conversation: audience, budget, time, available resources, stack, format, length, language, and what must not change.
- The context a stranger would need: paths or names of the relevant files, pasted data, what the product or situation is.
- What "done" looks like, if the user said.
- If the user rejected an earlier answer: what they disliked, in their words.

Do not add requirements the user never gave, and do not write your own view of the right answer into the file, because that pushes all nine the same way. If the task is too vague to be worth 31 calls, ask one clarifying question first.

If the user rejected an earlier answer, write that answer word for word to `duel-baseline.md`. The judges will score it blind alongside the nine answers.

## 3. Start the run

The tool is `scripts/duel.py` in this skill's folder, and it uses only Python's standard library. Copy it to the working directory, then run:

```bash
python3 duel.py init --task duel-task.md --models <fast>,<balanced>,<strongest> [--baseline duel-baseline.md]
```

Tell the user in one line that the duel has started and that it uses 31 sub-agents.

## 4. The loop

Drive everything with `python3 duel.py next`. Each time, it prints the current phase and one `JOB` line per sub-agent to launch:

`JOB <id> | model=<tier name> | prompt: <text>`

For each phase:
1. Launch every JOB of the phase at the same time, as parallel sub-agents. Give each one the model (or reasoning effort) printed on its line, and pass the text after `prompt:` verbatim as its instructions. Every sub-agent needs file access to the working directory, plus web search for the research job and for the duelists.
2. When all of them have finished, run `python3 duel.py next` again. If an output is missing, it relaunches only that job. After the retry limit it marks the job NO OUTPUT and moves on. A judge that keeps failing is dropped, and the tally says so.
3. When it prints `PHASE tally`, run `python3 duel.py tally`.

The phases in order: research (1), duel (9), attack (9), revise (9), judge (3), tally.

After each phase, give the user one short line of progress. Never paste answers, attacks or verdicts into the chat. Do not read them during the run: the state is on disk, and `python3 duel.py status` tells you where the run stands.

## 5. The result

Read `result.md` and the winning answer at the path it gives. Those are the only run files you read. Then give the user:
1. The winning answer, in full. You may adapt its formatting to the user's known preferences, but do not change its substance.
2. Why it won: two to four short points taken from the judges' reasons and notes.
3. A compact scoreboard: the winner's model and lens, the judges' first places, and whether the verdict was unanimous, a two-to-one dissent or split. Add one line on the model × lens averages if they show a clear pattern.
4. If there was a rejected answer, where it placed, stated honestly. If it beat the nine, say so plainly.
5. The run folder, in case they want the full record.

If the winning answer changes the user's files or systems, do not apply it. Ask first.

## Rules
- The task reaches every sub-agent through the briefs that `duel.py` builds from the one task file. Never paraphrase it for one agent or add a hint to one agent's instructions.
- Every brief puts the task first and the role last, so each agent reuses as much cached prefix as the platform allows. Do not reorder the briefs.
- Sub-agents write only inside `.duel/`. If one wrote anywhere else, tell the user.
- If the user says stop, stop. `python3 duel.py status` shows where the run got to, and `python3 duel.py next` resumes it.
- The judges are models too. The result is the strongest answer this duel found, not a proof that it is right. That is why the scoreboard and the dissent are shown.
