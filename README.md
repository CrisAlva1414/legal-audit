# legal-audit

> **Auditoría estática de cumplimiento GDPR + Ley 21.719 con evidencia verificable.**

[PENDIENTE: nombre final] — el nombre `legal-audit` es el de trabajo por
defecto, pero puede cambiar antes del lanzamiento público.

`legal-audit` es una skill portable (OpenCode, Claude Code y Gemini CLI) que
analiza un repositorio de código y lo compara contra el Reglamento General de
Protección de Datos de la UE (GDPR) y la Ley 21.719 de Chile. Por cada
obligación aplicable emite un veredicto respaldado por evidencia
`archivo:línea`, tomada de un pack de fuentes legales congelado.

---

## Qué hace y qué NO hace

| Hace                                                                 | NO hace                                                                                         |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Escanea el código y mapea hallazgos a obligaciones GDPR / Ley 21.719 | **NO es asesoría jurídica.** No reemplaza a un abogado.                                         |
| Cita cada norma desde un pack de evidencia congelado y verificable   | **NO certifica cumplimiento.** No emite "cumple la ley".                                        |
| Reporta evidencia `archivo:línea` por hallazgo                       | **NO concluye anonimato.** No puede declarar que un dataset es anónimo (ver más abajo).         |
| Separa checks deterministas de los que requieren juicio humano       | **NO reemplaza una revisión humana ni un DPIA** (evaluación de impacto).                        |
| Marca vigencia de cada fuente (`FRESH` / `STALE` / `CHANGED`)        | **NO investiga en vivo.** El pack es congelado y reproducible; no consulta la web durante el run. |

### Sobre el anonimato

La herramienta **nunca** puede concluir que un conjunto de datos es anónimo. Un
análisis de anonimato depende de datasets externos, del contexto de uso y del
adversario considerado; es un test de tres partes (singling-out, linkability,
inference) y no se puede resolver por análisis estático del código. Por eso,
para cualquier pregunta de anonimato, el veredicto es siempre el especial
**`NO CONCLUIBLE ESTÁTICAMENTE`**.

---

## Instalación

Los ejemplos usan el placeholder `<owner>`; el owner real todavía no está
definido.

La instalación está documentada por cliente en
[`install/`](install/README.md) — los tres instalan la misma skill y los
mismos 4 subagentes, solo cambia el mecanismo:

- [OpenCode](install/opencode.md) — symlink de la skill + copia de subagentes
  a `~/.config/opencode/{skills,agents}/`.
- [Claude Code](install/claude.md) — plugin desde `adapters/claude/`
  (`claude plugin marketplace add ./adapters/claude` + `claude plugin install
  legal-audit@legal-audit-marketplace`), o symlink + copia directa.
- [Gemini CLI](install/gemini.md) — `gemini skills install <repo>.git --path
  skills/legal-audit --consent` + copia de subagentes a `~/.gemini/agents/`.

El detalle de la traducción por cliente (nombres de tools, directorios,
frontmatter) vive en [`adapters/`](adapters/README.md).

**Notas específicas de Gemini CLI:**

- Solo lee los campos `name` y `description` del frontmatter (ignora el resto).
- El descubrimiento de skills es de **un nivel de profundidad**: enlazá o
  instalá siempre el directorio `skills/legal-audit` (con `--path`), nunca la
  raíz del repo — al enlazar la raíz, `SKILL.md` queda dos niveles abajo y no
  se descubre. La estructura interna `references/` + `scripts/` es la anatomía
  esperada por Gemini, no anidamiento prohibido.
- Usa la tool `run_shell_command` en lugar de `bash`; los adaptadores de Gemini
  traducen esa diferencia.

---

## Arquitectura

```
                         ┌────────────────────────────────┐
                         │  skills/legal-audit/SKILL.md   │  ← capa portable
                         │  (agentskills.io: name/desc)   │     (estándar abierto)
                         │  + references/sources/         │
                         │  + references/obligations/     │
                         │  + scripts/                    │
                         └───────────────┬────────────────┘
                                         │ orquesta vía tool de subagente
        ┌───────────────┬────────────────┼────────────────┬──────────────────┐
        ▼               ▼                ▼                ▼
 ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────────────┐
 │ source-    │  │ legal-     │  │ code-scout │  │ obligation-       │
 │ verifier   │  │ researcher │  │            │  │ auditor           │
 └────────────┘  └────────────┘  └────────────┘  └───────────────────┘
        │               │                │                │
        └───────────────┴────────┬───────┴────────────────┘
                                  ▼
                    ┌──────────────────────────────┐
                    │ adapters/{opencode,claude,   │  ← capa de orquestación
                    │ gemini}/                     │     (no portable)
                    └──────────────────────────────┘
```

