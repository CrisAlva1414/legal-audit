# Crosswalk UE ↔ Chile (GDPR vs. Ley 21.719)

## Índice
- [Tabla 1 — 13 dimensiones](#cw-tabla-1)
- [Tabla 2 — Regla distinta por jurisdicción](#cw-tabla-2)
- [Tabla 3 — Reglas UE-only](#cw-tabla-3)
- [Tabla 4 — Reglas Chile-only](#cw-tabla-4)
- [Adecuación y transferencias Chile ↔ UE](#cw-adecuacion)
- [ISO y estándares](#cw-iso)
- [Fuentes no verificadas](#cw-fuentes)


- **Fecha de captura:** 2026-10-05
- **Estado Chile:** Ley 21.719 publicada, **no vigente** (entra 2026-12-01 salvo Boletín 18.623-07). Aplica hoy la Ley 19.628 antigua.
- **Estado UE:** Reg. (UE) 2016/679 (GDPR) vigente desde 25-05-2018. **Chile NO tiene decisión de adecuación** de la Comisión.

<a id="cw-tabla-1"></a>
## Tabla 1 — 13 dimensiones (artículo exacto por lado)

| # | Dimensión | UE (GDPR) | Chile (Ley 19.628 mod. 21.719) |
|---|---|---|---|
| 1 | Base legal | Art. 6 (6 bases) | Art. 12 (consent.) + Art. 13 (5 "otras fuentes"); incluye base económica/financiera (13 a) |
| 2 | Consentimiento | Art. 4(11) + Art. 7 | Art. 12 + def. Art. 2 p); retiro Art. 12; presunción "no libre" en contrato |
| 3 | Datos sensibles | Art. 9 (lista) | Art. 16 + 16 bis (salud/perfil biológico) + 16 ter (biométricos); def. Art. 2 g) |
| 4 | NNA | Art. 8 (16, baja a 13 opcional) | Art. 16 quáter: <14 parental (todo); 14–17 propio; **sensibles <16 parental** |
| 5 | Decisiones automatizadas | Art. 22 ("solely"; "explicación" en Recital 71) | Art. 8° bis; derecho a explicación/intervención/revisión **en el artículo** |
| 6 | DPIA | Art. 35 (+ Art. 36 consulta previa) | Art. 15 ter; supuestos taxativos, incl. "tratamiento masivo" |
| 7 | Brechas | Art. 33 (72h autoridad) + Art. 34 (titular, alto riesgo) | Art. 14 sexies: sin plazo fijo ("sin dilaciones indebidas"); titular si sensible/NNA <14/económico |
| 8 | Registro de actividades | Art. 30 (ROPA) | **No existe ROPA**; sí Art. 14 ter (política pública) + Art. 14 sexies (registro de brechas) |
| 9 | Transferencias | Arts. 44–49 (45, 46, 47, 49) | Arts. 27–28 (+29); Agencia fija adecuación y cláusulas modelo (no operativa) |
| 10 | Cookies | ePrivacy Dir. 2002/58/CE Art. 5(3) (consentimiento previo) | **No hay norma específica**; aplica régimen general (Arts. 12/13/14 ter) desde 2026-12-01; anti-spam: Ley 19.496 Art. 28 B |
| 11 | Cifrado / pseudonimización | Art. 32(1)(a) + def. Art. 4(5) | Art. 14 quinquies a) ("seudonimización y cifrado") + defs. Art. 2 k)/l) |
| 12 | Autoridad | Arts. 51–59 (DPA) + Art. 83 (multas) | Art. 30 / 30 bis (APDP); multas Arts. 34–38 [PENDIENTE: verificar rango exacto]; **APDP no operativa** |
| 13 | Derecho de bloqueo | **No existe autónomo** (restricción: Art. 18) | Art. 8° ter (autónomo) + catálogo Art. 4 |

> Nota: el "B" de BARSOP (bloqueo) en el Art. 4 incluye 6 derechos: acceso, rectificación, supresión, oposición, portabilidad y **bloqueo**.

<a id="cw-tabla-2"></a>
## Tabla 2 — Qué tiene que hacer la skill de forma DISTINTA según jurisdicción

| Dimensión | Regla distinta para la skill |
|---|---|
| NNA | Chile: 3 umbrales — <14 parental todo; 14–17 propio; **<16 parental para sensibles**. UE: 1 umbral (16, o 13 por MS). La skill NO puede compartir un único check `age >= 16`. |
| Bloqueo | Sólo Chile: check de estado "bloqueado" (Art. 8° ter). En UE no buscar un derecho de bloqueo (existe restricción Art. 18, con supuestos distintos). |
| Decisiones automatizadas | Chile: exigir "explicación" + intervención humana + revisión (Art. 8° bis). UE: Art. 22 exige garantías; la explicación debe anclarse en Recital 71, no en el artículo. Diferente string de evidencia esperado. |
| DPIA | Chile: disparadores taxativos, incluido "tratamiento masivo"; UE: "alto riesgo" + lista orientativa (Art. 35). Chile es más amplio. |
| Brechas | Chile: sin plazo fijo; UE: 72h (Art. 33). No emitir "cumple 72h" para Chile. |
| ROPA | UE: verificar Art. 30. Chile: NO exigir ROPA; verificar Art. 14 ter (política pública versionada) + registro de brechas. Reportar el gap como "no aplica/norma no lo exige", no como incumplimiento. |
| Cookies | UE: consentimiento previo ePrivacy 5(3). Chile: no hay ePrivacy; evaluar bajo régimen general (licitud + información). No declarar "cumple ePrivacy" en Chile ni "no aplica" en UE. |
| Consentimiento | Chile: "libre, informado, específico, inequívoco" + presunción de no-libre en contratos + prueba a cargo del responsable. UE: Art. 7 + Art. 4(11). Textos distintos. |
| Sensibles/biométrico | Chile: biométrico = sensible por definición; voz nombrada; "situación socioeconómica" es sensible. UE: biométrico sensible sólo para identificación unívoca (Art. 9). |
| Sanciones | Chile: UTM (5k/10k/20k), 2%/4%; autoridad NO operativa. UE: 20M€/4% (Art. 83); autoridad operativa. |
| Autoridad | Chile: APDP sin Consejo (no operativa) → veredicto de sanción = UNVERIFIABLE/estado especial. UE: DPA operativa. |
| Transferencias | Chile: Agencia fija adecuación y cláusulas modelo (hoy inexistentes). UE: Comisión fija adecuación; SCC europeas vigentes. No asumir equivalencia. |
| Base legal | Chile: 5 "otras fuentes" (Art. 13), no 6 bases; la letra a) económica no tiene espejo GDPR. UE: Art. 6(1)(a–f). |

<a id="cw-tabla-3"></a>
## Tabla 3 — Reglas UE-only (no aplican a Chile)

| Regla UE | Artículo | Estatus en Chile |
|---|---|---|
| Consentimiento de cookies / almacenamiento en terminal | ePrivacy Dir. 2002/58/CE Art. 5(3) | **No existe equivalente.** Aplica régimen general de datos (licitud + información). |
| ROPA (registro de actividades de tratamiento) | GDPR Art. 30 | **No existe.** Sólo política pública (14 ter) y registro de brechas (14 sexies). |
| DPO obligatorio en supuestos | GDPR Arts. 37–39 | Chile: **potestativo** (Art. 50: "podrá designar"). No obligatorio universal. |
| Consulta previa a la autoridad | GDPR Art. 36 | No aparece como figura equivalente; la Agencia puede emitir orientaciones (Art. 15 ter in fine). |
| Responsables conjuntos | GDPR Art. 26 | No hay artículo espejo explícito. |
| Representante en la UE | GDPR Art. 27 | Chile: contacto/representación vía Art. 14 inciso final y Art. 10 (correo en Chile). |
| Certificación / códigos de conducta | GDPR Arts. 40–43 | Chile: modelos de prevención y certificación (Arts. 48–53), de diseño distinto. |
| Multas hasta 20M€/4% | GDPR Art. 83 | Chile: 5k/10k/20k UTM y 2%/4% (Art. 35). |

<a id="cw-tabla-4"></a>
## Tabla 4 — Reglas Chile-only (que la UE no tiene)

| Regla Chile | Artículo | Comentario |
|---|---|---|
| Derecho de bloqueo | Art. 8° ter | No existe como derecho autónomo en GDPR. |
| Derecho a "explicación" de decisiones automatizadas en el articulado | Art. 8° bis | GDPR lo deja en considerandos. |
| Presunción legal de consentimiento no libre en contratos | Art. 12, inciso final | Sin espejo GDPR. |
| Base de licitud de datos económicos/financieros/socioeconómicos | Art. 13 a) | Idiosincrática. |
| DPIA obligatoria por "tratamiento masivo" como supuesto autónomo | Art. 15 ter b) | Más taxativa. |
| Biometría = dato sensible por definición | Art. 2 g) + 16 ter | Más estricto que Art. 9 GDPR. |
| Escalón de sensibilidad etario <16 | Art. 16 quáter | Sin espejo GDPR. |
| Registro Nacional de Sanciones y Cumplimiento | Art. 39 | Registro público de sancionados/modelos. |

