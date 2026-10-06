# Instalación en Gemini CLI

> Comandos verificados contra https://geminicli.com/docs/cli/skills y
> https://geminicli.com/docs/cli/creating-skills. Corré todo desde la raíz del
> repo clonado de `legal-audit`. El `<owner>` no está definido todavía
> `[PENDIENTE: owner real del repo en GitHub]`.

## Qué se instala

1. **La skill** `skills/legal-audit/` (Gemini lee `name` y `description` del
   frontmatter; ignora el resto).
2. **Los 4 subagentes** (`source-verifier`, `legal-researcher`, `code-scout`,
   `obligation-auditor`), invocables con `@nombre`.

## 1. Skill — desde git

```bash
gemini skills install https://github.com/<owner>/legal-audit.git \
  --path skills/legal-audit --consent
```

`--path skills/legal-audit` es obligatorio: la skill no está en la raíz del
repo. `--consent` saltea la confirmación de seguridad.

## 2. Skill — enlace local (desarrollo)

```bash
gemini skills link skills/legal-audit
# o:  cd skills/legal-audit && gemini skills link .
```

> **Profundidad:** enlazá siempre el directorio `skills/legal-audit`, nunca la
> raíz del repo — al enlazar la raíz, `SKILL.md` queda dos niveles abajo y el
> descubrimiento de Gemini (un nivel) no la encuentra. La estructura interna
> `references/` + `scripts/` es la anatomía esperada por Gemini, no
> anidamiento prohibido.

## 3. Subagentes

```bash
mkdir -p ~/.gemini/agents
cp agents/*.md ~/.gemini/agents/
```

## Destinos

| Origen | Destino | Modo |
|---|---|---|
| `skills/legal-audit/` | `~/.gemini/skills/legal-audit/` | `install --path` o `link` |
| `agents/*.md` (4) | `~/.gemini/agents/*.md` | copia |

## Verificar

```bash
gemini skills list --all        # debe aparecer legal-audit
ls -1 ~/.gemini/agents/         # 4 subagentes
```

En sesión:

```
/skills list all
/skills reload                  # si la sesión estaba abierta al instalar
@code-scout Mapeá los flujos de datos de este repositorio
```

## Desinstalar

```bash
gemini skills uninstall legal-audit --scope user
rm ~/.gemini/agents/source-verifier.md \
   ~/.gemini/agents/legal-researcher.md \
   ~/.gemini/agents/code-scout.md \
   ~/.gemini/agents/obligation-auditor.md
```

## Notas

- Los subagentes de Gemini **no pueden invocarse entre sí**; la orquestación
  la hace el agente principal (ver
  [`adapters/gemini/agents/gemini-agents.md`](../adapters/gemini/agents/gemini-agents.md)).
- `npx skills` (Vercel Labs) es el instalador multi-agente emergente;
  `[PENDIENTE: verificar]` la sintaxis exacta para skills en subdirectorio.