**Por qué está separado así.** La capa de *skill* es un estándar abierto
(agentskills.io): un `SKILL.md` con `name`, `description` y markdown. La capa
de *orquestación* **no** es estándar: el nombre de la tool de subagente cambia
según el agente — `task` en OpenCode, `Agent` en Claude Code, `@nombre` en
Gemini CLI. Mantener el `SKILL.md` canónico y tres adaptadores finos permite
compartir el 90% del contenido y aislar solo la traducción de cada motor.

**Qué contiene cada adaptador** (`adapters/{opencode,claude,gemini}/`):
instrucciones de instalación, el delta de frontmatter por motor, y — para
Claude Code — un marketplace + plugin válido que sirve los subagentes y la
skill por symlinks a la fuente única (`agents/` y `skills/`), sin copias. Ver
[`adapters/README.md`](adapters/README.md) para la tabla comparativa y la
regla de mantenimiento (los prompts viven en `skills/` y `agents/`; los
adaptadores solo traducen).

---

## El modelo de evidencia

La corrección jurídica no puede depender de la memoria del modelo. El modelo
tiene dos piezas:

1. **Pack de evidencia congelado** (`skills/legal-audit/references/sources/`).
   Cada norma se guarda con URL oficial, artículo, **cita textual**, fecha de
   vigencia y fecha de captura. El LLM cita ese pack; nunca redacta ley de
   memoria.
2. **Subagente `source-verifier`.** Re-chequea la vigencia e integridad de cada
   fuente y marca cada norma como `FRESH`, `STALE` o `CHANGED`. Su veredicto
   aparece en el reporte.

**Por qué no se investiga en vivo.** Una auditoría que consulta la web en
tiempo de ejecución no es reproducible: el mismo código puede dar resultados
distintos según lo que devuelva la red. Congelar las fuentes y verificar su
vigencia por separado hace que el resultado sea auditable y repetible.

---

## Escala de veredictos

| Veredicto         | Significado                                                                 |
| ----------------- | --------------------------------------------------------------------------- |
| `SATISFIED`       | La evidencia estática cubre la obligación de forma suficiente.              |
| `PARTIAL`         | Hay evidencia de cumplimiento, pero incompleta o con excepciones.          |
| `NOT_SATISFIED`   | La evidencia contradice la obligación o falta por completo.                 |
| `NOT_APPLICABLE`  | La obligación no aplica al contexto detectado (con justificación).          |
| `UNVERIFIABLE`    | No hay artefacto estático que permita decidir; requiere revisión humana.    |
| `PENDING_VIGENCIA`| La obligación existe pero aún no está en vigor (incluye la fecha).          |
| `NO CONCLUIBLE ESTÁTICAMENTE` | Veredicto obligatorio para cualquier pregunta de anonimato.     |

La skill **nunca** dice "cumple la ley". Emite veredictos por obligación, con
su evidencia, y deja explícito qué requiere juicio humano.

---

## Ejemplo de output

Ejemplo real, resumido: corrida E2E de `scan.py` contra `express` (que no
procesa PII). Las líneas citadas existen en el repo auditado.

```text
$ legal-audit scan ./express

Pack de evidencia: sources-2026-10-05 (hash 3f9c…a1b2)  ·  source-verifier: PASS
Detectores ejecutados: 6/6  ·  hallazgos: 365

OBL-030  [GDPR Art. 30 — ROPA / registros de tratamiento]
ESTADO        PARTIAL
EVIDENCIA     examples/auth/index.js:104   serialización de req.body hacia un
                                           sink HTTP (respuesta del login)
              History.md:3360              serialización de `user` hacia un
                                           sink http_sdk con destino posible
                                           externo
NOTA          El detector marcó por sintaxis (`body`, `user`, `send`) sobre
              documentación y código de ejemplo. Express no procesa PII: leer
              como ruido salvo revisión humana. Determinismo SEMI, techo PARTIAL.

OBL-020  [GDPR Art. 20 — portabilidad]
ESTADO        NOT_SATISFIED
EVIDENCIA     (ausencia) sin coincidencias para los patrones del derecho
NOTA          Hallazgo por ausencia del detector dsar_endpoints. Regla: la
              ausencia de hallazgo no es evidencia de ausencia — el detector
              no encontró el hecho que sabe mirar, y hay cosas que no mira.

OBL-006  [GDPR Art. 6 — base de licitud]
ESTADO        UNVERIFIABLE
EVIDENCIA     no hay artefacto estático que pruebe la base legal
NOTA          Obligación sin detector (22 de 39): va al obligation-auditor y
              requiere documentación del responsable del tratamiento.

ANONIMATO
ESTADO        NO CONCLUIBLE ESTÁTICAMENTE
NOTA          La identificabilidad depende de datasets externos, contexto y
              adversario. No se puede resolver por análisis estático.

Lo que esta auditoría NO puede concluir (resumen):
- que el código sea conforme o no a cada obligación sin evidencia directa;
- que un dataset sea anónimo (respuesta siempre NO CONCLUIBLE ESTÁTICAMENTE);
- la región real en runtime, qué datos se transfirieron de verdad, o si un
  DPA firmado existe y cubre el alcance.
```

