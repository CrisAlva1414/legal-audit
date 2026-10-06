# Subagentes de legal-audit en Gemini CLI

Los **4 subagentes** canónicos viven en `agents/` en la raíz del repo
(fuente única). Gemini CLI los lee desde `~/.gemini/agents/*.md` (usuario) o
`.gemini/agents/*.md` (proyecto) y los expone al agente principal como tools
del mismo nombre; se invocan con el símbolo `@` al inicio del prompt
([doc subagents](https://geminicli.com/docs/core/subagents)).

## Qué cambia respecto de los canónicos

1. **Frontmatter:** Gemini lee **solo `name` y `description`** del frontmatter.
   Los campos extra que soporta la configuración de subagentes de Gemini
   (`kind`, `tools`, `mcpServers`, `model`, `temperature`, `max_turns`,
   `timeout_mins`) **no se agregan a los canónicos**: son configuración de
   ejecución por motor, y la regla del proyecto es que los prompts viven en
   `agents/*.md` y los adaptadores solo traducen. Si un equipo quiere
   restringir tools en Gemini, define el delta en un archivo local
   `~/.gemini/agents/legal-audit-gemini/*.md` (o un override en
   `settings.json` con `agents.overrides`), nunca editando el canónico.
2. **Una restricción real a documentar:** en Gemini CLI **un subagente no
   puede invocar a otro subagente** (recursión protegida). El body canónico de
   `obligation-auditor` dice "si te falta contexto, pedíselo al `code-scout`
   con tu herramienta de invocación de subagentes". En Gemini eso no se puede
   ejecutar desde dentro del subagente: es el **agente principal** el que debe
   haberle pasado el mapa del `code-scout` al delegar, o el usuario lo invoca
   con `@obligation-auditor` y `@code-scout` en la misma sesión. No hay que
   cambiar el prompt: es una nota operativa de orquestación.
3. **Invocación:** en el reporte final y en la orquestación, la capacidad
   "delegá al subagente X" se traduce a `@source-verifier`, `@code-scout`,
   `@legal-researcher`, `@obligation-auditor` al inicio del prompt.

## Cómo se instalan

```bash
mkdir -p ~/.gemini/agents
cp agents/*.md ~/.gemini/agents/
```

Los 4 archivos canónicos se copian **sin cambios** (solo nombre del archivo y
`#` del título del body; el `name` del frontmatter es el identificador que se
invoca con `@`).

## Verificar

```bash
ls -1 ~/.gemini/agents/              # 4 archivos .md
gemini skills list --all             # confirma que el ecosistema skill está sano
```

En sesión: pedí "usá @code-scout para mapear este repositorio" — la CLI debe
delegar al subagente. También podés administrarlos con `/agents`.

## Notas

- Los subagentes de Gemini se guardan en `~/.gemini/agents/` (no en
  `~/.gemini/skills/`); son dos mecanismos distintos: skills = conocimiento
  procedimental, subagentes = trabajadores con system prompt propio.
- `.agents/agents/` **no** es un alias documentado para subagentes (el alias
  `.agents/` existe para *skills*); por eso la vía canónica es
  `~/.gemini/agents/`.