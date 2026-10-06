# Instalación en OpenCode

Instala la **skill** (`skills/legal-audit/`) y los **4 subagentes** (`agents/`).
Los comandos se corren desde la raíz del repo clonado de `legal-audit`.

## 1. Skill

```bash
mkdir -p ~/.config/opencode/skills
ln -s "$(pwd)/skills/legal-audit" ~/.config/opencode/skills/legal-audit
```

El symlink es la vía recomendada: cualquier `git pull` del repo actualiza la
skill sin reinstalar. OpenCode descubre skills en
`~/.config/opencode/skills/<name>/SKILL.md`
([doc](https://opencode.ai/docs/skills/)) y respeta el symlink.

## 2. Subagentes

```bash
mkdir -p ~/.config/opencode/agents
cp agents/*.md ~/.config/opencode/agents/
```

Los 4 archivos canónicos ya tienen el frontmatter `name` + `description` que
OpenCode necesita; se copian sin modificar. (Alternativa legacy: el directorio
singular `~/.config/opencode/agent/`.)

## 3. (Opcional) `opencode.json.snippet`

Mirá [`opencode.json.snippet`](./opencode.json.snippet) si querés fijar
permisos explícitos de la skill o exponer los scripts en el PATH. **No es
requisito**: el descubrimiento de skills y agentes es por convención de
directorio.

## Verificar que quedó bien

```bash
ls -l ~/.config/opencode/skills/legal-audit/SKILL.md   # symlink → repo
ls -1 ~/.config/opencode/agents/                        # 4 subagentes
```

Dentro de OpenCode, pedí: "listá tus skills" (debe aparecer `legal-audit`) y
"usá el agente `obligation-auditor`" (debe delegar).

## Desinstalar

```bash
rm ~/.config/opencode/skills/legal-audit
rm ~/.config/opencode/agents/source-verifier.md \
   ~/.config/opencode/agents/legal-researcher.md \
   ~/.config/opencode/agents/code-scout.md \
   ~/.config/opencode/agents/obligation-auditor.md
```

(El `rm` sobre el symlink de la skill no toca el repo.)

## Alternativa: instalador multi-agente `npx skills`

El README histórico menciona `npx skills add <owner>/legal-audit -a opencode`
(Vercel Labs) como instalador multi-agente. `[PENDIENTE: verificar]` — no
pudimos confirmar contra la doc oficial del instalador la sintaxis exacta para
un repo cuya skill está en `skills/legal-audit/` (subdirectorio), así que la
vía de symlink/copy de arriba es la recomendada y verificada.