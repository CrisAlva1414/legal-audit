# Roadmap

## Slices pendientes

- [ ] **S2 — Pack de evidencia congelado.** Doctrina + fuentes en
      `skills/legal-audit/references/sources/`, cada norma con URL + artículo
      + cita textual + fecha de vigencia + fecha de captura.
- [ ] **S3 — Tabla de obligaciones.** Cada obligación con artículo, marca de
      determinismo (determinista / requiere juicio humano) y la evidencia que
      la satisface.
- [ ] **S4 — Detectores deterministas.** Scripts stdlib en
      `skills/legal-audit/scripts/` para los checks automatizables.
- [ ] **S5 — 4 subagentes.** `source-verifier`, `legal-researcher`,
      `code-scout`, `obligation-auditor`.
- [ ] **S6 — Adaptadores por agente + instalación.** Adaptadores finos para
      OpenCode, Claude Code y Gemini CLI, más instalación documentada.

## Ideas de research fuera de alcance (guardadas)

- **Fairness/WER para STT en castellano con voces infantiles.** El benchmark
  real es *On Top of Pasketti* (DrivenData), no COSER (que es de hablantes
  rurales mayores). Fuera de alcance de esta skill.
- **k-anonymity para heatmaps.** La supresión complementaria y el *disclosure
  by difference* permiten reconstruir celdas suprimidas. El framework
  recomendado es K-ambiguity o DP, no k-anonimidad sola.
- **Gobernanza y consentimiento.** Model cards, FRIA, ethics board, Consent
  Mode v2.
- **Opción A — Tags firmados + branch protection.** Disponible para cuando el
  proyecto crezca: anclar la integridad del pack a tags git firmados (GPG)
  con branch protection en `main`, reemplazando o reforzando el hash publicado
  en releases. Trade-off: firma criptográfica real contra manipulaciones, pero
  fricción de firma en cada contribución.
- **Crosswalk ISO/IEC 27701 ↔ Ley 21.719.** No existe un crosswalk oficial;
  construirlo requeriría trabajo normativo que excede este proyecto.

## Trabajo futuro — detectores de vendors (S6)

La tabla de proveedores en
`skills/legal-audit/references/sources/vendors.md` (captura 2026-10-05) es un
**look-up estático**: documenta qué se verificó a esa fecha, no qué es verdad
hoy. Hay que **re-verificarla** con `source-verifier` antes de cada uso (los
DPAs, listas de sub-procesadores y estados DPF mutan en meses). Detectores a
construir en S6 e integrar vía `obligations.json` (no se tocan en este slice):

- [ ] **Detector de transferencia sin base.** Proveedor fuera de la lista de
      adecuación o sin DPF activo → requiere SCCs + TIA.
- [ ] **Detector de DPA.** DPA ausente o no firmado (p. ej. Cohere solo NDA;
      DeepSeek sin DPA público).
- [ ] **Detector de sub-procesadores.** La cadena visible revela eslabones no
      contratados (Cloudflare AI Gateway, Datadog/Sentry, Azure "operated
      models", Bedrock `provider_data_share`).
- [ ] **Detector de región.** Región declarada en config vs regiones en que el
      proveedor puede procesar (Azure Global/DataZone, "Global inference" de
      Alibaba).
- [ ] **Detector de no-training.** Flag de training/fine-tuning habilitado en
      config → el proveedor deja de ser encargado para esa finalidad.
- [ ] **Re-verificación del look-up.** El inventario no es evidencia de que un
      contrato exista hoy; cada reporte declara el hash del pack usado
      (`SOURCES.sha256`).