<a id="cw-adecuacion"></a>
## Adecuación y transferencias Chile ↔ UE
- **Confirmado: Chile NO está en la lista de decisiones de adecuación de la Comisión** (lista oficial al 2026-10-05: Andorra, Argentina, **Brasil**, Canadá, Islas Feroe, Guernsey, Israel, Isla de Man, Japón, Jersey, Nueva Zelanda, Corea del Sur, Suiza, Reino Unido, EE.UU. (DPF), Uruguay, Organización Europea de Patentes).
  Fuente: `https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en`
- **Contraste — Brasil:** Decisión de Ejecución **(UE) 2026/179** de la Comisión, de **26-ene-2026** ("adequate level of protection of personal data by Brazil"), DOUE L de 28-01-2026. Fuente: `https://eur-lex.europa.eu/legal-content/EN/TXT/PDF?uri=OJ%3AL_202600179` y `https://www.boe.es/buscar/doc.php?id=DOUE-L-2026-80106`. Adoptada junto a una decisión recíproca de Brasil (comunicado 27-ene-2026).
- **Transferencia UE → Chile:** al no haber adecuación, requiere salvaguarda del **GDPR Art. 46** (SCC / garantías apropiadas) o Art. 49 (derogaciones). No hay "puerto seguro" por adecuación.
- **Transferencia Chile → UE:** bajo el Art. 27/28 chilenos, la UE calificaría como país con "niveles adecuados" **sólo si la Agencia lo determina** (Art. 28). Como la Agencia no está operativa, no hay listado chileno de países adecuados; se usarían garantías (Art. 27 b) / cláusulas modelo (que la Agencia aún no aprueba).
- **Chile NO adopta automáticamente las cláusulas contractuales tipo de la UE**; el Art. 28 faculta a la Agencia a aprobar sus propias cláusulas modelo.

