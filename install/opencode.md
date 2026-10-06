# Instalación en OpenCode

> Comandos verificados contra https://opencode.ai/docs/skills/. Corré todo
> desde la raíz del repo clonado de `legal-audit`. El `<owner>` no está
> definido todavía `[PENDIENTE: owner real del repo en GitHub]`: usá tu
> fork/org.

## Qué se instala

1. **La skill** `skills/legal-audit/` → visible por OpenCode como `legal-audit`
   (skill de auditoría GDPR + Ley 21.719).
2. **Los 4 subagentes** (`source-verifier`, `legal-researcher`, `code-scout`,
   `obligation-auditor`) → invocables por OpenCode como herramientas.

## Archivos y destinos

| Origen | Destino | Modo |
|---|---|---|
| `skills/legal-audit/` | `~/.config/opencode/skills/legal-audit/` | symlink |
| `agents/*.md` (4) | `~/.config/opencode/agents/*.md` | copia |

## Comandos

```bash
# 1. Skill (symlink → los cambios del repo se reflejan al toque)
mkdir -p ~/.config/opencode/skills
ln -s "$(pwd)/skills/legal-audit" ~/.config/opencode/skills/legal-audit

# 2. Subagentes
mkdir -p ~/.config/opencode/agents
cp agents/*.md ~/.config/opencode/agents/
```

Opcional: `adapters/opencode/opencode.json.snippet` para permisos explícitos.

## Verificar

```bash
ls -l ~/.config/opencode/skills/legal-audit/SKILL.md    # existe y es symlink
ls -1 ~/.config/opencode/agents/                        # 4 archivos
```

En una sesión de OpenCode: preguntá "listá tus skills" (debe aparecer
`legal-audit`) y pedí "usá el agente `code-scout`" para confirmar la
delegación.

## Desinstalar

```bash
rm ~/.config/opencode/skills/legal-audit
rm ~/.config/opencode/agents/source-verifier.md \
   ~/.config/opencode/agents/legal-researcher.md \
   ~/.config/opencode/agents/code-scout.md \
   ~/.config/opencode/agents/obligation-auditor.md
```

## Notas

- El symlink de skill es la vía recomendada (actualización automática al
  `git pull`); `npx skills add <owner>/legal-audit -a opencode` (Vercel Labs)
  es el instalador multi-agente emergente, `[PENDIENTE: verificar]` su
  sintaxis exacta para skills en subdirectorio.
- Detalle de qué copiar y por qué no se duplican los subagentes:
  [`adapters/opencode/agents/README.md`](../adapters/opencode/agents/README.md).