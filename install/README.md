# Instalación

Elegí tu cliente y seguí el archivo correspondiente. Todos los comandos se
corren desde la raíz del repo clonado de `legal-audit`. El `<owner>` de las
URLs todavía no está definido `[PENDIENTE: owner real del repo en GitHub]`;
usá tu fork/org si instalás desde git.

| Cliente | Guía | Qué instala |
|---|---|---|
| [OpenCode](./opencode.md) | symlink de skill + copia de subagentes | `legal-audit` como skill, 4 subagentes como tools |
| [Claude Code](./claude.md) | plugin desde `adapters/claude/` (o symlink + copia) | skill + 4 subagentes (en plugin, prefijo `legal-audit:`) |
| [Gemini CLI](./gemini.md) | `gemini skills install --path` + copia de subagentes | skill + 4 subagentes invocables con `@nombre` |

Los tres instalan **la misma skill y los mismos 4 subagentes**; solo cambia el
mecanismo. El detalle de la traducción por cliente está en
[`adapters/`](../adapters/README.md).

## Resumen de un comando clave por cliente

- **OpenCode:** `ln -s "$(pwd)/skills/legal-audit" ~/.config/opencode/skills/legal-audit`
- **Claude Code:** `claude plugin install legal-audit@legal-audit-marketplace`
  (tras `claude plugin marketplace add ./adapters/claude`)
- **Gemini CLI:** `gemini skills install <url-del-repo>.git --path skills/legal-audit --consent`

## Verificación transversal

La skill está verificada por su propio pack: `verify_pack.py` exit 0 y 58
tests (`python3 -m unittest discover -s tests`). Si instalás por symlink,
cualquier `git pull` del repo actualiza la skill sin reinstalar.