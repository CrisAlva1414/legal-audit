# Bibliografía

Registro navegable de las fuentes del pack. Cada entrada declara **qué se usa**,
**en qué archivo del pack aparece** y su **estado**. Las afirmaciones legales se
emiten solo desde las fuentes `VERIFICADO`; las `BORRADOR`, `INDIRECTA` y
`NO VERIFICADO` se citan con esa marca y no sostienen por sí solas un veredicto
(ver `doctrine.md`).

Leyenda de estado: `VERIFICADO` (texto leído contra fuente oficial) ·
`VERIFICADO_PARCIAL` (texto verificado, faltan metadatos de la fuente: ECLI,
fecha exacta, sala) · `INDIRECTA` (dato tomado de fuente secundaria, texto
primario no accedido) · `BORRADOR` (documento en consulta, no derecho vigente)
· `NO VERIFICADO` (mencionado pero no capturado/leído en el pack).

## Índice
- [Fuentes primarias (normas)](#bib-primarias)
- [Jurisprudencia](#bib-jurisprudencia)
- [Guías de autoridad](#bib-guias)
- [Estándares](#bib-estandares)
- [Fuentes de terceros (vendors)](#bib-vendors)
- [Prior art](#bib-prior)
- [Fuentes fuera de alcance](#bib-fuera-alcance)

<a id="bib-primarias"></a>
## Fuentes primarias (normas)

| Fuente | Qué se usa | Dónde aparece | Estado |
|---|---|---|---|
| **GDPR** — Reglamento (UE) 2016/679, CELEX `32016R0679`, OJ L 119, 4.5.2016 | Núcleo UE: definiciones, principios, bases, derechos, seguridad, brechas, DPIA, transferencias, identificabilidad. | `sources/gdpr.md` | `VERIFICADO` (texto OJ L 119 vía PDF oficial archivado; URL en vivo devolvió HTTP 202 el 2026-10-05) |
| **Directiva 2002/58/CE consolidada** — CELEX `02002L0058-20091219` (tras 2009/136/EC) | Régimen ePrivacy acumulativo e independiente; Art. 5(3) (terminal equipment). | `sources/eprivacy.md` | `VERIFICADO` |
| **Decisión de Ejecución (UE) 2021/914** (SCC), 4.6.2021, OJ L 199/31 | Cláusulas contractuales tipo del Art. 46 GDPR; cuatro módulos. | `sources/gdpr.md` | `VERIFICADO` |
| **Ley 19.628 (mod. Ley 21.719)** — BCN idNorma `1209272`, versión `2026-12-01` | Núcleo Chile: consentimiento, bases, información, DPIA, sensibles, biometría, NNA, derechos, brechas, seguridad, transferencias, sanciones. | `sources/chile-21719.md` | `VERIFICADO` |
| **Ley 21.806** — D.O. 05-02-2026, BCN idNorma `1221118` | Modifica el Art. cuarto transitorio de la Ley 21.719 (plazos de implementación/Consejo). | `sources/chile-21719.md` | `VERIFICADO` |
| **Decreto 12** — BCN idNorma `1214293`, 17-jun-2025 | Crea la Comisión Asesora Ministerial para la implementación de la Ley 21.719 (4 informes, ene-2026; sin criterios vinculantes de anonimización). | `sources/chile-eu-crosswalk.md` | `VERIFICADO` (existencia y objeto; articulado no leído completo) |
| **Resolución 1400 exenta CGR** — BCN idNorma `1225450`, D.O. 24-jun-2026 | Procedimiento interno de la Contraloría para Arts. 54–55; no es directriz general. | `sources/chile-eu-crosswalk.md` | `VERIFICADO` |
| **Decisión de Ejecución (UE) 2026/179** (adecuación Brasil), 26-ene-2026, DOUE L 28-01-2026 | Contraste: Brasil sí tiene adecuación UE; Chile no. | `sources/chile-eu-crosswalk.md` | `VERIFICADO` |

<a id="bib-jurisprudencia"></a>
## Jurisprudencia

| Fuente | Ratio (una línea) | Qué check justifica | Dónde aparece | Estado |
|---|---|---|---|---|
| **C-413/23 P — EDPS v Single Resolution Board** (Primera Sala, 2025-09-04, ECLI:EU:C:2025:645) | Una identificación no es "razonablemente probable" si el riesgo es insignificante en la realidad. | Check de **tabla de mapping separada** del dataset pseudonimizado (parr. 75/82/86). | `sources/gdpr.md` | `VERIFICADO` |
| **C-582/14 — Breyer v Bundesrepublik Deutschland** | La IP dinámica registrada por un operador web es dato personal si este tiene medios legales de cruzarla con datos del ISP. | IP/online identifiers tratados como dato personal frente al operador. **NO es el caso del derecho al olvido.** | `sources/gdpr.md` | `VERIFICADO_PARCIAL` — texto verificado; faltan ECLI / fecha exacta / sala. **`[PENDIENTE: no extraído de la fuente]`** |
| **C-131/12 — Google Spain** | La desindexación ordenada a un buscador no exige el borrado previo en la página fuente. | Check de supresión: distinguir **borrar en la fuente** de **desindexar**. | `sources/gdpr.md` | `VERIFICADO_PARCIAL` — texto verificado; faltan ECLI / fecha exacta / sala. **`[PENDIENTE: no extraído de la fuente]`** |

<a id="bib-guias"></a>
## Guías de autoridad

| Fuente | Qué se usa | Dónde aparece | Estado |
|---|---|---|---|
| **WP29 Opinion 05/2014 (WP216)** — Anonymisation Techniques | Fallos de k-anonymity, l-diversity, riesgos singling-out/linkability/inference. | `sources/gdpr.md` | `VERIFICADO` (37 pág.) |
| **WP248** — criterios de DPIA | Lista orientativa de 9 criterios para "alto riesgo" (Art. 35 GDPR). | `sources/gdpr.md` (mención en Art. 35) | `NO VERIFICADO` — referenciada, texto no capturado |
| **EDPB Guidelines 01/2025 on Pseudonymisation** | Separación de la *additional information*; control de acceso a claves/tablas. | `sources/gdpr.md` | `BORRADOR` — versión de consulta 16-01-2025; **sin versión final verificada a 2026-10-05** |
| **EDPB Guidelines 02/2026 on Anonymisation** | Enfoque relativo; riesgo de identificación no nulo pero "insignificante". | `sources/gdpr.md` | `BORRADOR` — **consulta cierra 2026-10-30**; no es derecho vigente |
| **EDPB Guidelines 05/2020 on Consent** | Estándares de consentimiento libre/específico/informado/inequívoco. | no capturada en el pack actual | `NO VERIFICADO` — referencia pendiente para S3 |
| **EDPB Guidelines 4/2019 v2.0 (DPbDD)** — Art. 25 | Protección por diseño y por defecto. | `sources/gdpr.md` | `VERIFICADO` |
| **EDPB Guidelines 2/2023 v2.0** — alcance técnico del Art. 5(3) ePrivacy | Alcance de "information", "terminal equipment", "storage/access". | `sources/eprivacy.md` | `VERIFICADO` |
| **EDPB Guidelines 9/2022 v2.0** — notificación de brechas | Criterios de riesgo y contenido de la notificación. | `sources/gdpr.md` | `VERIFICADO` |

<a id="bib-estandares"></a>
## Estándares

| Fuente | Qué se usa | Dónde aparece | Estado |
|---|---|---|---|
| **ISO/IEC 27701:2025 Ed.2** — Anexo D informativo | Crosswalk a GDPR Arts. 5–35 y 44–49 (excluye 36–43). | `sources/chile-eu-crosswalk.md` | `INDIRECTA` — texto de pago, no accedido |

<a id="bib-vendors"></a>
## Fuentes de terceros (vendors)

Registro de las fuentes externas del inventario de proveedores
(`sources/vendors.md`): policies, DPAs y listas de sub-procesadores oficiales.
Captura **2026-10-05**; son fuentes que **mutan en meses** y el
`source-verifier` debe re-consultarlas antes de cada uso. Ninguna se cita como
texto normativo capturado: se referencian como **inventario externo** (ver
`doctrine.md`, jerarquía de evidencia — rango 4/5, análisis de tercero
reputado; y `sources/vendors.md`, cabecera de vigencia).

| Fuente (URL oficial) | Qué se usa | Estado |
|---|---|---|
| Cloudflare — lista de sub-procesadores (`cloudflare.com/cloudflare_subprocessors/`) | Cadena AI Gateway → Anthropic/OpenAI/xAI/Groq/CoreWeave | VERIFICADO (captura 2026-10-05; re-consultar URL) |
| Datadog — lista de sub-procesadores (`datadoghq.com/legal/subprocessors/`) | Anthropic/OpenAI en servicios AI/ML | VERIFICADO |
| Sentry — DPA (`sentry.io/legal/dpa/`) | Anthropic/OpenAI como sub-procesadores | VERIFICADO |
| Microsoft DPA (`microsoft.com/licensing/docs/view/Microsoft-Products-and-Services-Data-Protection-Addendum-DPA`) | Azure "OpenAI operated models": OpenAI como sub-procesador | VERIFICADO (URL del anexo: A VERIFICAR) |
| AWS Bedrock — documentación de `provider_data_share` | Flag que decide transferencia a Anthropic; retención 30 días | VERIFICADO (URL exacta: A VERIFICAR) |
| AssemblyAI — legal (`assemblyai.com/legal`) | LLM Gateway vía Bedrock con ZDR | VERIFICADO (URL exacta: A VERIFICAR) |
| Comisión Europea — lista de adecuación (Art. 45) | Mapa 2026 de países adecuados | VERIFICADO |
| DPF — registro oficial (EEUU) | Membresía activa y cobertura por empresa | VERIFICADO (verificado 4-oct-2026) |
| Diario Oficial Chile — cláusulas contractuales modelo (19-dic-2025) | Vía de salvaguarda Chile para transferencias | VERIFICADO |
| Garante italiano — provvedimento 10098477 (30-ene-2025) | Bloqueo de DeepSeek | VERIFICADO |

**Categorías de proveedor cubiertas por `sources/vendors.md`:**
`llm` · `stt` · `idp` · `infra` · `observabilidad` · `pagos` · `chino`

<a id="bib-prior"></a>
## Prior art

| Fuente | Qué se usa | Dónde aparece | Estado |
|---|---|---|---|
| **Privado** (LGPL-3.0) | Solo *data-flow*; **no cubre obligaciones sustantivas**. Sin código derivado en esta etapa. | `README.md` (atribuciones) | `VERIFICADO` (atribución) — no capturado en el pack |
| **Binder et al. 2024** — Springer, DOI `10.1007/978-3-031-82349-7_11` | Antecedente académico de análisis legal automatizado. | no en el pack | `NO VERIFICADO` |
| **Bonatti et al. 2020** — H2020 SPECIAL, arXiv:2001.08930 | Antecedente de razonamiento sobre cumplimiento. | no en el pack | `NO VERIFICADO` |

> **Nicho del proyecto:** ninguna de las fuentes de prior art cubre el
> **crosswalk UE + Chile** (GDPR ↔ Ley 19.628 mod. 21.719). Ese cruce es el
> diferencial de `legal-audit`.

<a id="bib-fuera-alcance"></a>
## Fuentes fuera de alcance

> Estas fuentes quedan **registradas para consultas futuras**, pero **no son
> evidencia normativa** de este pack: no sostienen veredictos ni se citan como
> soporte de afirmaciones legales (ver `doctrine.md`, jerarquía de evidencia).

| Fuente | Qué se usa | Dónde aparece | Estado |
|---|---|---|---|
| **ITU-T P.800 / P.808 (MOS)** | Medición de calidad subjetiva del habla para evaluar STT. | no capturada en el pack actual | `NO VERIFICADO` |
| **ISO/IEC 19795-1** | **Aclaración: NO es estándar de ASR.** Es testing de rendimiento de sistemas biométricos. | no capturada en el pack actual | `NO VERIFICADO` |
| **On Top of Pasketti** (DrivenData) | Benchmark de referencia para **ASR infantil** (voces de menores). | `docs/roadmap.md` | `NO VERIFICADO` — link no capturado en el pack |
| **COSER** | **No sirve para ASR infantil**: es de hablantes rurales mayores. Se registra solo como descarte. | `docs/roadmap.md` | `NO VERIFICADO` |
