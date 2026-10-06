# Subagentes de legal-audit en Claude Code

Los **4 subagentes** canónicos viven en `agents/` en la raíz del repo
(fuente única). Claude Code los lee desde `~/.claude/agents/` (usuario),
`.claude/agents/` (proyecto) o desde la carpeta `agents/` de un plugin.
Este adaptador hace que lleguen a Claude Code **sin duplicar sus prompts**.

## Qué cambia respecto de los canónicos

Los canónicos (`agents/*.md`) tienen frontmatter `name` + `description` con un
body **agnóstico de motor**: no nombran `Agent(`, `Bash(` ni ninguna tool.
Claude Code puede cargarlos tal cual: `name` y `description` son los dos únicos
campos obligatorios del frontmatter de subagente ([doc](https://code.claude.com/docs/en/sub-agents)).

Lo que **puede** agregarse por frontmatter de Claude Code (sin tocar el body)
es configuración de ejecución. Ninguna es requerida; documentamos cuáles
existen y cuándo tendría sentido usarlas:

| Campo | Efecto | ¿Aplicaría a legal-audit? |
|---|---|---|
| `tools` | Allowlist de tools del subagente (p. ej. `Read, Grep, Glob, Bash`). Si se omite, hereda todas. | Sí, como *hardening* opcional: p. ej. `source-verifier` con `WebFetch, Read` y `obligation-auditor` sin `Write`. |
| `disallowedTools` | Denylist sobre las heredadas (p. ej. `Write, Edit`). | Preferible al allowlist para no romper herramientas futuras. |
| `model` | Modelo del subagente (`sonnet`, `opus`, `haiku`, id completo, o `inherit`). | `[PENDIENTE: decisión]` — no fijamos modelo canónico porque es política de costos de cada usuario. |
| `permissionMode` | Modo de permisos (`default`, `acceptEdits`, `auto`, `dontAsk`…). **Ignorado para subagentes de plugin.** | Solo si se copia a `~/.claude/agents/`; en el plugin no aplica. |
| `background` | True si el subagente corre en background. | No: la auditoría es secuencial y sus resultados alimentan fases siguientes. |
| `maxTurns` | Tope de turnos antes de devolver resultado parcial. | Útil para `code-scout` en repos grandes. |
| `skills`, `mcpServers`, `hooks`, `memory`, `isolation`, `omitClaudeMd`, `effort` | Características avanzadas del subagente. | Ninguna necesaria hoy. `hooks`/`mcpServers`/`permissionMode` se ignoran en subagentes de plugin. |

> **Regla de mantenimiento:** si una adaptación requiere un campo de frontmatter,
> el delta se documenta ACÁ y se define como overlay al copiar/instalar — nunca
> se edita el `agents/*.md` canónico con campos de un solo motor.

## Cómo llegan a Claude Code

Hay dos vías:

### A) Plugin (recomendado en este adaptador)

El plugin vive en este directorio. Su `agents/` contiene **enlaces simbólicos**
a `../../../agents/*.md` y su `skills/legal-audit` es un enlace simbólico a
`../../../skills/legal-audit` — así el plugin distribuye los mismos archivos,
no copias. Git preserva los symlinks, así que `git clone` mantiene la fuente
única.

Consecuencias documentadas del schema de plugins
([manifest](https://code.claude.com/docs/en/plugins/manifest-reference)):

- Los subagentes del plugin se invocan **con prefijo**: `legal-audit:code-scout`,
  `legal-audit:obligation-auditor`, etc.
- Los subagentes de plugin **no soportan** `hooks`, `mcpServers` ni
  `permissionMode` en frontmatter (ignorados por seguridad). Si alguien necesita
  esos campos, debe copiar el `.md` a `~/.claude/agents/`.
- `[PENDIENTE: verificar]` el seguimiento de symlinks dentro de un plugin para
  instalaciones por `claude plugin marketplace add <ruta-local>` en todas las
  versiones; la doc oficial cubre symlinks de skills en marketplaces
  ([host-marketplace](https://code.claude.com/docs/en/plugins/host-marketplace))
  pero no prometemos un comportamiento idéntico en todos los builds. Si el
  symlink molesta: `cp -r` de los 4 `.md` mantiene la skill funcional, a costa
  de la fuente única (solo aceptable para una release empaquetada).

### B) Symlink/copy directo (sin plugin)

```bash
ln -s "$(pwd)/skills/legal-audit" ~/.claude/skills/legal-audit   # la skill (symlink soportado)
mkdir -p ~/.claude/agents
cp agents/*.md ~/.claude/agents/                                 # los 4 subagentes
```

El skill symlink está explícitamente soportado por la doc
([skills](https://code.claude.com/docs/en/skills): "a `<skill-name>` entry in
the enterprise, personal, or project location can be a symlink"). Para
`~/.claude/agents/` usamos `cp` porque la doc de subagentes no garantiza
seguimiento de symlinks en agentes.

## Verificar

```bash
claude plugin validate ./adapters/claude        # valida marketplace + plugin
claude plugin marketplace add ./adapters/claude
claude plugin install legal-audit@legal-audit-marketplace
claude plugin list                              # legal-audit@legal-audit-marketplace ✔ enabled
```

En sesión: `/agents` (deben aparecer `legal-audit:source-verifier`,
`legal-audit:obligation-auditor`, …) y `/skills` (debe aparecer
`legal-audit:legal-audit` como skill del plugin, además de la skill personal si
la instalaste por la vía B).