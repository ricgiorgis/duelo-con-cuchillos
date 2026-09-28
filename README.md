# Duelo con cuchillos

![license](https://img.shields.io/badge/license-MIT-green) ![python](https://img.shields.io/badge/python-3.8%2B-blue) ![works with](https://img.shields.io/badge/works%20with-Claude%20%7C%20ChatGPT-black) ![dependencies](https://img.shields.io/badge/dependencies-none-lightgrey)

Stop taking the first answer. Nine AI answers from three models fight to the death over your question, three blind judges pick the one you can actually use, and every fact has to show where it came from.

[English](#english) · [Español](#español)

## English

Nine AI answers fight over one question and three blind judges pick the winner. It's a skill for Claude and ChatGPT, and the judges reward the answer that is useful to you and backed by evidence, not the one that sounds the most technical.

I built it for two things that keep happening. The model answers from memory instead of checking, and states stale or invented facts with total confidence. Or it hands you the most sophisticated solution instead of the one you can actually pull off with your time, budget and skills.

### How it works

1. One sub-agent does the research first and writes an evidence dossier: facts with sources and dates, where sources disagree, and what it couldn't confirm. Everyone works from that dossier, so nobody has to invent facts and you don't pay nine times for the same searches.
2. Nine duelists answer: three models, each one with three lenses (practical, technical, skeptic). Every factual claim has to come from the dossier, the task or the duelist's own check. Anything else gets marked `[ASSUMPTION]`.

   | | Practical | Technical | Skeptic |
   |---|---|---|---|
   | Haiku (fast tier) | d1 | d2 | d3 |
   | Sonnet (balanced tier) | d4 | d5 | d6 |
   | Opus (strongest tier) | d7 | d8 | d9 |

3. They attack each other in groups of three. The groups form a Latin square, so each one has one duelist per model and one per lens, and every attack crosses both. An attack is WRONG, UNSUPPORTED, IMPRACTICAL, MISSING or BREAKS, and each one has to be specific enough to check.
4. Each duelist revises once, conceding and fixing, or rebutting with evidence.
5. Three judges, one per model, score all the answers blind, shuffled and relabelled A to I. The rubric: practical usefulness 30%, evidence 25%, correctness 20%, completeness 15%, clarity 10%. The three judges' scores are added up, and an answer two judges flag as fatally flawed can't win.
6. You get the winning answer, why it won, whether the judges agreed, and a model × lens table showing whether the model or the approach mattered more.

If you're rerunning a question because you didn't like the first answer, that answer goes in as a tenth, anonymous entry. The result tells you where it placed, even if it beat all nine.

### Cost

31 sub-agent calls: 1 research, 9 answers, 9 attacks, 9 revisions, 3 judges. That's a lot more than a normal answer, so keep it for decisions that matter. For scale, a 100-agent single-elimination bracket needs around 595.

The main conversation never reads the intermediate files. Sub-agents write to disk and reply with one line, `duel.py` keeps the state, and a run survives the context getting compacted. Every brief puts the shared task first and the role last, so the platform can reuse whatever cached prefix it allows.

### When it runs

Only when you ask: "duelo", "duelo a muerte", "knife duel", "knife fight", "make them fight", or the skill's name. If a question has a lot riding on it, several defensible options, or depends on facts that may be out of date, the model suggests it in one line, in your language, and waits for a yes:

> This one calls for a knife fight to the death: 9 answers from 3 models attack each other and 3 judges pick the best one (31 sub-agents). Want me to run it?

> Men, esto pide un duelo a muerte con cuchillos: 9 respuestas de 3 modelos se atacan entre sí y 3 jueces eligen la mejor (31 subagentes). ¿Le damos?

### Install

Claude Code, as a plugin:

```
/plugin marketplace add ricgiorgis/duelo-con-cuchillos
/plugin install duelo-con-cuchillos@duelo-con-cuchillos
```

Claude Code, by hand:

```bash
git clone https://github.com/ricgiorgis/duelo-con-cuchillos.git
cp -r duelo-con-cuchillos/skills/duelo-a-muerte ~/.claude/skills/
```

Claude app (claude.ai or desktop): upload `skills/duelo-a-muerte/SKILL.md` as a custom skill. The script is embedded in that file and gets written to disk on the first run.

ChatGPT or Codex: zip the `chatgpt/duelo-a-muerte` folder and upload it under Skills, or copy it into your Codex skills directory.

You need sub-agents and Python 3.8 or newer. Nothing to install with pip.

### On ChatGPT

ChatGPT surfaces don't all offer the same things, so the skill checks first and picks a mode. With sub-agents and three different models it runs as designed. With sub-agents but one model, it uses low, medium and high reasoning effort instead and tells you so. With no sub-agents at all it can run every role itself in sequence, but the judging isn't truly blind that way, so it asks before doing it.

### Limits

The judges are models too. You get the strongest answer this duel found, not proof that it's right, which is why the dissent is shown.

On Claude the three models are whatever Haiku, Sonnet and Opus are current. Sub-agents can't be pinned to older versions.

A vague question gets you nine versions of vague. Sub-agents can't see your chat, so the skill writes a standalone task file, and asks you one question first if there isn't enough to justify 31 calls.

It never applies changes to your files or systems. The winning answer comes back to you and you decide.

### The script

```bash
python3 duel.py init --task task.md [--baseline old.md] [--models haiku,sonnet,opus] [--seed N]
python3 duel.py next     # writes this phase's briefs and prints the jobs to launch
python3 duel.py status
python3 duel.py tally    # scores, winner, result.md
python3 -m unittest discover -s tests -v
```

The tests run full duels with stand-in sub-agents: retries, garbled attack files, a judge that never answers, the fatal-flaw rule, the group layout, the task being byte-identical in every brief, and the Claude and ChatGPT copies of the script matching.

## Español

Nueve respuestas de IA se pelean por una misma pregunta y tres jueces a ciegas eligen a la ganadora. Es un skill para Claude y ChatGPT, y los jueces premian la respuesta que te sirve y que tiene evidencia detrás, no la que suena más técnica.

Lo hice por dos cosas que pasan todo el tiempo. El modelo contesta de memoria en vez de investigar, y te da datos viejos o inventados con toda la seguridad del mundo. O te da la solución más sofisticada en lugar de la que de verdad podés ejecutar con tu tiempo, tu presupuesto y lo que sabés hacer.

### Cómo funciona

1. Un subagente investiga primero y arma un expediente: datos con fuente y fecha, dónde no coinciden las fuentes y lo que no pudo confirmar. Todos trabajan sobre ese expediente, así nadie inventa y no pagás nueve veces las mismas búsquedas.
2. Responden nueve duelistas: tres modelos (Haiku, Sonnet y Opus, o los niveles rápido, equilibrado y máximo en ChatGPT), cada uno con tres enfoques: práctico, técnico y escéptico. Todo dato sale del expediente, de la tarea o de una verificación propia. Lo demás va marcado `[ASSUMPTION]`.
3. Se atacan en tríos cruzados, con un modelo de cada tipo y un enfoque de cada tipo por trío.
4. Cada uno revisa una vez: concede y corrige, o refuta con evidencia.
5. Tres jueces, uno por modelo, califican todas las respuestas sin saber de quién es cada una. La rúbrica: utilidad práctica 30%, evidencia 25%, corrección 20%, completitud 15%, claridad 10%. Se suman los puntos de los tres, y una respuesta que dos jueces marcan con falla fatal no puede ganar.
6. Te llega la ganadora, por qué ganó, si los jueces coincidieron y una tabla modelo × enfoque que muestra qué pesó más.

Si repetís una pregunta porque no te gustó la primera respuesta, esa entra como décima respuesta anónima, y el resultado te dice en qué lugar quedó aunque les haya ganado a las nueve.

### Costo

31 llamadas a subagentes. Es bastante más que una respuesta normal, así que guardalo para decisiones que importan. Como referencia, un torneo de eliminación directa con 100 agentes anda por las 595.

### Cuándo se activa

Solo si lo pedís: "duelo", "duelo a muerte", "duelo con cuchillos", "ponelos a pelear". Si la pregunta tiene mucho en juego, varias opciones defendibles o depende de datos que pueden estar desactualizados, el modelo lo sugiere en una línea, en tu idioma, y espera tu sí.

### Instalación

Los pasos son los mismos de la sección en inglés: plugin de Claude Code, copia manual, app de Claude, o ChatGPT/Codex. Necesitás subagentes y Python 3.8 o más nuevo.

---

The idea of making agents compete comes from [arena-skill](https://github.com/Jakeschincariol/arena-skill). This is an independent redesign (shared research, cross-model duelists, several blind judges, a rubric that puts usefulness first), and no code was taken from it.

MIT License © 2026 Rik Giorgis
