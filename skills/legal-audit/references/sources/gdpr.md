# GDPR + ePrivacy — Pack de evidencia congelado

## Vigencia de esta fuente
- **Fecha de captura:** 2026-10-05
- **Norma:** Reglamento (UE) 2016/679 (GDPR), CELEX 32016R0679, OJ L 119, 4.5.2016
- **Estado:** vigente desde 2018-05-25
- **Nota de acceso:** las citas del GDPR se verificaron contra el PDF oficial del
  OJ L 119 vía snapshot archivado (`web.archive.org/web/2020id_/`). EUR-Lex
  devolvió HTTP 202 (bot challenge) el 2026-10-05. **El subagente
  `source-verifier` DEBE intentar la URL en vivo primero y caer al snapshot
  antes de marcar una fuente como STALE** — si no, reportará falsos positivos.
- **Quién verifica:** subagente `source-verifier`

> **Nota de alcance:** el régimen de ePrivacy (Directiva 2002/58/EC, art. 5(3))
> es acumulativo e independiente del GDPR y se documenta en archivo separado:
> [`eprivacy.md`](./eprivacy.md). Mezclar ambos regímenes en una sola tabla
> genera falsos negativos.

## Índice
- [GDPR Art. 4 — Definiciones](#gdr-art-4--definiciones)
- [GDPR Art. 5 — Principios](#gdr-art-5--principios)
- [GDPR Art. 6 — Bases legales](#gdr-art-6--bases-legales)
- [GDPR Art. 7 — Consentimiento](#gdr-art-7--condiciones-del-consentimiento)
- [GDPR Art. 8 — Consentimiento de menores](#gdr-art-8--consentimiento-de-menores)
- [GDPR Art. 9 — Categorías especiales](#gdr-art-9--categorias-especiales)
- [GDPR Art. 12 — Transparencia](#gdr-art-12--transparencia)
- [GDPR Arts. 13 y 14 — Contenido de la información](#gdr-art-13-14--contenido-de-la-informacion)
- [GDPR Art. 15 — Acceso](#gdr-art-15--derecho-de-acceso)
- [GDPR Art. 16 — Rectificación](#gdr-art-16--rectificacion)
- [GDPR Art. 17 — Supresión](#gdr-art-17--supresion)
- [GDPR Art. 18 — Limitación](#gdr-art-18--limitacion)
- [GDPR Art. 20 — Portabilidad](#gdr-art-20--portabilidad)
- [GDPR Art. 21 — Oposición](#gdr-art-21--oposicion)
- [GDPR Art. 22 — Decisiones automatizadas](#gdr-art-22--decisiones-automatizadas)
- [GDPR Art. 25 — Protección por diseño](#gdr-art-25--proteccion-por-diseno)
- [GDPR Art. 28 — Encargado](#gdr-art-28--encargado)
- [GDPR Art. 30 — ROPA](#gdr-art-30-ropa)
- [GDPR Art. 32 — Seguridad](#gdr-art-32--seguridad)
- [GDPR Arts. 33 y 34 — Brechas](#gdr-art-33-34--brechas)
- [GDPR Arts. 35 y 36 — DPIA](#gdr-art-35-36--dpia)
- [GDPR Arts. 44–49 — Transferencias](#gdr-art-44-49--transferencias)
- [GDPR Recital 26 — Identificabilidad](#gdr-recital-26)
- [GDPR Recital 71 + Art. 4(4) — Scoring](#gdr-recital-71--art-44-scoring)
- [Bloque de jurisprudencia](#jurisprudencia-de-reidentificacion)
- [Checklist de determinismo (GDPR)](#gdr-determinismo)
- [Tabla: 8 checks de más alto valor](#gdr-8-checks)
- [Las 10 trampas de interpretación](#gdr-trampas)
- [Fuentes no verificadas](#gdr-fuentes-no-verificadas)
- [ePrivacy — archivo separado](./eprivacy.md#eprivacy--directiva-200258ec-art-53)

Método y estado de acceso (2026-10-05): `eur-lex.europa.eu` devolvió **HTTP 202 (bot challenge)** en vivo y `webfetch` 502; verifiqué el texto del GDPR contra el **PDF oficial del OJ L 119, 4.5.2016 (CELEX 32016R0679)** obtenido vía snapshot archivado `web.archive.org/web/2020id_/…`. El resto se leyó de PDF/HTML primarios (EDPB, ec.europa.eu) o del archivo de EUR-Lex/Curia. Cada cita es literal del documento indicado.

---

# Correcciones críticas al brief (revisadas contra fuente primaria)

El mapeo de varios artículos del brief **no coincide** con el texto vigente. Corrijo antes de usarlo, porque alimentaría checks erróneos:

1. **4(12)** es *‘personal data breach’*, **no “tratamiento”**. "Tratamiento/procesamiento" = **4(2)**.
2. **4(14)** es *‘biometric data’*, **no “decisiones automatizadas”**. *‘Profiling’* = **4(4)**; decisiones automatizadas = **Art. 22**.
3. **4(15)** es *‘data concerning health’*, **no “dato que identifica a un NNA”**. Menores = **Art. 8** (no hay definición de NNA en Art. 4).
4. **9(2)(g)** es *“substantial public interest”*, **no biométricos**. El biométrico para identificación única está en **9(1)**.
5. **El GDPR Art. 5 NO tiene apartado (3)**: solo (1) principios y (2) responsabilidad. “Variación (3)” no existe.
6. **6(2)** no es “el costo”: son medidas más específicas que pueden mantener/introducir los Estados miembros.
7. **15(1)(d)** es el plazo de conservación; “datos no obtenidos del interesado (fuente)” es **15(1)(g)**.
8. **28(4)** son las obligaciones del subencargado; la prohibición de designar nuevo encargado sin autorización es **28(2)**.
9. **Recital 22 es ámbito territorial/establecimiento**, no scoring. Scoring/profiling = **Recital 71 + Art. 4(4) + Art. 22**.
10. **32(2)** es la evaluación del riesgo, no “personas y procesos”.
11. **Art. 12(1)** no dice “proactivamente”: dice *“shall take appropriate measures to provide…”* (lo “proactivo” viene de guías/Recital 58).

---

<a id="gdr-articulos"></a>
# Bloque 1 — GDPR: núcleo para análisis de código

Fuente primaria: EUR-Lex **CELEX 32016R0679** (`https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679`), texto OJ L 119, 4.5.2016 · en vigor desde **25.5.2018**. **[VERIFICADO vía PDF oficial archivado; URL en vivo no accedida: HTTP 202]**

> **Campo "Diferencia con el GDPR": NO aplica en este bloque.** Estas fichas son
> las obligaciones del **lado UE** (referencia). La comparación con Chile vive en
> [`chile-eu-crosswalk.md`](./chile-eu-crosswalk.md). La ausencia del campo en
> cada ficha es explícita y por definición, no una omisión silenciosa.

<a id="gdr-art-4--definiciones"></a>
## GDPR Art. 4 — Definiciones relevantes
- **Texto/cita:** 4(1) *“any information relating to an identified or identifiable natural person (‘data subject’); … directly or indirectly, in particular by reference to an identifier such as a name, an identification number, location data, an online identifier or to one or more factors specific to the physical, physiological, genetic, mental, economic, cultural or social identity…”* · 4(2) *“any operation … such as collection, recording, organisation, structuring, storage, adaptation or alteration, retrieval, consultation, use, disclosure by transmission … erasure or destruction”* · 4(5) *“the personal data can no longer be attributed to a specific data subject without the use of additional information, provided that such additional information is kept separately and is subject to technical and organisational measures…”* · 4(11) consent *“any freely given, specific, informed and unambiguous indication … by a statement or by a clear affirmative action”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** inventario de campos/tablas y detección de identificadores (email, IP, device_id, voz, geolocalización); clase `Consent` con timestamp/versión; flag de “additional information” separado del dataset pseudonimizado.
- **Determinismo:** SEMI
- **Caveat:** 4(12) es *data breach* y 4(14) es *biometric data* — no usarlos como “tratamiento”/“decisiones automatizadas”. **4(11) exige acción afirmativa**: un pre-tick o silencio no es consentimiento.

<a id="gdr-art-5--principios"></a>
## GDPR Art. 5 — Principios (incl. 5(1)(e) y 5(2))
- **Texto/cita:** 5(1)(c) *“adequate, relevant and limited to what is necessary in relation to the purposes … (‘data minimisation’)”*; 5(1)(d) *“accurate and, where necessary, kept up to date … erased or rectified without delay”*; 5(1)(e) *“kept in a form which permits identification of data subjects for no longer than is necessary … (‘storage limitation’)”*; 5(1)(f) *“appropriate security … against unauthorised or unlawful processing and against accidental loss, destruction or damage … (‘integrity and confidentiality’)”*; 5(2) *“The controller shall be responsible for, and be able to demonstrate compliance with, paragraph 1 (‘accountability’)”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** ausencia de campos no usados; jobs/TTL de borrado y `retention_days`; logs de integridad; evidencias (ROPA/DPIA) versionadas en repo.
- **Determinismo:** DETERMINISTA en estructura (¿existe política/TTL/job?), SEMI en suficiencia.
- **Caveat:** Art. 5 tiene **solo dos apartados**. “Minimización” no es “no usar datos”: es limitar a lo *necesario para la finalidad*.

<a id="gdr-art-6--bases-legales"></a>
## GDPR Art. 6 — Bases legales
- **Texto/cita:** 6(1) *“Processing shall be lawful only if and to the extent that at least one of the following applies”*: (a) consent; (b) contract; (c) legal obligation; (d) vital interests; (e) public task; (f) legitimate interests *“except where such interests are overridden by the interests or fundamental rights and freedoms of the data subject … in particular where the data subject is a child.”* · 6(2) *“Member States may maintain or introduce more specific provisions to adapt the application … for compliance with points (c) and (e)…”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** campo `legal_basis` por finalidad y su justificación; no reutilizar el mismo dataset para una finalidad incompatible (Art. 6(4)).
- **Determinismo:** SEMI (detectar base declarada = DETERMINISTA; validez = JUICIO)
- **Caveat:** 6(2) **no** es “el costo”. Interés legítimo **no** cubre autoridades públicas en sus tareas (2º párr.) y exige balancing documentado.

<a id="gdr-art-7--condiciones-del-consentimiento"></a>
## GDPR Art. 7 — Condiciones del consentimiento
- **Texto/cita:** 7(1) *“the controller shall be able to demonstrate that the data subject has consented…”*; 7(2) *“the request for consent shall be presented in a manner which is clearly distinguishable from the other matters, in an intelligible and easily accessible form…”*; 7(3) *“It shall be as easy to withdraw as to give consent.”* (fuente: EUR-LEX CELEX 32016R0679)
- **Se operacionaliza en:** registro de consentimiento (user_id, timestamp, versión de policy, scope); endpoint de retiro con la misma cantidad de pasos que el otorgamiento; separación de checkboxes por finalidad.
- **Determinismo:** SEMI
- **Caveat:** “tan fácil como darlo” se mide en clics/pasos. Un retiro por email mientras se consiente con un clic es incumplimiento.

<a id="gdr-art-8--consentimiento-de-menores"></a>
## GDPR Art. 8 — Consentimiento de menores
- **Texto/cita:** 8(1) *“the processing … shall be lawful where the child is at least 16 years old. Where the child is below the age of 16 years, such processing shall be lawful only if and to the extent that consent is given or authorised by the holder of parental responsibility … Member States may provide by law for a lower age … provided that such lower age is not below 13 years.”* · 8(2) *“The controller shall make reasonable efforts to verify … that consent is given or authorised by the holder of parental responsibility … taking into consideration available technology.”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** age-gate, flujo de consentimiento parental verificable, y excepción cuando el tratamiento se basa solo en contrato/ley (no consentimiento).
- **Determinismo:** SEMI
- **Caveat:** **16 por defecto, no 13**; 13 solo si el Estado miembro lo bajó. La excepción solo aplica si la base es contrato/ley, no si es consentimiento.

<a id="gdr-art-9--categorias-especiales"></a>
## GDPR Art. 9 — Categorías especiales (voz/biometría)
- **Texto/cita:** 9(1) *“Processing of personal data revealing racial or ethnic origin, political opinions, religious or philosophical beliefs, or trade union membership, and the processing of genetic data, **biometric data for the purpose of uniquely identifying a natural person**, data concerning health or data concerning a natural person’s sex life or sexual orientation shall be prohibited.”* · 9(2)(a) *“explicit consent”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** flag de campos biométricos (embedding de voz/rostro) y si la finalidad es identificación única; base 9(2) explícita y documentada.
- **Determinismo:** SEMI
- **Caveat:** el biométrico está en **9(1)**; **9(2)(g) es “substantial public interest”**. La voz es categoría especial cuando se usa para identificación única.

<a id="gdr-art-12--transparencia"></a>
## GDPR Art. 12 — Transparencia y modalidades
- **Texto/cita:** 12(1) *“in a concise, transparent, intelligible and easily accessible form, using clear and plain language, **in particular for any information addressed specifically to a child**.”*; 12(3) respuesta *“without undue delay and in any event within one month”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** texto de privacy notice y su registro de versión; plazo de respuesta a DSARs; lenguaje por franja de edad.
- **Determinismo:** SEMI
- **Caveat:** Art. 12 **no** dice “proactivamente”. “Accesible” no es solo “publicado”: debe ser encontrable en ≤1 clic.

<a id="gdr-art-13-14--contenido-de-la-informacion"></a>
## GDPR Arts. 13 y 14 — Contenido de la información
- **Texto/cita:** 13(1) (*datos recogidos del interesado*): identidad/contacto, DPO, *“the purposes … as well as the legal basis”*, intereses legítimos si 6(1)(f), destinatarios, transferencias; 13(2): plazo de conservación, derechos, retiro, reclamación, etc. · 14(1) (*datos NO obtenidos del interesado*): + 14(1)(d) *“the categories of personal data concerned”* y 14(2)(f) *“from which source the personal data originate”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** diff entre fuente de datos (formulario vs scraping/terceros). 14 se dispara cuando el dato no lo dio el interesado.
- **Determinismo:** SEMI
- **Caveat:** falta frecuente: 14 exige **categorías de datos + fuente**, no solo aviso genérico; plazos de 14(3) distintos de 13.

<a id="gdr-art-15--derecho-de-acceso"></a>
## GDPR Art. 15 — Derecho de acceso
- **Texto/cita:** 15(1) *“confirmation as to whether or not personal data concerning him or her are being processed, and … access to the personal data and the following information”*; 15(1)(g) *“where the personal data are not collected from the data subject, any available information as to their source”*; 15(3) *“The controller shall provide a copy of the personal data undergoing processing … in a commonly used electronic form.”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** endpoint de export/consulta que devuelve categorías, fines, destinatarios, plazo y copia; no solo un “ok”.
- **Determinismo:** DETERMINISTA (existencia) + SEMI (completitud)
- **Caveat:** **15(1)(d) es el plazo de conservación**, no “los datos que no aportó”; eso es 15(1)(g).

<a id="gdr-art-16--rectificacion"></a>
## GDPR Art. 16 — Rectificación
- **Texto/cita:** *“the right to obtain … without undue delay the rectification of inaccurate personal data … the right to have incomplete personal data completed, including by means of providing a supplementary statement.”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** endpoint de update con propagación a réplicas/derivados (incl. datasets de ML).
- **Determinismo:** DETERMINISTA
- **Caveat:** completar no es solo corregir: hay que poder añadir dato faltante.

<a id="gdr-art-17--supresion"></a>
## GDPR Art. 17 — Supresión (“derecho al olvido”)
- **Texto/cita:** 17(1) *“erase … without undue delay where one of the following grounds applies”* (a)–(f); 17(2) *“take reasonable steps, including technical measures, to inform controllers which are processing the personal data … of any links to, or copy or replication of, those personal data.”*; 17(3) excepciones (a)–(e) (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** borrado real + cascada a backups, caches, índices y terceros; distinguir borrado de desindexación.
- **Determinismo:** DETERMINISTA (¿existe borrado?) + SEMI/NO-VERIFICABLE (¿aplica una causal/excepción?).
- **Caveat:** **desindexar ≠ borrar** (ver Google Spain). 17(2) solo si los datos fueron “made public”.

<a id="gdr-art-18--limitacion"></a>
## GDPR Art. 18 — Limitación del tratamiento
- **Texto/cita:** 18(1) *“restriction of processing where one of the following applies:”* (a)–(d); 18(2) *“such personal data shall, with the exception of storage, only be processed with the data subject’s consent or for the establishment, exercise or defence of legal claims…”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** flag `restricted` que bloquea procesamiento salvo almacenamiento; no basta un campo sin efecto en el pipeline.
- **Determinismo:** SEMI
- **Caveat:** limitar no es borrar: debe persistir el dato pero cesar el tratamiento.

<a id="gdr-art-20--portabilidad"></a>
## GDPR Art. 20 — Portabilidad
- **Texto/cita:** 20(1) *“receive the personal data concerning him or her, which he or she has provided to a controller, in a structured, commonly used and machine-readable format … where: (a) … consent … or … contract; and (b) the processing is carried out by automated means.”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** endpoint de export JSON/CSV; solo datos aportados por el interesado y base consent/contrato.
- **Determinismo:** DETERMINISTA (existencia/ formato) + SEMI (inclusión correcta)
- **Caveat:** no cubre datos “observados”/derivados ni tratamientos con otras bases (p. ej. interés legítimo).

<a id="gdr-art-21--oposicion"></a>
## GDPR Art. 21 — Oposición
- **Texto/cita:** 21(1) oposición a 6(1)(e)/(f) *“including profiling based on those provisions”*; 21(2) *“Where personal data are processed for direct marketing purposes, the data subject shall have the right to object at any time … which includes profiling to the extent that it is related to such direct marketing.”*; 21(3) *“the personal data shall no longer be processed for such purposes.”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** flag de opt-out por finalidad; para marketing debe ser inmediato e incondicional.
- **Determinismo:** DETERMINISTA (mecanismo) + SEMI
- **Caveat:** oposición direct marketing **no admite balancing**; la general (21(1)) sí.

<a id="gdr-art-22--decisiones-automatizadas"></a>
## GDPR Art. 22 — Decisiones automatizadas
- **Texto/cita:** 22(1) *“The data subject shall have the right not to be subject to a decision based solely on automated processing, including profiling, which produces legal effects concerning him or her or similarly significantly affects him or her.”*; 22(2)–(4) excepciones y garantías (intervención humana, expresar su punto de vista, impugnar) (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** detectar pipelines de decisión sin intervención humana + efecto significativo; endpoint de revisión humana.
- **Determinismo:** SEMI
- **Caveat:** **no todo scoring es Art. 22**: requiere decisión *solely* automatizada **y** efecto legal/similarmente significativo. El scoring común es *profiling* (Art. 4(4)) regido por 13/14/15/21, no por 22. (Ver Recital 71.)

<a id="gdr-art-25--proteccion-por-diseno"></a>
## GDPR Art. 25 — Protección por diseño y por defecto
- **Texto/cita:** 25(1) *“both at the time of the determination of the means for processing and at the time of the processing itself, implement appropriate technical and organisational measures, such as pseudonymisation…”*; 25(2) *“by default, only personal data which are necessary for each specific purpose … are processed … such measures shall ensure that by default personal data are not made accessible without the individual’s intervention to an indefinite number of natural persons.”* (fuente: EUR-Lex CELEX 32016R0679)
- **Guía:** EDPB **Guidelines 4/2019 v2.0**, *“Adopted on 20 October 2020”*, *“Version 2.0 20 October 2020 Adoption of the Guidelines by the EDPB after public consultation”* **[VERIFICADO]**.
- **Se operacionaliza en:** revisión de las decisiones de diseño y de la configuración por defecto (minimización de campos, exposición no automática a un número indefinido de personas, pseudonimización donde corresponda). No es cerrable por detector determinista: exige juicio de necesidad y proporcionalidad.
- **Determinismo:** JUICIO
- **Caveat:** no es certificación (25(3) solo es “elemento”); “default” se opone a *opt-in* para exposición de datos.

<a id="gdr-art-28--encargado"></a>
## GDPR Art. 28 — Encargado
- **Texto/cita:** 28(2) *“The processor shall not engage another processor without prior specific or general written authorisation of the controller.”*; 28(3) *“Processing by a processor shall be governed by a contract or other legal act … [que estipule, en particular, que el encargado] (a) processes the personal data only on documented instructions…; (h) … allow for and contribute to audits…”*; 28(4) *“the same data protection obligations … shall be imposed on that other processor”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** existencia de DPA por proveedor; lista de sub-encargados; cláusulas 28(3)(a)–(h).
- **Determinismo:** DETERMINISTA (presencia de contrato/subencargados) + SEMI (suficiencia)
- **Caveat:** la autorización para subencargado es **28(2)**, no 28(4).

<a id="gdr-art-30-ropa"></a>
## GDPR Art. 30 — Registro de actividades (ROPA)
- **Texto/cita:** 30(1) campos (a)–(g): *“name and contact details…; the purposes of the processing; a description of the categories of data subjects and of the categories of personal data; the categories of recipients…; where applicable, transfers…; where possible, the envisaged time limits for erasure…; where possible, a general description of the technical and organisational security measures…”*; 30(2) campos equivalentes para encargado; 30(5) *“shall not apply to an enterprise … employing fewer than 250 persons unless the processing … is likely to result in a risk … the processing is not occasional, or the processing includes special categories … or personal data relating to criminal convictions…”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** validar `.compliance/ropa` contra esquema 30(1); cruzar entradas con endpoints/modelos reales (drift).
- **Determinismo:** DETERMINISTA
- **Caveat:** la exención <250 empleados tiene **tres** excepciones; casi todo SaaS cae en “no ocasional”.

<a id="gdr-art-32--seguridad"></a>
## GDPR Art. 32 — Seguridad del tratamiento
- **Texto/cita:** 32(1) *“appropriate technical and organisational measures … including inter alia as appropriate: (a) the pseudonymisation and encryption of personal data; (b) the ability to ensure the ongoing confidentiality, integrity, availability and resilience…; (c) the ability to restore the availability and access … in a timely manner…; (d) a process for regularly testing, assessing and evaluating the effectiveness…”*; 32(2) *“In assessing the appropriate level of security account shall be taken in particular of the risks that are presented by processing…”*; 32(3) *“Adherence to an approved code of conduct … or an approved certification mechanism … may be used as an element by which to demonstrate compliance”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** cifrado en tránsito/reposo, backups + restore test, logs de integridad, pruebas periódicas; pseudonimización de campos sensibles.
- **Determinismo:** SEMI (ausencia de cifrado = hecho; adecuación = juicio)
- **Caveat:** **NO es certificación**: 32(3) dice “elemento”, no cumplimiento. Cifrado solo no cubre (b)(c)(d). 32(2) es riesgo, no “personas y procesos”.

<a id="gdr-art-33-34--brechas"></a>
## GDPR Art. 33 y 34 — Brechas
- **Texto/cita:** 33(1) *“without undue delay and, where feasible, not later than 72 hours after having become aware of it, notify … unless the personal data breach is unlikely to result in a risk…”*; 33(3)(a)–(d) *“describe the nature … categories and approximate number of data subjects … and … records; … name and contact details of the DPO …; describe the likely consequences; … measures taken or proposed…”*; 34(1) *“When the personal data breach is likely to result in a high risk … communicate … to the data subject without undue delay.”* (fuente: EUR-Lex CELEX 32016R0679)
- **Guía:** EDPB **Guidelines 9/2022 v2.0**, *“Adopted 28 March 2023”* **[VERIFICADO]**.
- **Se operacionaliza en:** playbook/runbook + registro documental de brechas con campos 33(3) y cálculo de 72 h.
- **Determinismo:** DETERMINISTA (campos/registro/plazo) + SEMI (evaluación de riesgo)
- **Caveat:** el reloj corre desde “having become aware”, no desde la detección técnica. 34 aplica solo a **alto** riesgo.

<a id="gdr-art-35-36--dpia"></a>
## GDPR Arts. 35 y 36 — DPIA y consulta previa
- **Texto/cita:** 35(1) *“Where a type of processing in particular using new technologies … is likely to result in a high risk … the controller shall, prior to the processing, carry out an assessment…”*; 35(3) exigible si (a) *“a systematic and extensive evaluation of personal aspects … based on automated processing, including profiling, and on which decisions are based…”*, (b) *“processing on a large scale of special categories…”*, (c) *“a systematic monitoring of a publicly accessible area on a large scale.”*; 36(1) *“consult the supervisory authority prior to processing where a data protection impact assessment … indicates that the processing would result in a high risk in the absence of measures…”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** señalizar tratamientos que gatillan 35(3) (biometría a escala, monitoreo, scoring con efecto) y ausencia de DPIA; ruteo a 36.
- **Determinismo:** SEMI → JUICIO
- **Caveat:** DPIA no es solo para datos sensibles: 35(1) es “alto riesgo” amplio (ver 9 criterios EDPB WP248).

<a id="gdr-art-44-49--transferencias"></a>
## GDPR Arts. 44–49 — Transferencias internacionales
- **Texto/cita:** 45(1) *“A transfer … may take place where the Commission has decided that the third country … ensures an adequate level of protection.”*; 45(3) *“The implementing act shall provide for a mechanism for a periodic review, at least every four years … shall specify its territorial and sectoral application…”*; 46(1) *“only if the controller or processor has provided appropriate safeguards, and on condition that enforceable data subject rights and effective legal remedies … are available”*; 46(2)(c) *“standard data protection clauses adopted by the Commission…”*; 49(1)(a) *“the data subject has explicitly consented to the proposed transfer, after having been informed of the possible risks…”.* (fuente: EUR-Lex CELEX 32016R0679)
- **SCC — Decisión de Ejecución (UE) 2021/914** (4.6.2021, OJ L 199/31): Art. 1(1) *“The standard contractual clauses set out in the Annex are considered to provide appropriate safeguards within the meaning of Article 46(1) and (2)(c)…”*; cuatro módulos (C→C, C→P, P→P, P→C) (fuente: CELEX 32021D0914). **[VERIFICADO vía archivo]**
- **Se operacionaliza en:** inventario de destinos (subprocessors, regiones de nube/CDN/LLM), transfer tool documentado, mapping país→adecuación (p. ej. Data Privacy Framework).
- **Determinismo:** SEMI (inventario = DETERMINISTA; validez = JUICIO)
- **Caveat:** SCC exige *Transfer Impact Assessment*; 49 es derogación **excepcional**, no base habitual.

<a id="gdr-recital-26"></a>
## GDPR Recital 26 — Identificabilidad / pseudonimización
- **Texto/cita:** *“Personal data which have undergone pseudonymisation, which could be attributed to a natural person by the use of additional information should be considered to be information on an identifiable natural person. To determine whether a natural person is identifiable, account should be taken of all the means reasonably likely to be used, such as **singling out**, either by the controller or by another person…”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** tratar datasets pseudonimizados como personales; exigir medidas sobre la *additional information*.
- **Determinismo:** NO-VERIFICABLE-ESTÁTICAMENTE
- **Caveat:** “quitar el nombre” **no** anonimiza. El estándar es “means reasonably likely to be used”, no cero absoluto.

<a id="gdr-recital-71--art-44-scoring"></a>
## GDPR Recital 71 + Art. 4(4) — Scoring/profiling (corrección del brief)
- **Texto/cita:** Recital 71 *“the right not to be subject to a decision, which may include a measure, evaluating personal aspects … which is based **solely** on automated processing and which produces legal effects … or similarly significantly affects him or her…”*; 4(4) *“‘profiling’ means any form of automated processing … to evaluate certain personal aspects … to analyse or predict aspects concerning … performance at work, economic situation, health, personal preferences, interests, reliability, behaviour, location or movements”* (fuente: EUR-Lex CELEX 32016R0679)
- **Se operacionaliza en:** distinguir scoring informativo (permitido, con transparencia Art. 13/14/15) de decisión *solely* automatizada con efecto significativo (Art. 22).
- **Determinismo:** SEMI
- **Caveat:** **Recital 22 no trata de scoring** (es establecimiento territorial). El scoring **sí es dato personal** por 4(1)+4(4), pero **no todo scoring** cae en Art. 22.

---

<a id="jurisprudencia-de-reidentificacion"></a>
# Bloque 2 — Jurisprudencia de reidentificación

## WP29 Opinion 05/2014 (WP216) — Anonymisation Techniques
- **Fuente:** `https://ec.europa.eu/justice/article-29/documentation/opinion-recommendation/files/2014/wp216_en.pdf` **[VERIFICADO, 37 pág.]**
- **Ratio + cita:** anonimizar exige impedir *singling out*, *linkability* e *inference*: *“An effective anonymisation solution prevents all parties from singling out an individual in a dataset, from linking two records within a dataset … and from inferring any information…”* · quitar el nombre no basta: *“removing directly identifying elements in itself is not enough to ensure that identification of the data subject is no longer possible.”*
- **k-anonymity:** *“The main flaw of the k-anonymity model is that it does not prevent any type of inference attack. Indeed, **if all k individuals are within a same group, then if it is known which group an individual belongs to, it is trivial to retrieve the value of this property.**”* (y Tabla 2: fallo con CP 750* / diagnóstico).
- **Regla operativa:** un check no puede aceptar “k≥5” como anonimato; debe exigir evaluación de quasi-identificadores, inferencia y linkability.
- **Determinismo:** NO-VERIFICABLE-ESTÁTICAMENTE
- **Caveat:** WP216 es previa al GDPR (Directiva 95/46) pero **endosada por el EDPB** en su primera plenaria; sigue citándose.

## EDPB Guidelines 02/2026 on Anonymisation — ⚠️ BORRADOR EN CONSULTA
- **Fuente:** `https://www.edpb.europa.eu/system/files/2026-07/edpb_guidelines_202602_anonymisation_v1_en_0.pdf` **[VERIFICADO]** — *v1.0, adopted 07 July 2026*; **consulta abierta hasta 2026-10-30 (23:59 CET)** (verificado en `edpb.europa.eu/public-consultations/guidelines-022026-on-anonymisation_en`).
- **Ratio + cita (“relative approach”):** *“Whether this is the case may vary from one entity to another. Consequently, anonymity should be assessed from each relevant entity’s perspective…”*; y cita a C-413/23 P: referencia [4] *“C-413/23 P EDPS v SRB.”*; riesgo: *“the likelihood of the individual being successfully distinguished from others … does not need to be zero; instead, that likelihood should be insignificant in reality.”*
- **Regla operativa:** la anonimización es relativa a la entidad; el mismo dataset puede ser personal para el controlador y anónimo para un tercero que no puede reidentificar.
- **Determinismo:** NO-VERIFICABLE-ESTÁTICAMENTE
- **Caveat:** **No es derecho vigente aún**; no citar como obligación. Cierre de consulta **2026-10-30**.

## EDPB Guidelines 01/2025 on Pseudonymisation — ⚠️ versión de consulta
- **Fuente:** `https://www.edpb.europa.eu/system/files/2025-01/edpb_guidelines_202501_pseudonymisation_en.pdf` **[VERIFICADO, 200]** — *“Adopted on 16 January 2025”*, pie *“Adopted - version for public consultation”*.
- **Estado final:** **NO VERIFICADO / no adoptada**. La consulta cerró 14-03-2025; al 2026-10-05 no encontré versión final publicada en el sitio EDPB (solo el borrador). Tratar como guía en borrador.
- **Ratio + cita:** *“they need to keep additional information for attributing the personal data to a specific data subject separately … In particular, the additional information is not to be disclosed to or used by persons processing the pseudonymised data. Such additional information may itself be personal data…”*; *“the pseudonymising controller or processor must be subject to technical and organisational measures…”*; *“Typically such measures limit access to the retained additional information (e.g. keys or tables of pseudonyms), and control the flow of pseudonymised data.”*
- **No exige controlador jurídicamente separado:** el texto deja quién queda excluido *“to the controller’s decision”* y admite efectos *“within the same controller”* (Recital 29) — **no** exige una entidad jurídica distinta.
- **Regla operativa:** check “tabla/keys de mapping con control de acceso separado del de los datos pseudonimizados” + obligación de no divulgación.
- **Determinismo:** SEMI (separación de accesos = DETERMINISTA; eficacia = JUICIO)
- **Caveat:** pseudonimizar **no** requiere base legal propia (es medida técnica/organizativa), pero **no anonimiza**.

## CJEU C-413/23 P — EDPS v Single Resolution Board (Primera Sala, 4.9.2025, ECLI:EU:C:2025:645)
- **Fuente:** `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62023CJ0413` **[VERIFICADO vía archivo]**.
- **Ratio + cita:** párr. 82 *“a means of identifying the data subject is not reasonably likely to be used where the risk of identification appears in reality to be insignificant, in that the identification … is prohibited by law or impossible in practice, for example because it would involve a disproportionate effort in terms of time, cost and labour.”* · párr. 75/86 *“pseudonymisation may, depending on the circumstances of the case, effectively prevent persons other than the controller from identifying the data subject … pseudonymised data must not be regarded as constituting, in all cases and for every person, personal data…”*
- **Regla operativa:** un check de “tabla de mapping con control de acceso separado del de los datos pseudonimizados”; pseudonimizado es personal **para el emisor** que retiene la información adicional, no necesariamente para todos.
- **Determinismo:** SEMI / NO-VERIFICABLE
- **Caveat:** no convierte automáticamente lo pseudonimizado en anónimo; exige que las medidas “actually put in place” impidan la atribución para el receptor.

## CJEU C-582/14 — Breyer v Bundesrepublik Deutschland (2016)
- **Fuente:** `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62014CJ0582` **[VERIFICADO vía archivo]**.
- **Ratio + cita:** párr. 49 *“a dynamic IP address registered by an online media services provider … constitutes personal data … where the latter has the legal means which enable it to identify the data subject with additional data which the internet service provider has about that person.”*
- **Regla operativa:** IP dinámica = dato personal respecto del operador web si tiene medios legales de cruzarla.
- **Determinismo:** SEMI
- **Caveat:** **Breyer NO es el caso del derecho al olvido** (ese es Google Spain C-131/12, abajo).

## CJEU C-131/12 — Google Spain (Grand Chamber, 2014)
- **Fuente:** `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62012CJ0131` **[VERIFICADO vía archivo]**.
- **Ratio + cita:** párr. 82 *“order the operator of the search engine to remove from the list of results … links to web pages published by third parties … **without an order to that effect presupposing the previous or simultaneous removal of that name and information … from the web page on which they were published**.”* · párr. 97: los derechos del interesado *“override, as a rule, not only the economic interest of the operator of the search engine but also the interest of the general public…”*
- **Regla operativa:** un check de supresión debe distinguir **borrar de la fuente** (Art. 17 GDPR) vs **desindexar**; cumplir uno no cumple el otro.
- **Determinismo:** SEMI
- **Caveat:** no confundir con Breyer; Google Spain resuelve sobre Directiva 95/46 pero el principio de desindexación persiste bajo Art. 17.

---

<a id="gdr-determinismo"></a>
# Bloque 4 — Checklist de determinismo (integrado arriba)

Clasificación por artículo: **4** SEMI · **5** DETERMINISTA/SEMI · **6** SEMI · **7** SEMI · **8** SEMI · **9** SEMI · **12** SEMI · **13-14** SEMI · **15** DETERMINISTA/SEMI · **16** DETERMINISTA · **17** DETERMINISTA/SEMI · **18** SEMI · **20** DETERMINISTA/SEMI · **21** DETERMINISTA/SEMI · **22** SEMI · **25** JUICIO · **28** DETERMINISTA/SEMI · **30 DETERMINISTA** · **32** SEMI · **33-34** DETERMINISTA/SEMI · **35-36** SEMI→JUICIO · **44-49** SEMI · **Recital 26** NO-VERIFICABLE · **WP216 / 02/2026 / C-413/23 P** NO-VERIFICABLE.

<a id="gdr-8-checks"></a>
## Tabla — 8 checks de más alto valor
| # | Artículo | Qué señala en código | Determinismo |
|---|----------|----------------------|--------------|
| 1 | **Art. 30** | ROPA ausente o desincronizada con endpoints/modelos | DETERMINISTA |
| 2 | **Art. 20** | Endpoint de export en formato estructurado/legible por máquina | DETERMINISTA |
| 3 | **Art. 17 + 5(1)(e)** | Borrado real (cascada) vs desindexación; ausencia de TTL/job de retención | DETERMINISTA |
| 4 | **Art. 32(1)(a)** | Cifrado en tránsito/reposo y pseudonimización de campos sensibles | SEMI |
| 5 | **Art. 15(1)+(3)** | DSAR que devuelve categorías+fines+**copia** de datos | DETERMINISTA |
| 6 | **Art. 33(3)** | Campos mínimos de brecha + plazo 72 h documentado | DETERMINISTA |
| 7 | **Art. 9(1)** | Campos biométricos (voz/rostro) usados para identificación única | SEMI |
| 8 | **Art. 7(3)** | Retiro de consentimiento en ≤ los mismos pasos que otorgarlo | SEMI |

<a id="gdr-trampas"></a>
## Lista de trampas (errores de interpretación a evitar)
1. **“Scoring = Art. 22.”** Solo si la decisión es *solely* automatizada **y** produce efecto legal/similarmente significativo (22(1)); el resto es *profiling* (4(4)) con deberes de transparencia, no prohibición.
2. **“k≥5 = anónimo.”** k-anonymity no evita inferencia; si todos los k comparten el atributo, el valor se recupera trivialmente (WP216).
3. **“Borrar el nombre/anónimo.”** Pseudonimizar no anonimiza: los datos siguen siendo personales (Recital 26; C-413/23 P).
4. **“Desindexar = borrar.”** Google Spain párr. 82: desindexar no extingue la publicación en la fuente.
5. **“ePrivacy 5(3) se cubre con interés legítimo GDPR.”** No: 5(3) exige consentimiento autónomo (lex specialis; Art. 95 GDPR).
6. **“Todo dato agregado está fuera del GDPR.”** Solo si supera el estándar de anonimato; la agregación que permite *singling out/linkability/inference* sigue dentro.
7. **“DPIA solo para datos sensibles.”** Art. 35(1) es alto riesgo (incluye monitoreo sistemático a escala y scoring con efecto).
8. **“Cifrado en reposo = Art. 32 cumplido.”** 32(1)(b)(c)(d) exigen continuidad, restauración y testing; certificación es solo “elemento” (32(3)).
9. **“Menores: 13 años siempre.”** Defecto 16; 13 solo si el EM lo bajó (Art. 8(1)).
10. **“Pseudonimización exige controlador jurídicamente separado.”** Falso: el EDPB deja el diseño al controlador, incluso dentro de la misma organización.

<a id="gdr-fuentes-no-verificadas"></a>
## Fuentes NO verificadas / con salvedad
- **EDPB Guidelines 01/2025 on Pseudonymisation — versión final:** `NO VERIFICADO`. Solo existe publicada la *versión para consulta* (16-01-2025); no encontré adopción final al 2026-10-05.
- **eur-lex.europa.eu (URL en vivo):** `NO ACCEDIDO` — HTTP **202** (bot challenge) el 2026-10-05; texto tomado de copia archivada del PDF oficial OJ L 119.
- **Citas de la Decisión 2021/914 / C-413/23 P / Breyer / Google Spain / 2002/58:** verificadas vía snapshot archivado de EUR-Lex (no URL en vivo).
- **EDPB Guidelines 04/2019 y 09/2022:** fechas y versiones verificadas contra PDF/páginas oficiales EDPB (texto íntegro no re-citado línea por línea).

**Fecha de captura: 2026-10-05.**
