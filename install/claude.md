# Instalación en Claude Code

> Comandos verificados contra https://code.claude.com/docs/en/skills y la
> doc de plugin marketplace. Corré todo desde la raíz del repo clonado de
> `legal-audit`. El `<owner>` no está definido todavía
> `[PENDIENTE: owner real del repo en GitHub]`.

## Qué se instala

1. **La skill** `skills/legal-audit/` (con `references/` y `scripts/`).
2. **Los 4 subagentes** (`source-verifier`, `legal-researcher`, `code-scout`,
   `obligation-auditor`).

## Vía A — Plugin (recomendado, single source of truth)

El adaptador `adapters/claude/` es un marketplace + plugin válido; los
subagentes y la skill se sirven por symlinks a la fuente única.

```bash
claude plugin validate ./adapters/claude
claude plugin marketplace add ./adapters/claude
claude plugin install legal-audit@legal-audit-marketplace
```

En sesión: `/plugin marketplace add ./adapters/claude` + `/plugin install`.

**Para instalación remota** (cuando el repo esté hosteado), el marketplace no
está en la raíz del repo; agregalo por settings:

```json
{
  "extraKnownMarketplaces": {
    "legal-audit-marketplace": {
      "source": {
        "source": "github",
        "repo": "<owner>/legal-audit",
        "path": "adapters/claude/.claude-plugin/marketplace.json"
      }
    }
  }
}
```

## Vía B — Symlink + copia directa

```bash
ln -s "$(pwd)/skills/legal-audit" ~/.claude/skills/legal-audit
mkdir -p ~/.claude/agents
cp agents/*.md ~/.claude/agents/
```

## Destinos

| Origen | Destino | Modo |
|---|---|---|
| `skills/legal-audit/` | `~/.claude/skills/legal-audit/` | symlink (soportado) |
| `agents/*.md` (4) | `~/.claude/agents/*.md` | copia |
| `adapters/claude/` | plugin `legal-audit@legal-audit-marketplace` | marketplace |

## Verificar

```bash
claude plugin list          # vía A: legal-audit@legal-audit-marketplace ✔ enabled
claude plugin details legal-audit   # vía A: Skills (1), Agents (4)
ls -l ~/.claude/skills/legal-audit  # vía B: symlink
```

En sesión: `/skills` (debe listar `legal-audit` o `legal-audit:legal-audit`)
y `/agents` (los 4 subagentes; en plugin, con prefijo `legal-audit:`).

## Desinstalar

```bash
# Vía A:
/plugin uninstall legal-audit@legal-audit-marketplace
claude plugin marketplace remove legal-audit-marketplace

# Vía B:
rm ~/.claude/skills/legal-audit
rm ~/.claude/agents/source-verifier.md \
   ~/.claude/agents/legal-researcher.md \
   ~/.claude/agents/code-scout.md \
   ~/.claude/agents/obligation-auditor.md
```

## Notas

- `npx skills` (Vercel Labs) es el instalador multi-agente emergente;
  `[PENDIENTE: verificar]` la sintaxis exacta para skills en subdirectorio.
- Delta de frontmatter y limitaciones del plugin (subagentes sin `hooks`/
  `mcpServers`/`permissionMode`, prefijo `legal-audit:`):
  [`adapters/claude/agents/claude-agents.md`](../adapters/claude/agents/claude-agents.md).