<a id="cw-iso"></a>
# Bloque 4 — ISO y estándares
- **ISO/IEC 27701:2025** existe: *"Information security, cybersecurity and privacy protection — Privacy information management systems — Requirements and guidance"*, Ed. 2, publicada **2025-10**, 64 pp. (reemplaza la 27701:2019). Contiene **Anexo D (informativo) "Mapping to the General Data Protection Regulation"** (p. 53). Fuente: `https://www.iso.org/standard/27701` (VERIFICADO en la página oficial).
- **¿Qué arts. del GDPR mapea?** Según fuente secundaria (ISMS.online): mapea cláusulas/controles del PIMS a los **Arts. 5 a 35 y 44 a 49 (excluyendo Arts. 36–43)**. **INDIRECTA** (el Anexo D es texto de pago; no accedido).
- **No existe crosswalk oficial ISO 27701 ↔ Ley 21.719.** Búsqueda sin resultados; Anexo D sólo mapea a GDPR. **REFUTADO** (no encontrado) — reportar como vacío real de la skill.
- **¿Estándar/directriz chilena sobre anonimización/seudonimización?** No se encontró norma ni directriz técnica chilena vinculante. El **Decreto 12** (BCN idNorma 1214293, 17-jun-2025) crea la **Comisión Asesora Ministerial para la implementación de la Ley 21.719**, que emitió **4 informes** (ene-2026) con recomendaciones, pero **sin criterios normativos vinculantes** de anonimización. La **Resolución 1400 exenta** (BCN idNorma 1225450, Contraloría General de la República, D.O. 24-jun-2026; vigente 2026-12-01) es un procedimiento **interno de la CGR** para Arts. 54–55, no una directriz general. **NO VERIFICADO / no existe** directriz general.

<a id="cw-fuentes"></a>
## Fuentes NO verificadas / limitaciones del crosswalk
- `[NO ACCEDIDO: ISO/IEC 27701:2025 Anexo D — texto de pago]`; el rango 5–35/44–49 es INDIRECTO.
- Lado UE (GDPR, ePrivacy): no re-capturado contra EUR-Lex en esta sesión; verificar con `source-verifier`.
- Estado del **Boletín 18.623-07** es volátil; re-chequear antes de publicar el pack.
- **Suma urgencia** del boletín: fuente secundaria/INDIRECTA (el Mensaje oficial consta, la calificación de urgencia no se leyó de fuente primaria).
- Contenido del Art. 15 bis de la Ley 19.496 (suprimido): no verificado.

---

<a id="cw-resumen"></a>
## Resumen ejecutivo (para `orchestrator`)
- La ley chilena **NO rige aún** (esperada 2026-12-01, con proyecto de postergación pendiente): el pack debe marcar cada obligación con fecha de vigencia parametrizable.
- **Correcciones al research previo:** DPIA = **Art. 15 ter** (no 15 bis); `8° bis`/`8° ter` **sí existen**; brechas sin 72h; **no hay ROPA**; la "Resolución 1400" es de la **Contraloría**; la voz es biométrico nombrado y biométrico = sensible.
- **Diferenciales Chile-only para la skill:** bloqueo (8° ter), explicación de decisiones automatizadas (8° bis), umbral sensible NNA <16 (16 quáter), DPIA por "tratamiento masivo" (15 ter b).
- **Chile no exporta por adecuación** y la APDP **no está operativa**: cualquier veredicto de sanción debe degradarse a UNVERIFIABLE/estado especial.
