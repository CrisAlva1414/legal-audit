# Índice de obligaciones

Generado mecánicamente por `scripts/build_obligations.py` a partir de
las fichas estructuradas de `references/sources/` (gdpr.md, eprivacy.md,
chile-21719.md). No editar a mano: se regenera con el script.

`obligations.json` es la fuente de verdad para los detectores.

Total: 39 fichas (GDPR 24 · ePrivacy 1 · Chile 14).

- Un `determinismo` compuesto (p. ej. 
  `DETERMINISTA en estructura ..., SEMI en suficiencia`) se muestra en
  la tabla como su determinismo principal (`determinismo_principal`).
- `diferencia_con_gdpr` es `null` en las fichas UE por definición: son
  el lado de referencia; la comparación con Chile vive en
  `sources/chile-eu-crosswalk.md`.
- El `techo_de_veredicto` es el máximo que doctrine.md permite para el
  determinismo de la ficha: un `JUICIO` o `NO-VERIFICABLE-ESTATICAMENTE`
  nunca puede emitir `SATISFIED` (regla del techo de veredicto).

| id | jurisdicción | artículo | título | determinismo | techo | responsable |
|----|--------------|----------|--------|--------------|-------|-------------|
| gdpr-art-4 | UE | Art. 4 | Definiciones relevantes | SEMI | PARTIAL | AMBOS |
| gdpr-art-5 | UE | Art. 5 | Principios (incl. 5(1)(e) y 5(2)) | DETERMINISTA | SATISFIED | DETECTOR |
| eprivacy-art-5-3 | UE | Art. 5(3) | (consolidada tras 2009/136/EC) | SEMI | PARTIAL | AMBOS |
| gdpr-art-6 | UE | Art. 6 | Bases legales | SEMI | PARTIAL | AMBOS |
| gdpr-art-7 | UE | Art. 7 | Condiciones del consentimiento | SEMI | PARTIAL | AMBOS |
| gdpr-art-8 | UE | Art. 8 | Consentimiento de menores | SEMI | PARTIAL | AMBOS |
| gdpr-art-9 | UE | Art. 9 | Categorías especiales (voz/biometría) | SEMI | PARTIAL | AMBOS |
| gdpr-art-12 | UE | Art. 12 | Transparencia y modalidades | SEMI | PARTIAL | AMBOS |
| gdpr-art-13-14 | UE | Arts. 13 y 14 | Contenido de la información | SEMI | PARTIAL | AMBOS |
| gdpr-art-15 | UE | Art. 15 | Derecho de acceso | DETERMINISTA | SATISFIED | DETECTOR |
| gdpr-art-16 | UE | Art. 16 | Rectificación | DETERMINISTA | SATISFIED | DETECTOR |
| gdpr-art-17 | UE | Art. 17 | Supresión (“derecho al olvido”) | DETERMINISTA | SATISFIED | DETECTOR |
| gdpr-art-18 | UE | Art. 18 | Limitación del tratamiento | SEMI | PARTIAL | AMBOS |
| gdpr-art-20 | UE | Art. 20 | Portabilidad | DETERMINISTA | SATISFIED | DETECTOR |
| gdpr-art-21 | UE | Art. 21 | Oposición | DETERMINISTA | SATISFIED | DETECTOR |
| gdpr-art-22 | UE | Art. 22 | Decisiones automatizadas | SEMI | PARTIAL | AMBOS |
| gdpr-art-25 | UE | Art. 25 | Protección por diseño y por defecto | JUICIO | PARTIAL | JUICIO-HUMANO |
| gdpr-recital-26 | UE | Recital 26 | Identificabilidad / pseudonimización | NO-VERIFICABLE-ESTATICAMENTE | NO_CONCLUIBLE_ESTATICAMENTE | JUICIO-HUMANO |
| gdpr-art-28 | UE | Art. 28 | Encargado | DETERMINISTA | SATISFIED | DETECTOR |
| gdpr-art-30 | UE | Art. 30 | Registro de actividades (ROPA) | DETERMINISTA | SATISFIED | DETECTOR |
| gdpr-art-32 | UE | Art. 32 | Seguridad del tratamiento | SEMI | PARTIAL | AMBOS |
| gdpr-art-33-34 | UE | Art. 33 y 34 | Brechas | DETERMINISTA | SATISFIED | DETECTOR |
| gdpr-art-35-36 | UE | Arts. 35 y 36 | DPIA y consulta previa | SEMI | PARTIAL | AMBOS |
| gdpr-art-44-49 | UE | Arts. 44–49 | Transferencias internacionales | SEMI | PARTIAL | AMBOS |
| gdpr-recital-71-art-4 | UE | Recital 71 + Art. 4(4) | Scoring/profiling (corrección del brief) | SEMI | PARTIAL | AMBOS |
| cl-barsop | CL | Arts. 5, 6, 7, 8, 8° bis, 8° ter, 9 | Catálogo de derechos (BARSOP) | DETERMINISTA | SATISFIED | DETECTOR |
| cl-8-bis | CL | Art. 8° bis | Decisiones individuales automatizadas | SEMI | PARTIAL | AMBOS |
| cl-8-ter | CL | Art. 8° ter | Derecho de bloqueo (la "B" de BARSOP) | DETERMINISTA | SATISFIED | DETECTOR |
| cl-12 | CL | Art. 12 | Regla general del tratamiento / consentimiento | SEMI | PARTIAL | AMBOS |
| cl-13 | CL | Art. 13 | Otras fuentes de licitud | SEMI | PARTIAL | AMBOS |
| cl-14-ter | CL | Art. 14 ter | Deber de información y transparencia (política de tratamiento) | DETERMINISTA | SATISFIED | DETECTOR |
| cl-14-quater-14-quinquies | CL | Arts. 14 quáter y 14 quinquies | Seguridad, diseño y cifrado | DETERMINISTA | SATISFIED | DETECTOR |
| cl-14-sexies | CL | Art. 14 sexies | Notificación de brechas | SEMI | PARTIAL | AMBOS |
| cl-15-ter | CL | Art. 15 ter | Evaluación de impacto (DPIA) | SEMI | PARTIAL | AMBOS |
| cl-16 | CL | Art. 16 | Datos personales sensibles | SEMI | PARTIAL | AMBOS |
| cl-16-ter | CL | Art. 16 ter | Datos personales biométricos (voz) | SEMI | PARTIAL | AMBOS |
| cl-16-quater | CL | Art. 16 quáter | Niños, niñas y adolescentes (NNA) | SEMI | PARTIAL | AMBOS |
| cl-27-28-29 | CL | Arts. 27, 28 y 29 | Transferencias internacionales | SEMI | PARTIAL | AMBOS |
| cl-30-30-bis | CL | Art. 30 / 30 bis | Agencia y régimen sancionatorio (Arts. 34–38 [PENDIENTE: veri... | NO-VERIFICABLE-ESTATICAMENTE | NO_CONCLUIBLE_ESTATICAMENTE | JUICIO-HUMANO |
