# Cómo contribuir

Gracias por querer mejorar `legal-audit`. Este proyecto audita cumplimiento
legal, así que la barra de rigor es más alta que la de un proyecto común.

## Principios no negociables

1. **Nunca redactar ley de memoria.** Toda norma que entre al pack de
   evidencia debe traer: URL de la fuente oficial, artículo, cita textual,
   fecha de vigencia y fecha de captura. Si no está la cita, no entra.
2. **La integridad del pack de evidencia es crítica.** Cambiar un archivo de
   `skills/legal-audit/references/sources/` requiere revisión de una segunda
   persona y actualización del hash registrado.
3. **La herramienta nunca certifica cumplimiento.** Se aceptan aportes que
   mejoren la evidencia y la trazabilidad; se rechazan los que prometan
   emitir "cumple la ley".
4. **Detectores deterministas con stdlib.** Los checks automatizables no
   deben depender de servicios externos ni de juicio del LLM.

## Flujo de pull requests

- Hacé fork y una rama descriptiva (`fix/...`, `feat/...`, `docs/...`).
- Un cambio conceptual por PR. Si el PR toca más de un área no relacionada,
  probablemente hay que partirlo.
- Describí: qué cambia, por qué, y cómo lo verificaste.
- Los cambios en el pack de evidencia deben citar la fuente oficial en la
  descripción del PR.

## Cambios al pack de evidencia

1. Actualizá el archivo de la norma en `references/sources/`.
2. Actualizá el `source-verifier` / hash correspondiente.
3. Escribí explícitamente si el estado de vigencia cambió
   (`FRESH` / `STALE` / `CHANGED`).
4. Pedí una segunda revisión antes de mergear.

## Estilo

- Documentación en español neutro.
- **Emojis decorativos en prosa: prohibidos.** No son semántica.
- **Excepción — avisos de advertencia** dentro de los archivos de referencia
  (`references/`): se permiten `⚠️` (advertencia) y `❌` (afirmación prohibida).
  Son semántica, no decoración: marcan un riesgo o una frase que la skill no
  debe emitir.
- Commits en imperativo y con alcance claro.
- Preferí tablas y ejemplos con `archivo:línea` antes que prosa.

## Licencia de las contribuciones

Al contribuir aceptás que tu aporte se licencie bajo Apache-2.0, según los
términos del repositorio.
