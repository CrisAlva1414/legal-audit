# ePrivacy — Directiva 2002/58/EC (Pack de evidencia congelado)

## Vigencia de esta fuente
- **Fecha de captura:** 2026-10-05
- **Norma:** Directiva 2002/58/EC del Parlamento Europeo y del Consejo, de 12 de
  julio de 2002, relativa al tratamiento de los datos personales y a la
  protección de la intimidad en el sector de las comunicaciones electrónicas
  (versión consolidada CELEX `02002L0058-20091219`, tras la Directiva 2009/136/EC).
- **Estado:** vigente (texto consolidado de 19-12-2009).
- **Quién verifica:** subagente `source-verifier`

> **Por qué vive en archivo propio:** ePrivacy y GDPR son regímenes
> **acumulativos e independientes**. Art. 95 GDPR lo declara *lex specialis*.
> Una skill que los mezcle genera falsos negativos (p. ej. aceptar interés
> legítimo del Art. 6 GDPR como base para cookies).

## Índice
- [Directiva 2002/58/EC Art. 5(3)](#eprivacy--directiva-200258ec-art-53)
- [Por qué NO mapear 1:1 ePrivacy ↔ GDPR](#por-que-no-mapear-11-eprivacy--gdpr)

# Bloque 3 — ePrivacy

<a id="eprivacy--directiva-200258ec-art-53"></a>
## Directiva 2002/58/EC Art. 5(3) (consolidada tras 2009/136/EC)
- **Fuente:** CELEX **02002L0058-20091219** (`https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02002L0058-20091219`) **[VERIFICADO vía archivo]**. Texto vigente marcado “▼M2”.
- **Texto/cita:** *“Member States shall ensure that the storing of information, or the gaining of access to information already stored, in the terminal equipment of a subscriber or user is only allowed on condition that the subscriber or user concerned has given his or her consent, having been provided with clear and comprehensive information … This shall not prevent any technical storage or access for the sole purpose of carrying out the transmission of a communication … or as strictly necessary in order for the provider of an information society service explicitly requested by the subscriber or user to provide the service.”*
- **Independencia del GDPR:** GDPR **Art. 95** *“This Regulation shall not impose additional obligations … in relation to matters for which they are subject to specific obligations with the same objective set out in Directive 2002/58/EC.”* → Art. 5(3) es **lex specialis** y su consentimiento es **autónomo**: no se satisface con una base del Art. 6 GDPR (p. ej. interés legítimo).
- **Guía:** EDPB **Guidelines 2/2023 on Technical Scope of Art. 5(3)**, *16 October 2024*, *Final version v2.0* (`…/2024-10/edpb_guidelines_202302_technical_scope_art_53_eprivacydirective_v2_en_0.pdf`) **[VERIFICADO]**: *“Article 5(3) ePD applies if: (a) … the operations … relate to ‘information’ …; (b) … ‘terminal equipment’ of a subscriber or user …; (c) … ‘storage’ … or a ‘gaining of access’.”*
- **Se operacionaliza en:** inventario de cookies/SDKs/fingerprinting/almacenamiento en dispositivo; banner con consentimiento previo; exención solo para transmisión o servicio explícitamente solicitado.
- **Determinismo:** SEMI
- **Caveat:** el término es **“information”**, no “personal data”: Art. 5(3) aplica incluso a datos no personales almacenados en el terminal.

<a id="por-que-no-mapear-11-eprivacy--gdpr"></a>
## Por qué NO mapear 1:1 ePrivacy ↔ GDPR
- **Fuente:** Art. 5(3) ePD + GDPR Art. 95 (arriba) + EDPB 2/2023 §4: *“These Guidelines do not address the circumstances … exemptions from the consent requirement … as these circumstances should be analysed on a case-by-case basis…”* **[VERIFICADO]**.
- **Diferencias operativas:** (1) base legal distinta (consentimiento ePD, no bases del Art. 6); (2) alcance distinto (terminal equipment, no “personal data”); (3) exención *sandbox* limitada a transmisión/servicio solicitado.
- **Determinismo:** SEMI
- **Caveat:** una skill que aplique el balancing de interés legítimo del GDPR al banner/cookies genera **falsos negativos**. Son dos regímenes acumulativos.

---
