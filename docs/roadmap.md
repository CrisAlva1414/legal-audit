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
