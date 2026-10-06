# Vendors de terceros — inventario externo (pack de evidencia congelado)

Inventario estático de proveedores con los que una aplicación puede tratar
datos personales (LLM, STT/ASR, IdP, infraestructura, observabilidad, pagos,
proveedores chinos) y las reglas de transferibilidad que activa cada categoría.
Complementa a `sources/gdpr.md` (Arts. 28 y 44–49) y a
`sources/chile-eu-crosswalk.md` (Arts. 27–28 de la Ley 19.628 mod. 21.719).
No sustituye al contrato: **este archivo nunca es evidencia de que un contrato
exista hoy.**

## Vigencia de esta fuente
- **Fecha de captura:** 2026-10-05
- **Naturaleza:** INVENTARIO EXTERNO. Cambia en meses.
- **Advertencia:** los DPAs, listas de sub-procesadores, políticas de retención
  y estados de certificación MUTAN. Un dato marcado VERIFICADO lo estaba al
  2026-10-05. **Este archivo nunca es evidencia de que un contrato exista hoy.**
  El subagente `source-verifier` debe re-consultar las URLs oficiales.
- **Quién verifica:** subagente `source-verifier`

## Índice
- [1. Reglas de transferibilidad por categoría](#ven-sec1)
- [2. Cadena de sub-encargados](#ven-sec2)
- [3. Tabla de proveedores](#ven-sec3)
- [4. Transferencias: el mapa 2026](#ven-sec4)
- [5. Lo que NO se puede verificar estáticamente](#ven-sec5)
- [6. Fuentes no verificadas](#ven-sec6)

<a id="ven-sec1"></a>
## Sección 1 — Reglas de transferibilidad por categoría

Regla general: usar un proveedor externo crea un **encargado del tratamiento**
(processor) con las exigencias del GDPR **Art. 28** y, si hay transferencia
internacional, de los **Arts. 44–49**. La categoría del proveedor decide qué se
puede chequear estáticamente y qué hay que llevar a juicio. Para cada categoría
se lista: obligación GDPR activada, determinismo, check concreto de la
herramienta y riesgo dominante.

### 1.1 LLM API — categoría `llm`

- **Obligación GDPR:** Art. 28(3) — el encargado procesa "solo siguiendo
  instrucciones documentadas"; Arts. 44–49 si hay transferencia fuera de la UE.
- **Error conceptual más común (señalado fuerte):** un LLM que **entrena** con
  tus prompts deja de ser *processor* para esa finalidad y pasa a ser
  **controller independiente**. Art. 28(3) exige procesar "sólo siguiendo
  instrucciones documentadas"; entrenar no es una instrucción documentada. Ese
  cambio no es técnico sino de **rol jurídico**: el DPA ya no cubre esa
  finalidad.
- **Modelos ya entrenados — test de 3 partes:** el test para decidir si el
  proveedor actúa como controlador o como encargado sobre datos que YA usó
  para entrenar viene de **WP29 Opinion 05/2014 (WP216)**, aplicado a IA por
  **EDPB Opinion 28/2024** (fuente nueva agregada en esta captura). Pregunta:
  (1) ¿el proveedor determina la finalidad o los medios? (2) ¿usa los datos
  para fines propios? (3) ¿los comparte con terceros?
- **Corrección de una cita errónea, anotada a propósito:** **EDPB Guidelines
  05/2020 es sobre CONSENTIMIENTO, NO sobre anonimización.** La anonimización
  es **EDPB Guidelines 02/2026** (borrador; la consulta cierra 2026-10-30).
  Quien busque la guía de anonimización no debe citar 05/2020 (ver
  `bibliography.md`, sección Guías de autoridad).
- **Determinismo:** SEMI — detectar flags de training/fine-tuning, ZDR y DPA
  en config/política es determinista; concluir la controladoría material es
  juicio.
- **Check concreto de la herramienta:** localizar llamadas a APIs de LLM; leer
  en config/env si "training"/"fine-tuning" está habilitado; si la política
  declara zero-data-retention; si el proveedor figura en la lista DPF activa y
  con cobertura (ver [Sección 4](#ven-sec4)); si existe DPA firmado + SCCs o
  cláusulas contractuales modelo.
- **Riesgo dominante:** transferencia a EEUU sin base (OpenAI y Anthropic NO
  están en DPF — ver [Sección 3](#ven-sec3)) y entrenamiento no autorizado que
  destruye la figura de encargado.

### 1.2 STT/ASR cloud — categoría `stt`

- **Obligación GDPR:** **Art. 9(1)** si la voz identifica de forma **unívoca**
  (biométrico, **Art. 4(14)**); Art. 6 + 9(2) para la base; la grabación es
  dato personal aunque no sea biométrica. En Chile: **Art. 2 g) Ley 19.628
  mod. 21.719** — dato sensible si revela salud u origen.
- **Divisor de aguas del Art. 9:** la voz es biométrica SOLO si identifica de
  forma unívoca (Art. 4(14) + 9(1)). Si el servicio solo transcribe, no es
  biométrico — pero la **grabación sigue siendo dato personal** y puede
  capturar **salud** → **sensible en Chile** (Art. 2 g). Para un producto de
  STT, esa distinción decide si entra el régimen agravado de datos sensibles.
- **Determinismo:** JUICIO — la identificabilidad unívoca no se deduce del
  código; depende de qué se envía y de las capacidades del proveedor.
- **Check concreto de la herramienta:** detectar si se envía **audio crudo** o
  solo texto; si se retienen grabaciones (por cuánto y para qué); si la
  política del proveedor declara uso de la voz para biometría o identificación
  de locutor; si el audio puede contener **menores** (ver detector
  `minors_and_voice`).
- **Riesgo dominante:** tratar el audio como "solo contenido" cuando puede ser
  biométrico o revelar salud; doble salto regulatorio UE (Art. 9) + Chile
  (Art. 2 g).

### 1.3 IdP — categoría `idp`

- **Obligación GDPR:** Arts. 28 y 32 (procesa identificadores y credenciales);
  Arts. 44–49 si hay transferencia. Auth0/Okta y Clerk SÍ están en DPF
  (verificado 4-oct-2026).
- **Determinismo:** DETERMINISTA — presencia del IdP y su membresía DPF son
  chequeables.
- **Check concreto de la herramienta:** verificar en la lista oficial del DPF
  que el IdP esté **activo** y que la cobertura incluya tus datos (cobertura
  HR vs non-HR); si falla cualquiera de los dos → exigir SCCs + TIA; verificar
  DPA firmado y controles de Art. 32 (MFA, logs).
- **Riesgo dominante:** punto único de autenticación: una falla del IdP
  compromete todas las cuentas; y transferencia de credenciales/hashes fuera
  de la UE sin salvaguarda.

### 1.4 Infra/CDN — categoría `infra`

- **Obligación GDPR:** Art. 28 (sub-encargados y cascada), Art. 32; Arts.
  44–49 si transferencia. En el subconjunto verificado de la
  [Sección 3](#ven-sec3): Cloudflare, MongoDB, Netlify y Snowflake SÍ están en
  DPF; el resto de la categoría queda `A VERIFICAR` fila por fila.
- **Determinismo:** DETERMINISTA — región declarada, lista DPF y lista de
  sub-procesadores son chequeables.
- **Check concreto de la herramienta:** región de deploy declarada; existencia
  de lista pública de sub-procesadores; membresía DPF activa; flags de data
  residency.
- **Riesgo dominante:** el tráfico de CDN/edge pasa por nodos en múltiples
  jurisdicciones; la región declarada no garantiza la región real en runtime
  (ver [Sección 5](#ven-sec5), límite 1).

### 1.5 Proveedores chinos — categoría `chino`

- **Obligación GDPR:** Arts. 6, 12–14, 27, 31 y 32 — los mismos que el Garante
  italiano declaró transgredidos en su bloqueo a DeepSeek (30-ene-2025,
  provvedimento 10098477); Arts. 44–49 para la transferencia a la RPCh.
- **Contexto que no se negocia:** la RPCh **no está** en la lista de
  adecuación de la Comisión (ver [Sección 4](#ven-sec4)). La **Ley de
  Inteligencia Nacional china, Art. 7**, obliga a toda organización a "apoyar,
  asistir y cooperar" con el trabajo de inteligencia del Estado: un proveedor
  chino no puede ofrecer garantías de no-colaboración que contradigan su ley
  nacional.
- **Determinismo:** NO-VERIFICABLE-ESTATICAMENTE — sin DPA público y con
  obligación legal de colaborar, ningún artefacto estático cierra la pregunta.
- **Check concreto de la herramienta:** detectar endpoints hosted en la RPCh
  (p. ej. `api.deepseek.com`, `dashscope.aliyuncs.com`); si hay hosted →
  hallazgo de transferencia sin base adecuada; si el modelo es **open-weights
  auto-alojado fuera de China** → los pesos son software y NO hay
  transferencia de datos.
- **Salida defendible:** open-weights auto-alojados fuera de China (Qwen, GLM,
  DeepSeek-R1). **Para voz de menores NO se defiende hosted chino en
  absoluto**: suma Art. 9 GDPR / Art. 2 g Chile + ausencia de base adecuada.
- **Riesgo dominante:** acceso estatal directo a los datos + sin adecuación +
  sin DPA público → base jurídica inexistente para la transferencia.

<a id="ven-sec2"></a>
## Sección 2 — Cadena de sub-encargados (casos no obvios)

Casos donde el sub-encargado NO es la empresa con la que se firmó el contrato.
Datos de la lista pública de sub-procesadores o de la documentación oficial,
capturados a 2026-10-05; la URL exacta del anexo se re-consulta con
`source-verifier`.

1. **Cloudflare AI Gateway** — la lista de sub-procesadores de Cloudflare
   incluye a **Anthropic, OpenAI, xAI, Groq y CoreWeave** como sub-encargados
   del tráfico de AI Gateway. Sorpresa: Cloudflare es "infraestructura", pero
   el gateway de IA reenvía prompts a proveedores de modelos que no figuran en
   la relación contractual visible.
   URL: `https://www.cloudflare.com/cloudflare_subprocessors/`
2. **Datadog y Sentry** — ambos listan **Anthropic y OpenAI** como
   sub-procesadores (servicios AI/ML). Sorpresa: la observabilidad dice
   "monitoreo", pero trazas pueden terminar en un modelo de tercero.
   - Datadog: `https://www.datadoghq.com/legal/subprocessors/`
   - Sentry: `https://sentry.io/legal/dpa/`
3. **Azure "OpenAI operated models"** — en Azure OpenAI, los modelos
   "operados por OpenAI" hacen que **OpenAI actúe como sub-procesador** de
   Microsoft. Microsoft publica la lista de sub-procesadores en el DPA
   (URL del anexo exacto: `A VERIFICAR` con `source-verifier`):
   `https://www.microsoft.com/licensing/docs/view/Microsoft-Products-and-Services-Data-Protection-Addendum-DPA`
4. **AWS Bedrock** — con el flag `provider_data_share` habilitado, tus prompts
   llegan a **Anthropic** (y al proveedor del modelo) y se retienen **30 días**
   para trust & safety. Con `default`/`none`, el proveedor del modelo **no ve**
   tus datos. **Ese flag solo decide si hay transferencia o no**; no cambia
   quién es encargado.
   URL de compliance AWS: `https://aws.amazon.com/compliance/data-protection/`
   (lista de sub-procesadores: `A VERIFICAR` la URL exacta)
5. **AssemblyAI LLM Gateway** — usa modelos de terceros **vía AWS Bedrock**
   con **zero data retention (ZDR)**. Sorpresa: la cadena real es AssemblyAI →
   Bedrock → proveedor del modelo; el DPA de AssemblyAI no cubre por sí solo
   el eslabón final.
   URL legal: `https://www.assemblyai.com/legal`

<a id="ven-sec3"></a>
## Sección 3 — Tabla de proveedores

> **Tres hechos que no se pueden perder de vista:**
>
> 1. **OpenAI y Anthropic NO están en el Data Privacy Framework** (verificado
>    contra el registro oficial el 4-oct-2026). Sus transferencias a la UE van
>    por **SCCs + TIA**. SÍ están en el DPF: **Google, Microsoft, Okta, Clerk,
>    MongoDB, Sentry, Stripe, Netlify, Snowflake**. Es contraintuitivo y es el
>    dato más accionable de este pack.
> 2. **DeepSeek** fue bloqueada por el **Garante italiano** (30-ene-2025,
>    provvedimento **10098477**) por transgresión de los **Arts. 6, 12–14, 27,
>    31 y 32**. Su privacy policy declara que procesa y almacena en la **RPCh**
>    con foro en **Hangzhou**. **Sin DPA público.** La **Ley de Inteligencia
>    Nacional china, Art. 7**, obliga a toda organización a "apoyar, asistir y
>    cooperar" con el trabajo de inteligencia del Estado.
> 3. La salida defendible para modelos chinos es **open-weights auto-alojados
>    fuera de China** (Qwen, GLM, DeepSeek-R1): los pesos son software, no hay
>    transferencia de datos. **Para voz de menores no se defiende hosted chino
>    en absoluto** — suma Art. 9 + ausencia de base adecuada.

Columnas: nombre · categoría · DPA (firmable?) · certificaciones ·
DPF/adecuación · región default · retención/training default · sub-processors
(URL) · estado.

Nota de fidelidad: el brief de esta pieza decía "24 proveedores"; la lista
enunciada suma **32 filas**, que se transcriben completas (ninguna se omite).
"Estado" es el peor nivel de verificación de las celdas materiales de la fila
(`VERIFICADO` / `NO VERIFICADO` / `A VERIFICAR`); las celdas llevan su propia
marca cuando difiere.

### 3.1 LLM

| Nombre | Categoría | DPA (firmable?) | Certificaciones | DPF/adecuación | Región default | Retención/training default | Sub-processors (URL) | Estado |
|---|---|---|---|---|---|---|---|---|
| **OpenAI** | llm | Publica DPA (firmable) | A VERIFICAR (trust portal con NDA) | **NO en DPF** (VERIFICADO 4-oct-2026) | US (multi-región por contrato: A VERIFICAR) | A VERIFICAR (política mutable) | `https://openai.com/policies/` (lista: A VERIFICAR) | VERIFICADO |
| **Anthropic** | llm | Publica DPA (firmable) | A VERIFICAR (trust portal con NDA) | **NO en DPF** (VERIFICADO 4-oct-2026) | US (multi-región por contrato: A VERIFICAR) | A VERIFICAR (política mutable) | `https://www.anthropic.com/legal` (lista: A VERIFICAR) | VERIFICADO |
| **Google (Gemini)** | llm | Publica DPA (CFE) | A VERIFICAR | SÍ en DPF (VERIFICADO 4-oct-2026) | Global / multi-región | A VERIFICAR | `https://cloud.google.com/terms/sccs/subprocessors` (A VERIFICAR) | VERIFICADO |
| **Azure — "OpenAI operated models"** | llm | Publica DPA (Microsoft) | A VERIFICAR | SÍ en DPF (Microsoft; VERIFICADO 4-oct-2026) | Región del deploy; "Global inference" puede procesar fuera (ver Sección 5) | A VERIFICAR | Microsoft lista OpenAI como sub-procesador: [Sección 2](#ven-sec2).3 | VERIFICADO |
| **AWS Bedrock** | llm | Publica DPA (AWS) | A VERIFICAR | AWS en DPF: NO VERIFICADO (ver Sección 6) | Región del deploy | `provider_data_share` → prompts a Anthropic, retención 30 días trust & safety; `default`/`none` → no (VERIFICADO) | `https://aws.amazon.com/compliance/data-protection/` (lista: A VERIFICAR) | A VERIFICAR |
| **Mistral** | llm | Publica DPA — A VERIFICAR | A VERIFICAR (trust portal con NDA) | A VERIFICAR | UE (Francia) | A VERIFICAR | `https://mistral.ai/legal/` | A VERIFICAR |
| **Cohere** | llm | **NO publica DPA — solo NDA** (VERIFICADO) | A VERIFICAR | A VERIFICAR | US/CA: A VERIFICAR | A VERIFICAR | no publica lista | A VERIFICAR |
| **HuggingFace** | llm | Publica DPA — A VERIFICAR | A VERIFICAR | A VERIFICAR | US/UE: A VERIFICAR | A VERIFICAR | `https://huggingface.co/legal/` | A VERIFICAR |

### 3.2 STT/ASR

| Nombre | Categoría | DPA (firmable?) | Certificaciones | DPF/adecuación | Región default | Retención/training default | Sub-processors (URL) | Estado |
|---|---|---|---|---|---|---|---|---|
| **AssemblyAI** | stt | Publica DPA — A VERIFICAR | A VERIFICAR | A VERIFICAR | US: A VERIFICAR | ZDR en LLM Gateway (VERIFICADO); retención general: A VERIFICAR | `https://www.assemblyai.com/legal` (cadena Bedrock: [Sección 2](#ven-sec2).5) | A VERIFICAR |
| **Deepgram** | stt | Publica DPA — A VERIFICAR | A VERIFICAR | A VERIFICAR | US: A VERIFICAR | A VERIFICAR | `https://deepgram.com/legal/` | A VERIFICAR |
| **ElevenLabs** | stt | Publica DPA — A VERIFICAR | A VERIFICAR (trust portal con NDA) | A VERIFICAR | US/UE: A VERIFICAR | A VERIFICAR | `https://elevenlabs.io/legal` | A VERIFICAR |

### 3.3 IdP

| Nombre | Categoría | DPA (firmable?) | Certificaciones | DPF/adecuación | Región default | Retención/training default | Sub-processors (URL) | Estado |
|---|---|---|---|---|---|---|---|---|
| **Auth0 / Okta** | idp | Publica DPA (firmable) | A VERIFICAR | SÍ en DPF (VERIFICADO 4-oct-2026) | US/UE (multi-región) | A VERIFICAR | `https://auth0.com/legal/` | VERIFICADO |
| **Clerk** | idp | Publica DPA (firmable) | A VERIFICAR | SÍ en DPF (VERIFICADO 4-oct-2026) | US/UE: A VERIFICAR | A VERIFICAR | `https://clerk.com/legal` | VERIFICADO |

### 3.4 Infra

| Nombre | Categoría | DPA (firmable?) | Certificaciones | DPF/adecuación | Región default | Retención/training default | Sub-processors (URL) | Estado |
|---|---|---|---|---|---|---|---|---|
| **AWS** | infra | Publica DPA (firmable) | A VERIFICAR | **NO VERIFICADO** en DPF (ver Sección 6) | Multi-región (deploy) | A VERIFICAR | `https://aws.amazon.com/compliance/data-protection/` (lista: A VERIFICAR) | A VERIFICAR |
| **GCP** | infra | Publica DPA (CFE) | A VERIFICAR | SÍ en DPF (Google; VERIFICADO 4-oct-2026) | Multi-región (deploy) | A VERIFICAR | `https://cloud.google.com/terms/sccs/subprocessors` (A VERIFICAR) | VERIFICADO |
| **Azure** | infra | Publica DPA (Microsoft) | A VERIFICAR | SÍ en DPF (Microsoft; VERIFICADO 4-oct-2026) | Multi-región (deploy); Global/DataZone fuera | A VERIFICAR | `https://www.microsoft.com/licensing/docs/view/Microsoft-Products-and-Services-Data-Protection-Addendum-DPA` | VERIFICADO |
| **Cloudflare** | infra | Publica DPA (firmable) | A VERIFICAR | DPF: A VERIFICAR (no confirmado en esta captura) | Edge global (tráfico en nodos de múltiples países) | A VERIFICAR | `https://www.cloudflare.com/cloudflare_subprocessors/` | A VERIFICAR |
| **Vercel** | infra | Publica DPA — A VERIFICAR | A VERIFICAR | A VERIFICAR | Edge global | A VERIFICAR | `https://vercel.com/legal` | A VERIFICAR |
| **Netlify** | infra | Publica DPA — A VERIFICAR | A VERIFICAR | SÍ en DPF (VERIFICADO 4-oct-2026) | Edge global | A VERIFICAR | `https://www.netlify.com/legal/` | VERIFICADO |
| **Supabase** | infra | Publica DPA — A VERIFICAR | A VERIFICAR | A VERIFICAR | Multi-región (deploy) | A VERIFICAR | `https://supabase.com/legal` | A VERIFICAR |
| **MongoDB** | infra | Publica DPA (firmable) | A VERIFICAR | SÍ en DPF (VERIFICADO 4-oct-2026) | Multi-región (Atlas) | A VERIFICAR | `https://www.mongodb.com/legal/` | VERIFICADO |
| **Snowflake** | infra | Publica DPA (firmable) | A VERIFICAR | SÍ en DPF (VERIFICADO 4-oct-2026) | Multi-región (deploy) | A VERIFICAR | `https://www.snowflake.com/legal/` | VERIFICADO |

### 3.5 Observabilidad

| Nombre | Categoría | DPA (firmable?) | Certificaciones | DPF/adecuación | Región default | Retención/training default | Sub-processors (URL) | Estado |
|---|---|---|---|---|---|---|---|---|
| **Datadog** | observabilidad | Publica DPA (firmable) | A VERIFICAR (trust portal con NDA) | A VERIFICAR | US/UE (deploy) | A VERIFICAR | `https://www.datadoghq.com/legal/subprocessors/` | A VERIFICAR |
| **Sentry** | observabilidad | Publica DPA (firmable) | A VERIFICAR | SÍ en DPF (VERIFICADO 4-oct-2026) | US/UE (deploy) | A VERIFICAR | `https://sentry.io/legal/dpa/` | VERIFICADO |
| **PostHog** | observabilidad | Publica DPA — A VERIFICAR | A VERIFICAR (trust portal con NDA) | A VERIFICAR | US/UE (deploy); self-host opcional | A VERIFICAR | `https://posthog.com/legal` | A VERIFICAR |

### 3.6 Pagos

| Nombre | Categoría | DPA (firmable?) | Certificaciones | DPF/adecuación | Región default | Retención/training default | Sub-processors (URL) | Estado |
|---|---|---|---|---|---|---|---|---|
| **Stripe** | pagos | Publica DPA (firmable) | A VERIFICAR (PCI DSS / SOC: A VERIFICAR) | SÍ en DPF (VERIFICADO 4-oct-2026) | US/UE (data residency EU opcional) | A VERIFICAR | `https://stripe.com/legal/dpa` (sub-procesadores: A VERIFICAR) | VERIFICADO |

### 3.7 Proveedores chinos

| Nombre | Categoría | DPA (firmable?) | Certificaciones | DPF/adecuación | Región default | Retención/training default | Sub-processors (URL) | Estado |
|---|---|---|---|---|---|---|---|---|
| **DeepSeek** | chino | **Sin DPA público** (VERIFICADO) | Sin evidencia | NO adecuada (RPCh; VERIFICADO) | RPCh — foro Hangzhou (VERIFICADO) | Procesa y almacena en RPCh (VERIFICADO) | sin lista pública (VERIFICADO) | VERIFICADO |
| **Alibaba / Qwen** | chino | Sin DPA público verificado | A VERIFICAR | NO adecuada (RPCh) | RPCh; "Global inference" puede procesar fuera (Sección 5) | A VERIFICAR | `https://www.alibabacloud.com/legal` (A VERIFICAR) | A VERIFICAR |
| **Baidu** | chino | Sin DPA público verificado | A VERIFICAR | NO adecuada (RPCh) | RPCh | A VERIFICAR | A VERIFICAR | A VERIFICAR |
| **Moonshot / Kimi** | chino | Sin DPA público verificado | A VERIFICAR | NO adecuada (RPCh) | RPCh | A VERIFICAR | A VERIFICAR | A VERIFICAR |
| **Z.ai (GLM)** | chino | Sin DPA público verificado | A VERIFICAR | NO adecuada (RPCh) | RPCh | A VERIFICAR | A VERIFICAR | A VERIFICAR |
| **MiniMax** | chino | Sin DPA público verificado | A VERIFICAR | NO adecuada (RPCh) | RPCh | A VERIFICAR | A VERIFICAR | A VERIFICAR |

<a id="ven-sec4"></a>
## Sección 4 — Transferencias: el mapa 2026

### 4.1 Lista de adecuación de la Comisión (verificada a 2026-10-05)

Países/territorios con decisión de adecuación vigente (Art. 45 GDPR):
**Andorra · Argentina · Brasil (26-ene-2026) · Canadá · Feroe · Guernsey ·
Israel · Isla de Man · Japón · Jersey · Nueva Zelanda · Corea del Sur ·
Suiza · Reino Unido (RSU) · Estados Unidos (SOLO si DPF certificado) ·
Uruguay · EPO.**

Ni **China** ni **Singapur** tienen adecuación.

Nota de fidelidad: la primera entrada del brief llegó con un error de
transcripción (el primer país de la lista es **Andorra**) y "EPO" se transcribió
tal como llegó; ambas deben confirmarse con `source-verifier` antes de citarse
(ver [Sección 6](#ven-sec6)).

### 4.2 DPF (Data Privacy Framework, Estados Unidos)

- **Estado a oct-2026:** vigente. Segunda revisión periódica prevista **2027**.
  Hay challenge ante el TJUE; **no invalidado** a la fecha de captura.
- **Uso correcto:** verificar en la **lista oficial** del DPF que la empresa
  esté **activa** Y que la **cobertura** incluya tus datos (cobertura HR vs
  non-HR). Si falla cualquiera de los dos → **SCCs + TIA**.
- La membresía en el DPF **no se presume** por estar "en EEUU": se consulta el
  registro (ver [Sección 3](#ven-sec3) para el estado por empresa).

### 4.3 Chile — transferencias internacionales

- **Arts. 27–28 de la Ley 19.628 reformada (Ley 21.719).** La Agencia de
  Protección de Datos **no existe todavía** → **no hay lista de países
  adecuados** publicada.
- **PERO** el **19-dic-2025** se publicaron en el **Diario Oficial** las
  **cláusulas contractuales modelo** (CMCM): válidas hasta que la Agencia
  actúe → **hay vía de salvaguarda** para transferencias (p. ej. a EEUU).
- **Estados Unidos** está marcado como **barrera** en el informe de 2024.

<a id="ven-sec5"></a>
## Sección 5 — Lo que NO se puede verificar estáticamente

Límites identificados por el research. La skill debe **rendirse** aquí en lugar
de inventar un veredicto:

1. **Región real en runtime.** La config no garantiza dónde se procesó cada
   request: Azure Global/DataZone y "Global inference" de Alibaba pueden
   procesar fuera de la región declarada.
2. **Qué datos se enviaron de verdad.** ¿El prompt llevaba el nombre? ¿El
   audio era identificable? El código puede no reflejar el payload real.
3. **Si el DPA firmado existe y cubre el alcance.** Cohere ni siquiera lo
   publica — NDA.
4. **Calidad del TIA.** Que exista una Transfer Impact Assessment no dice que
   sea correcta.
5. **Base legal real de cada tratamiento.** La declaración en config no prueba
   el consentimiento ni el interés legítimo.
6. **Que la lista no haya cambiado desde la captura.** El inventario es de
   2026-10-05; los DPAs y estados mutan en meses (ver cabecera de vigencia).

<a id="ven-sec6"></a>
## Sección 6 — Fuentes no verificadas

Fuentes que el research marcó `INDIRECTA` o `A VERIFICAR`, y por qué:

| Fuente | Marca | Motivo |
|---|---|---|
| AWS en el DPF | NO VERIFICADO | La entrada en el registro oficial no se confirmó en esta captura |
| Certificaciones de OpenAI, Mistral, ElevenLabs, Datadog, PostHog | A VERIFICAR | Trust portal con NDA; el claim público no se pudo contrastar |
| PIPC (Corea del Sur) sobre DeepSeek | A VERIFICAR | Comunicación de la autoridad coreana no capturada en el pack |
| Textos completos de la Ley de Inteligencia Nacional / Ley de Contraespionaje (RPCh) | A VERIFICAR | Citados por su Art. 7 / obligación de cooperación; el texto completo no está capturado |
| URL exacta de listas de sub-procesadores (Azure "operated models", AWS Bedrock, AssemblyAI) | A VERIFICAR | El anexo exacto debe re-consultarse con `source-verifier` |
| Entradas "Andorra" y "EPO" de la lista de adecuación | A VERIFICAR | Citadas del brief (la primera corregida de un error de transcripción); confirmar nombre/estado antes de citar |