# Adaptadores por cliente

`legal-audit` es **portable a nivel skill** (un solo `SKILL.md` conforme al
estándar abierto agentskills.io) pero **no a nivel orquestación**: el mecanismo
para invocar subagentes, el nombre de la tool de shell y dónde se buscan los
archivos cambian por cliente. Los adaptadores de este directorio traducen esa
diferencia **sin duplicar prompts**.

## Tabla comparativa

| | OpenCode | Claude Code | Gemini CLI |
|---|---|---|---|
| Invocar subagente | tool `task` | tool `Agent` (antes `Task`) | `@nombre` al inicio del prompt |
| Shell | `bash` | `Bash` | `run_shell_command` |
| Directorio de skills | `~/.config/opencode/skills/` | `~/.claude/skills/` | `~/.gemini/skills/` o `~/.agents/skills/` |
| Subagentes | `~/.config/opencode/agents/` | `~/.claude/agents/` | `~/.gemini/agents/` |
| Frontmatter que lee en SKILL.md | `name`, `description`, `license`, `compatibility`, `metadata` | todos los de agentskills.io + extensiones (`when_to_use`, `context: fork`, `allowed-tools`, …) | solo `name` y `description` |
| Instalación de skill | symlink o `npx skills` | symlink, o plugin por marketplace | `gemini skills install` / `gemini skills link` |
| Detalle | [adapters/opencode](./opencode/) | [adapters/claude](./claude/) | [adapters/gemini](./gemini/) |
| Instrucciones de instalación | [install/opencode.md](../install/opencode.md) | [install/claude.md](../install/claude.md) | [install/gemini.md](../install/gemini.md) |

## Qué es común y qué diverge

**Común (no se adapta):** el `SKILL.md` orquestador, los 4 subagentes
(`agents/*.md`), el pack de evidencia (`references/`), los scripts
(`scripts/scan.py`, `scripts/verify_pack.py`) y los 6 detectores. Todo eso es
agnóstico de motor y está cubierto por `tests/test_prompt_invariants.py`
(the `test_portability_no_hardcoded_tools` corre SOLO sobre `skills/legal-audit/SKILL.md`
y `agents/*.md` — por eso los adaptadores pueden nombrar tools concretas).

**Diverge (se adapta):** el mecanismo de invocación de subagentes, el nombre
de la tool de shell, el directorio de instalación y el frontmatter que cada
motor entiende. Eso es exactamente lo que documentan estos tres adaptadores.

## Regla de mantenimiento

> **Los prompts viven en `skills/` y `agents/`; los adaptadores solo traducen.
> Si un prompt necesita un cambio por cliente, es que el prompt estaba mal
> escrito** (se está acoplando a un motor).

En la práctica:

1. Un cambio de **comportamiento** se hace en `skills/legal-audit/SKILL.md` o
   en `agents/*.md`, una sola vez, y aplica a los tres clientes.
2. Un cambio de **mecanismo** (cómo se invoca, dónde se instala, qué
   frontmatter opcional conviene) se documenta en el adaptador del cliente
   afectado, sin tocar el prompt canónico.
3. Los adaptadores **no copian** contenido de prompts. Donde un mecanismo
   exige archivos físicos (p. ej. subagentes dentro de un plugin de Claude
   Code), usamos **enlaces simbólicos** a la fuente única — nunca copias.
4. Si te encontrás escribiendo "en OpenCode esto se hace así pero en Claude
   asá" dentro de un `agents/*.md`, detenete: eso va en un adaptador.

## Estado por cliente

| Cliente | Skill | Subagentes | Verificado contra doc oficial |
|---|---|---|---|
| OpenCode | symlink → `skills/legal-audit` | copy → `~/.config/opencode/agents/` | sí (opencode.ai/docs/skills) |
| Claude Code | symlink a `~/.claude/skills/` o plugin | plugin con symlinks, o copy → `~/.claude/agents/` | sí (code.claude.com/docs) |
| Gemini CLI | `install --path skills/legal-audit` o `link` | copy → `~/.gemini/agents/` | sí (geminicli.com/docs) |

`[PENDIENTE]` que quedan: sintaxis exacta de `npx skills` para skills en
subdirectorio; comportamiento de symlinks dentro de un plugin de Claude Code
en todos los builds; decisión de fijar `model` en subagentes de Claude Code.