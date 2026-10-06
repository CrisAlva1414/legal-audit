# Subagentes de legal-audit en OpenCode

Los **4 subagentes** de legal-audit viven en `agents/` en la raíz del repo
(fuente única):

| Subagente | Archivo canónico | Rol |
|---|---|---|
| `source-verifier` | [`../../agents/source-verifier.md`](../../agents/source-verifier.md) | Único con red: verifica vigencia de fuentes (FRESH/STALE/CHANGED) |
| `legal-researcher` | [`../../agents/legal-researcher.md`](../../agents/legal-researcher.md) | Investigación puntual fuera del pack (nota, nunca evidencia) |
| `code-scout` | [`../../agents/code-scout.md`](../../agents/code-scout.md) | Mapas técnico y de flujos de datos (no juzga) |
| `obligation-auditor` | [`../../agents/obligation-auditor.md`](../../agents/obligation-auditor.md) | Veredictos por obligación con techo de determinismo |

## Qué copiar y a dónde

**Se copian tal cual** — OpenCode lee el frontmatter `name` + `description`
(que es todo lo que los archivos canónicos declaran) y el body como system
prompt. No hace falta adaptar nada:

```bash
mkdir -p ~/.config/opencode/agents
cp ../../agents/*.md ~/.config/opencode/agents/
```

Rutas válidas en OpenCode:

- **Global (recomendado):** `~/.config/opencode/agents/*.md`
- **Global legacy (singular):** `~/.config/opencode/agent/*.md` — ruta
  histórica; preferí la plural si tu versión la soporta.
- **Proyecto:** `.opencode/agents/*.md` (si querés auditarlos solo en un repo).

## Por qué no duplicamos los subagentes

Este adaptador **enlaza a los canónicos** (`../../agents/*.md`) en lugar de
copiar su contenido. Si copiáramos, habría dos versiones de cada prompt: la
del repo y la del adaptador, y cualquier corrección de prompt (p. ej. un
endurecimiento de seguridad) quedaría desincronizada — drift garantizado. La
regla de mantenimiento es: **los prompts viven en `agents/`; los adaptadores
solo traducen el mecanismo de invocación.** Si un `agents/*.md` necesita un
cambio solo para OpenCode, es señal de que el prompt canónico está mal
escrito (se está acoplando a un motor).

## Verificar

```bash
ls -la ~/.config/opencode/agents/            # 4 archivos .md
python3 -m unittest tests.test_prompt_invariants  # portabilidad intacta
```

Dentro de una sesión de OpenCode, pedile que liste los agentes disponibles o
invocá directamente: "usá el agente `code-scout` para mapear el repo".