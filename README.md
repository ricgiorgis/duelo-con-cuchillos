# Duelo a muerte con cuchillos (Knife duel)

[English](#english) · [Español](#español)

---

## English

A skill for Claude and ChatGPT that makes nine AI answers fight over one question and has three blind judges pick the winner. The judges reward the answer that is actually useful to you and backed by evidence, not the one that sounds the most technical.

It exists because of two failures every heavy AI user knows. First, the model answers from memory instead of checking, and states stale or invented facts with total confidence. Second, it gives you the most sophisticated solution instead of the one you can actually execute with your time, budget and skills.

### How it works

1. **Research, once.** One sub-agent builds an evidence dossier with sources and dates, plus what it could not confirm. Everybody works from the same dossier, so nobody needs to make facts up and you don't pay nine times for the same searches.
2. **Nine duelists.** Three models crossed with three lenses:

   | | Practical | Technical | Skeptic |
   |---|---|---|---|
   | Haiku / fast tier | d1 | d2 | d3 |
   | Sonnet / balanced tier | d4 | d5 | d6 |
   | Opus / strongest tier | d7 | d8 | d9 |

   Every factual claim must come from the dossier, the task, or the duelist's own check. Anything else has to be marked `[ASSUMPTION]`.
3. **Attack in groups of three.** The groups form a Latin square, so each one has one duelist per model and one per lens, and every attack crosses both. Attacks are labelled WRONG, UNSUPPORTED, IMPRACTICAL, MISSING or BREAKS.
4. **Revise once.** Each duelist concedes and fixes, or rebuts with evidence.
5. **Three blind judges, one per model.** Answers are shuffled and relabelled A to I. The rubric weighs practical usefulness 30%, evidence 25%, correctness 20%, completeness 15% and clarity 10%. Scores are summed across judges. An answer that two judges flag as fatally flawed cannot win.
6. **Result.** You get the winning answer, why it won, whether the judges agreed, and a model × lens table that shows whether the model or the approach mattered more.

If you are rerunning a question because you didn't like the first answer, that answer goes in as a tenth, anonymous entry. The result tells you honestly where it placed, even if it beat all nine.

### Cost

31 sub-agent calls: 1 research, 9 answers, 9 attacks, 9 revisions, 3 judges. That's a lot more than a normal answer, so save it for decisions that matter. For comparison, a 100-agent single-elimination bracket needs about 595 calls.

The orchestrator never reads the intermediate files. Sub-agents write to disk and reply with one line, and `duel.py` keeps the state, so the main conversation stays small and a run can resume after the context is compacted. Every brief puts the shared task first and the role last, so the platform can reuse as much cached prefix as it allows.

### When it runs

Only when you ask: "duelo", "duelo a muerte", "knife duel", "knife fight", "make them fight", or the skill name. When a question looks high-stakes, has several defensible options, or depends on facts that may be stale, the model suggests it in one line, in your language, and waits for a yes:

> This one calls for a knife fight to the death: 9 answers from 3 models attack each other and 3 judges pick the best one (31 sub-agents). Want me to run it?

> Men, esto pide un duelo a muerte con cuchillos: 9 respuestas de 3 modelos se atacan entre sí y 3 jueces eligen la mejor (31 subagentes). ¿Le damos?

### Install

**Claude Code, as a plugin**

```
/plugin marketplace add ricgiorgis/duelo-a-muerte
/plugin install duelo-a-muerte@duelo-a-muerte
```

**Claude Code, by hand**

```bash
git clone https://github.com/ricgiorgis/duelo-a-muerte.git
cp -r duelo-a-muerte/skills/duelo-a-muerte ~/.claude/skills/
```

**Claude app (claude.ai / desktop).** Upload `skills/duelo-a-muerte/SKILL.md` as a custom skill. The script is embedded in the file, and Claude writes it to disk on the first run.

**ChatGPT / Codex.** Zip the `chatgpt/duelo-a-muerte` folder and upload it in Skills, or copy it into your Codex skills directory. It contains `SKILL.md`, `scripts/duel.py` and `agents/openai.yaml`.

Requirements: sub-agents and Python 3.8 or newer. No packages to install.

### ChatGPT modes

ChatGPT surfaces differ, so the skill checks what it can do before it starts:
- **Full:** sub-agents with three different models. Best.
- **Effort:** sub-agents on one model at low, medium and high reasoning effort. The skill tells you that's where the diversity comes from.
- **Solo:** no sub-agents, so one context runs every role in sequence. It's weaker, because the judging isn't truly blind. The skill asks before running it this way.

### Fine print

- The judges are models too. You get the strongest answer this duel found, not proof that it's right. That's why it shows you the dissent.
- On Claude the three models are the current Haiku, Sonnet and Opus. Pinning specific older versions isn't possible through sub-agents.
- A vague task gives you nine flavours of vague. The skill writes a standalone task file, since sub-agents can't see your chat, and asks one question first if the task is too thin to be worth 31 calls.
- It never applies changes to your files or systems. The winning answer comes back to you.

### The tool

```bash
python3 duel.py init --task task.md [--baseline old.md] [--models haiku,sonnet,opus] [--seed N]
python3 duel.py next     # writes this phase's briefs and prints the jobs to launch
python3 duel.py status
python3 duel.py tally    # scores, winner, result.md
python3 -m unittest discover -s tests -v
```

The tests run complete duels with stand-in sub-agents. They cover retries, garbled attack files, a dead judge, the fatal-flaw rule, the Latin-square groups, and the check that every brief carries the task byte for byte. They also check that the Claude and ChatGPT copies of the script are identical.

---

## Español

Un skill para Claude y ChatGPT que pone a nueve respuestas de IA a pelear por una misma pregunta, y tres jueces a ciegas eligen a la ganadora. Los jueces premian la respuesta que de verdad te sirve y que está respaldada por evidencia, no la que suena más técnica.

Nace de dos fallas que conoce cualquiera que usa IA en serio. La primera: el modelo contesta de memoria en vez de investigar, y te da datos viejos o inventados con total seguridad. La segunda: te da la solución más sofisticada en lugar de la que realmente podés ejecutar con tu tiempo, presupuesto y habilidades.

### Cómo funciona

1. **Investigación, una sola vez.** Un subagente arma un expediente con fuentes, fechas y lo que no pudo confirmar. Todos trabajan sobre el mismo expediente: nadie tiene que inventar datos y no pagás nueve veces las mismas búsquedas.
2. **Nueve duelistas.** Tres modelos (Haiku, Sonnet y Opus, o los niveles rápido, equilibrado y máximo en ChatGPT), cada uno con tres enfoques: práctico, técnico y escéptico. Todo dato tiene que salir del expediente, de la tarea o de una verificación propia. Lo demás va marcado como `[ASSUMPTION]`.
3. **Ataque en tríos cruzados.** Cada trío tiene un modelo de cada tipo y un enfoque de cada tipo.
4. **Una revisión.** Cada duelista concede y corrige, o refuta con evidencia.
5. **Tres jueces a ciegas, uno por modelo.** Las respuestas llegan revueltas y etiquetadas de la A a la I. La rúbrica pesa así: utilidad práctica 30%, evidencia 25%, corrección 20%, completitud 15% y claridad 10%. Se suman los puntos de los tres jueces, y una respuesta que dos jueces marcan con falla fatal no puede ganar.
6. **Resultado.** Te llega la respuesta ganadora, por qué ganó, si los jueces coincidieron, y una tabla modelo × enfoque que muestra qué pesó más.

Si repetís una pregunta porque no te gustó la primera respuesta, esa entra como una décima respuesta anónima. El resultado te dice honestamente en qué lugar quedó, aunque les haya ganado a las nueve.

### Costo

31 llamadas a subagentes. Es bastante más que una respuesta normal, así que conviene guardarlo para decisiones que importan. Como comparación, un torneo de eliminación directa con 100 agentes usa unas 595.

### Cuándo se activa

Solo si lo pedís: "duelo", "duelo a muerte", "duelo con cuchillos", "ponelos a pelear". Si la pregunta tiene mucho en juego, varias opciones defendibles o depende de datos que pueden estar desactualizados, el modelo lo sugiere en una línea, en tu idioma, y espera tu sí.

### Instalación

Las instrucciones de instalación están arriba, en la sección en inglés: plugin de Claude Code, copia manual, app de Claude, y ChatGPT/Codex. Los requisitos son subagentes y Python 3.8 o más nuevo.

---

Inspired by the idea of making agents compete, as in [arena-skill](https://github.com/Jakeschincariol/arena-skill). This is an independent redesign with a shared research phase, cross-model duelists, blind multi-judge scoring and a rubric weighted toward practical usefulness. No code was taken from it.

MIT License © 2026 Rik Giorgis
