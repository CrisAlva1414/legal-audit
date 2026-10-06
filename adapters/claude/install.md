# Instalación en Claude Code

Instala la **skill** (`skills/legal-audit/`) y los **4 subagentes** (`agents/`).
Claude Code ofrece dos vías; documentamos ambas con los comandos verificados
contra la doc oficial (skills + plugin marketplace).

## Vía A — Plugin desde este adaptador (recomendado)

El adaptador `adapters/claude/` ES un marketplace + plugin válido
(`.claude-plugin/marketplace.json` + `.claude-plugin/plugin.json`). Los
subagentes y la skill se sirven por symlinks a la fuente única.

```bash
# 1. Validar (schema oficial: name/owner/plugins; agent paths ./...):
claude plugin validate ./adapters/claude

# 2. Registrar el marketplace (ruta local; para un repo hosteado, ver nota):
claude plugin marketplace add ./adapters/claude

# 3. Instalar el plugin:
claude plugin install legal-audit@legal-audit-marketplace
```

En una sesión equivale a: `/plugin marketplace add ./adapters/claude` y
`/plugin install legal-audit@legal-audit-marketplace`.

**Nota sobre hosteo:** `claude plugin marketplace add <owner>/legal-audit`
busca `marketplace.json` en la raíz del repo; el nuestro vive en
`adapters/claude/.claude-plugin/`. Para instalación remota, agregalo por
settings con el `path` explícito:

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

(Es el patrón que la doc prescribe cuando el marketplace no está en la raíz:
[marketplace-reference](https://code.claude.com/docs/en/plugins/marketplace-reference).)

## Vía B — Symlink + copia directa

```bash
ln -s "$(pwd)/skills/legal-audit" ~/.claude/skills/legal-audit
mkdir -p ~/.claude/agents
cp agents/*.md ~/.claude/agents/
```

El symlink de la skill está soportado
([skills doc](https://code.claude.com/docs/en/skills)); los subagentes se
copian porque la doc no garantiza symlinks en `~/.claude/agents/`.

## Verificar que quedó bien

```bash
claude plugin list            # legal-audit@legal-audit-marketplace: Status ✔ enabled (vía A)
claude plugin details legal-audit   # Component inventory: Skills (1) legal-audit, Agents (4)
ls -l ~/.claude/skills/legal-audit  # symlink → repo (vía B)
```

Dentro de una sesión: `/skills` (debe listar `legal-audit` y/o
`legal-audit:legal-audit`) y `/agents` (debe listar los 4 subagentes, en el
plugin con prefijo `legal-audit:`). Probá delegar: "usá `legal-audit:code-scout`
para mapear los flujos de datos".

## Desinstalar

```bash
# Vía A:
/plugin uninstall legal-audit@legal-audit-marketplace   # dentro de una sesión
claude plugin marketplace remove legal-audit-marketplace  # quita el marketplace y su plugin

# Vía B:
rm ~/.claude/skills/legal-audit              # el symlink, no el repo
rm ~/.claude/agents/source-verifier.md \
   ~/.claude/agents/legal-researcher.md \
   ~/.claude/agents/code-scout.md \
   ~/.claude/agents/obligation-auditor.md
```

## Alternativa: instalador multi-agente `npx skills`

`npx skills` (Vercel Labs) es el instalador multi-agente emergente.
`[PENDIENTE: verificar]` la sintaxis exacta para un repo cuya skill está en un
subdirectorio; por eso documentamos los comandos nativos de Claude Code, que
sí están verificados contra la doc oficial.