> El reporte **nunca** incluye un resumen agregado: sin porcentajes, sin
> scores, sin conteos de obligaciones satisfechas (p. ej. "34/39 SATISFIED").
> Los conteos por detector o por jurisdicción son triage técnico, no un
> veredicto.

> Los veredictos del ejemplo están dentro del techo que el pack asigna a cada
> obligación; los artículos citados (Art. 30, Art. 20, Art. 6 del GDPR) son
> los reales del pack. El 365 no es una métrica de cumplimiento: es el ruido
> de los detectores heurísticos sobre un framework que no procesa PII (ver
> "Estado del proyecto").

---

## Estado del proyecto

**Alpha.** El pipeline completo está implementado y testeado, pero los
resultados no deben usarse para decisiones reales sin revisión humana.

- **Qué funciona hoy:** pack de evidencia congelado (6 fuentes, 39
  obligaciones con techo de veredicto), 6 detectores estáticos + `scan.py`,
  el `SKILL.md` orquestador, los 4 subagentes (`source-verifier`,
  `legal-researcher`, `code-scout`, `obligation-auditor`), 3 adaptadores
  (OpenCode, Claude Code, Gemini CLI), CI con verificación de integridad y
  **58 tests**.
- **Qué es alpha:**
  - Las fuentes son una **captura de fecha fija** (2026-10-05): hay que
    re-verificarlas con el `source-verifier` antes de cada uso (los DPAs, las
    listas de adecuación y las políticas de retención mutan en meses).
  - **22 de 39 obligaciones no tienen detector**; van a juicio del
    `obligation-auditor` y se listan como tales en el reporte, nunca se
    ocultan.
  - Los detectores son **heurísticos de sintaxis** y producen falsos
    positivos. Demostrado: la corrida E2E sobre `express` dio **365
    hallazgos**, la mayoría ruido sobre documentación (`History.md`,
    `Readme.md`) y código de ejemplo de un framework que no procesa PII.
  - La tabla de vendors (`references/sources/vendors.md`) es un **look-up
    estático**: documenta qué se verificó a la fecha de captura, no qué es
    verdad hoy.
- **Qué NO hace:** no es asesoría jurídica, no certifica cumplimiento y **no
  concluye anonimato** (toda pregunta de anonimato responde
  `NO CONCLUIBLE ESTÁTICAMENTE`).
- **Estado de la ley chilena:** las obligaciones de la Ley 21.719 se reportan
  `PENDING_VIGENCIA` hasta el **2026-12-01**, o **2027-12-01** si prospera el
  **Boletín 18.623-07** (en tramitación, no es ley todavía).

**Roadmap:** fuera de lo anterior, queda en roadmap el trabajo listado en
[`docs/roadmap.md`](docs/roadmap.md): detectores de vendors (transferencia sin
base, DPA, sub-procesadores, región, no-training) y la re-verificación
periódica del look-up. No está implementado y no se promete en esta versión.

---

## Disclaimer legal

`legal-audit` es una **herramienta informativa**. No constituye asesoría
jurídica ni presta servicios legales. Sus veredictos son automáticos, se basan
en análisis estático y en un pack de fuentes congelado, y pueden estar
desactualizados o ser incompletos.

El usuario es el único responsable de las determinaciones que tome a partir de
sus resultados. Antes de tomar cualquier decisión de cumplimiento, verificá
siempre el texto oficial vigente de la norma aplicable y consultá a un
profesional del derecho.

---

## Licencia

Apache-2.0. Ver `LICENSE`.

### Atribuciones

- **WP29 Opinion 05/2014 (WP216)** — documento de referencia de la UE
  (reutilización permitida con atribución). Referencia doctrinal para el
  análisis de anonimización.
- **EDPB Guidelines 01/2025** (pseudonimización) y **02/2026** (anonimización,
  borrador en consulta hasta 2026-10-30) — EUPL / dominio público de la UE.
  Referencia doctrinal; la de 2026 es un borrador.
- **CJEU C-413/23 P EDPS v SRB**, **C-582/14 Breyer**, **C-131/12 Google
  Spain** — documentos judiciales de la UE, reutilización permitida con
  atribución. Casos de referencia del análisis.
- **Texto oficial GDPR** (EUR-Lex CELEX 32016R0679) y **Ley 21.719** (BCN
  idNorma 1209272) — fuentes primarias citadas textualmente.
- **Privado** (LGPL-3.0) — solo como referencia de prior art. Sin código
  derivado en esta etapa.

Las URLs exactas de cada fuente y su cita textual se registran en el pack de
evidencia (`skills/legal-audit/references/sources/`) durante S2.
