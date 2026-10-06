# Instalación en Gemini CLI

Instala la **skill** (`skills/legal-audit/`) y los **4 subagentes** (`agents/`).
Comandos verificados contra la doc oficial de Gemini CLI
([skills](https://geminicli.com/docs/cli/skills), [creating-skills](https://geminicli.com/docs/cli/creating-skills)).

## 1. Skill — instalación desde git

```bash
gemini skills install https://github.com/<owner>/legal-audit.git \
  --path skills/legal-audit --consent
```

- `--path skills/legal-audit` es **obligatorio** en este repo: la doc define
  `--path` como "el sub-directorio dentro del repositorio git que contiene la
  skill", y la skill de legal-audit no está en la raíz del repo.
- `--consent` saltea la confirmación de seguridad del instalador.

## 2. Skill — enlace local (desarrollo)

Desde la raíz del repo:

```bash
gemini skills link skills/legal-audit
```

o, equivalente y más explícito:

```bash
cd skills/legal-audit && gemini skills link .
```

> **Restricción de profundidad (verificada).** Gemini CLI descubre skills como
> `<raíz-de-skills>/<nombre>/SKILL.md` — un nivel de anidamiento. Nuestra
> estructura `skills/legal-audit/SKILL.md` **calza** siempre que el punto de
> enlace/instalación sea `skills/legal-audit` (con `--path` o `gemini skills
> link skills/legal-audit`). Lo que **no** calza es enlazar la **raíz del
> repo**: ahí `SKILL.md` quedaría dos niveles abajo
> (`<raíz>/skills/legal-audit/SKILL.md`) y el descubrimiento no la encontraría.
> No hace falta aplanar la estructura; hace falta apuntar al directorio de la
> skill. La doc de Gemini recomienda explícitamente que el skill tenga
> `references/` y `scripts/` como subdirectorios internos — eso no es
> "anidamiento", es la anatomía esperada de un skill.

## 3. Subagentes

```bash
mkdir -p ~/.gemini/agents
cp agents/*.md ~/.gemini/agents/
```

Se invocan por su `name` del frontmatter con `@`: `@source-verifier`,
`@legal-researcher`, `@code-scout`, `@obligation-auditor`.

## 4. Verificar que quedó bien

```bash
gemini skills list --all                 # debe aparecer legal-audit
ls -1 ~/.gemini/agents/                  # 4 subagentes
```

En una sesión:

```
/skills list all         # lista las skills descubiertas
/skills reload           # si acabás de instalarla y la sesión estaba abierta
@code-scout Mapeá los flujos de datos de este repositorio
```

## 5. Desinstalar

```bash
gemini skills uninstall legal-audit --scope user
rm ~/.gemini/agents/source-verifier.md \
   ~/.gemini/agents/legal-researcher.md \
   ~/.gemini/agents/code-scout.md \
   ~/.gemini/agents/obligation-auditor.md
```

(Si instalaste la skill por `gemini skills link`, el uninstall quita el
enlace; si la instalaste por `install`, borra la carpeta copiada.)

## Alternativa: instalador multi-agente `npx skills`

`npx skills` (Vercel Labs) es el instalador multi-agente emergente.
`[PENDIENTE: verificar]` la sintaxis exacta para un repo cuya skill está en un
subdirectorio; los comandos nativos de Gemini de arriba están verificados
contra la doc oficial.