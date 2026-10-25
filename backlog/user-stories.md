# Backlog · Take a Break

Fuente de verdad de las historias de usuario del TPO. `Crear-Issues.ps1` lee este archivo y crea un
issue por cada historia `US-NN` en `DesarrolloApps1/tpo-da1`, y los agrega al Project *DA1 | Board*.

Reglas del backlog:

- **Historias grandes y verticales.** Cada integrante tiene asistentes de IA, así que una historia
  cubre una funcionalidad completa (dominio, datos y pantalla) en vez de partirla en tareas chicas.
- **Pocas dependencias.** Todo depende solo de US-00 (arquitectura). Las interfaces de dominio,
  los DTOs y el `UiState` ya están definidos en el esqueleto, así que cada uno trabaja contra esos
  contratos con *fakes* y nadie espera a nadie. Los tests son la única fase que va después.
- **Stack único.** Todo en Kotlin, compilado y ejecutado desde Android Studio (app) e IntelliJ o
  Android Studio (backend Ktor). Nada de Java, XML de layouts ni otros lenguajes.
- **Sprints.** 0: arquitectura · 1 y 2: funcionalidades en paralelo · 3: testing, entrega y defensa.
- **Historia grande, commits chicos.** La consigna (4.14 y 9) evalúa la evolución del repo y
  penaliza concentrar todo en pocos commits antes de la entrega. Cada historia se entrega en varios
  PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- **Uso de IA (consigna, sección 8).** Se puede usar IA, pero el autor tiene que poder explicar y
  modificar todo lo que integra. Cada PR responde en su descripción las seis preguntas de la
  consigna (la plantilla de PR sale de US-00).

Trazabilidad con la consigna, Etapa 2:

| Consigna | Dónde se cubre |
|---|---|
| 7.1 Requisitos comprometidos RF01–RF04 | RF01: US-01 · RF02: US-02, US-05 · RF03: US-03, US-04, US-06 · RF04: US-03, US-04, US-06 |
| 7.1 Kotlin, Compose, navegación, estado, ViewModel, MVVM, Clean Architecture, repositorios | US-00, US-08 |
| 7.1 Persistencia, Room, Retrofit, offline, capacidades del dispositivo | US-01, US-04, US-06 |
| 7.2 Casos de uso, errores, navegación, estado, persistencia, conectividad limitada | US-04, US-08, US-09, US-10, US-12 |
| 7.3 Carga, contenido, vacío, error, offline, permisos rechazados, recuperación | US-02, US-05, US-06, US-08, US-11 |
| 7.4 Repositorio, README e instrucciones, arquitectura final, decisiones, limitaciones | US-00, US-12 |
| 7.5 Demo y defensa | US-01 (pausa simulada), US-12 (guion y ensayo) |
| 8 Uso de IA | Plantilla de PR (US-00) y definición de terminado de cada historia |

Cada historia termina con la misma **definición de terminado**: PR parciales a `dev` con commits
chicos, plantilla de PR completa con 1 revisión, CI en verde y el autor capaz de explicar su código.

| Dev | Usuario de GitHub | Área |
|---|---|---|
| Joa | `JoaVelazquez` | Arquitectura, integración, acceso y perfil |
| Valentin | `valentinpapa12` | Detección de pausas, reglas y actividad |
| Juan | `Juanjerezz` | Backend, sincronización y canjes |
| Abril | `amaci003` | UI/UX: onboarding, inicio, explorar y canje |

---

# ÉPICA 0 · Arquitectura

### US-00 · Arquitectura base de la app y del backend

```markdown
**Dev:** Joa · **Sprint:** 0 · **Puntos:** 8 · **Labels:** `tipo:infra` `area:app` `area:backend` `bloqueante`

## Historia

**Como** integrante del equipo,
**quiero** una arquitectura base que compile, arranque y defina todos los contratos entre capas,
**para** poder desarrollar mi parte en paralelo sin pisarme con los demás y sin esperar a nadie.

## Contexto

Es la única historia bloqueante del backlog. El esqueleto ya está en los PR
DesarrolloApps1/tpo-da1#1 y DesarrolloApps1/tpo-da1-backend#1: esta historia cubre terminarlo,
revisarlo con el equipo y mergearlo a `dev`. Sigue la sección 7 (Arquitectura) del documento.

## Alcance

### App (`tpo-da1`, Kotlin + Jetpack Compose, abre directo en Android Studio)
- [ ] Proyecto Gradle con version catalog, `minSdk 28`, JDK = JBR de Android Studio.
- [ ] Paquetes `ui/`, `presentation/`, `domain/`, `data/`, `platform/`, `di/` con la regla de dependencias de Clean Architecture (el dominio no importa nada de Android).
- [ ] `AppContainer` con inyección manual de base de datos, API, repositorios y casos de uso.
- [ ] Interfaces de repositorio y firmas de todos los casos de uso (`SyncBreaks`, `GetHomeSummary`, `GetRewards`, `RedeemReward`, `SetGoal`, `GetBreakHistory`, `GetRedemptions`).
- [ ] Room (entidades, DAOs, índice único por `startedAt`), DataStore, Retrofit con los 4 endpoints y mappers.
- [ ] `UiState` (Loading / Content / Empty / Error + offline), `StateContent` y un ViewModel por pantalla.
- [ ] Tema de Compose con los tokens de Figma, navegación type-safe con las 3 pestañas y pantallas placeholder.
- [ ] Workers registrados (`BreakSyncWorker`, `CatalogSyncWorker`, `RedemptionSyncWorker`) y manifest con los permisos del documento.
- [ ] La lógica de negocio queda como `TODO("...")` con el responsable indicado, nunca en el camino de arranque.

### Backend (`tpo-da1-backend`, Ktor + Exposed + PostgreSQL)
- [ ] Capas `routes → service → repository → Exposed`, igual que en la app.
- [ ] Endpoints declarados con sus DTOs (mismos nombres de campo que en la app), StatusPages y JWT configurado.
- [ ] `docker-compose.yml` con Postgres local, `Dockerfile` para Render y datos semilla.
- [ ] Sacar del repo la carpeta `bin/` (salida de compilación que quedó commiteada) y agregarla al `.gitignore`.

### Equipo
- [ ] GitHub Actions: `./gradlew assembleDebug testDebugUnitTest` en la app y `./gradlew test` en el backend en cada PR a `dev`.
- [ ] Plantilla de PR (`.github/pull_request_template.md`) en los dos repos: qué historia cubre, cómo se probó y las seis preguntas de la consigna sobre uso de IA (qué problema resuelve, qué capa modifica, qué dependencias agrega, si hay una alternativa más simple, cómo se comprobó que funciona y qué pasa si falla).
- [ ] README de cada repo: cómo correrlo, mapa de capas y tabla de pendientes por responsable.
- [ ] Protección de `dev` y `main`: PR obligatorio con al menos 1 revisión.

## Criterios de aceptación

- [ ] Clonar `tpo-da1`, abrirlo en Android Studio y darle *Run* instala la app en un emulador API 28 y API 35, y se puede navegar por las 3 pestañas sin crashes.
- [ ] `docker compose up -d` + `./gradlew run` levanta el backend y `GET /rewards` devuelve el catálogo semilla.
- [ ] La app en el emulador consume el backend local (`10.0.2.2`) usando el `BASE_URL` de `BuildConfig`.
- [ ] El CI corre verde en ambos repos.
- [ ] Ninguna clase de `domain/` importa `android.*`.
- [ ] Los 4 integrantes revisaron el PR y saben dónde va su código.

## Depende de

Nada. Todas las demás historias dependen de esta.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

---

# ÉPICA 1 · Pausas y puntos

### US-01 · Detección pasiva de pausas y validación con las reglas de puntos

```markdown
**Dev:** Valentin · **Sprint:** 1 · **Puntos:** 13 · **Labels:** `tipo:feature` `area:app`

## Historia

**Como** usuario que quiere usar menos el celular,
**quiero** que la app detecte sola cuándo dejé el teléfono bloqueado y me dé puntos por esa pausa,
**para** ser recompensado sin tener que acordarme de iniciar nada.

## Contexto

Es el núcleo de la app (RF01). Implementa los `TODO` de `UsageEventsReader`, `Pause.minutesOutside`,
`SyncBreaks` y el flujo completo de `BreakSyncWorker` descrito en la sección 7.3 del documento.

## Alcance

- [ ] `AndroidUsageEventsReader`: consultar `UsageStatsManager.queryEvents` desde el checkpoint de DataStore y armar las pausas cerradas desde `KEYGUARD_SHOWN` hasta `KEYGUARD_HIDDEN`, usando solo los 4 tipos de evento del documento.
- [ ] Si la pantalla se enciende por una notificación y se apaga sin desbloquear, la pausa continúa.
- [ ] `Pause.minutesOutside(restFrom = 23, restTo = 9)`: descontar el horario de descanso aunque la pausa cruce la medianoche o dure varios días.
- [ ] `BreakRules.points`: 1 punto por minuto válido, mínimo 30 min de lunes a viernes y 45 min el fin de semana, tope diario de 240 puntos.
- [ ] `SyncBreaks`: aplicar las reglas a cada pausa acumulando los puntos del día, asignar el `BreakStatus` con el motivo cuando no suma (muy corta, horario de descanso, tope alcanzado) y guardar con *upsert*.
- [ ] `BreakSyncWorker`: leer → validar y guardar en Room → actualizar el checkpoint → notificar. Corre cada 15 min y también al abrir la app.
- [ ] `AndroidNotifier`: canal propio y notificación "Break validado: +N pts", que agrega "Ya te alcanza para <premio meta>" cuando el saldo llega a la meta. Al tocarla abre Inicio con el estado validado (Figma 09 y 27). Solo si la pausa sumó, el permiso está otorgado y las notificaciones están activas en Perfil.
- [ ] Chequeo del permiso de *Acceso a datos de uso* expuesto como `Flow<Boolean>` para que la UI de permisos (US-05) lo consuma.
- [ ] **Prueba técnica de la detección** (sección "Testear" del documento), al principio del sprint: leer los eventos de bloqueo en el emulador y en 3 teléfonos de marcas distintas y registrar en `docs` si llegan completos.
- [ ] **Pausa simulada para la demo**, solo en el build `debug`: un `UsageEventsReader` falso, elegible desde un menú oculto, que genera una pausa de N minutos. Permite mostrar el ciclo completo en la defensa sin esperar una hora y sirve para los tests.

## Criterios de aceptación

- [ ] Con el teléfono bloqueado 60 min un martes entre las 9 y las 23 h, la pausa aparece válida con +60 puntos y llega la notificación a más tardar 30 min después de desbloquear, o apenas se abre la app.
- [ ] Funciona igual en modo avión.
- [ ] Una pausa de 22:30 a 23:45 suma solo 30 minutos; una de 23:30 a 08:00 queda en el historial con 0 puntos y su motivo.
- [ ] Una pausa de 40 min un sábado no suma; una de 50 min sí.
- [ ] Nunca se superan los 240 puntos en un día, aunque haya muchas pausas válidas.
- [ ] Forzar el cierre de la app entre que se guarda la pausa y se actualiza el checkpoint no pierde ni duplica la pausa (RNF04).
- [ ] No se lee ni se guarda ningún nombre de app (RNF03) y el manifest no declara servicios en primer plano (RNF01).
- [ ] Las pausas nunca salen del teléfono: ningún request al backend las incluye (sección 8 del documento).
- [ ] La pausa simulada no existe en el build `release`.

## Depende de

US-00.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

### US-02 · Actividad, saldo, meta y racha

```markdown
**Dev:** Valentin · **Sprint:** 2 · **Puntos:** 8 · **Labels:** `tipo:feature` `area:app`

## Historia

**Como** usuario,
**quiero** ver mi saldo, cuánto me falta para mi meta, mi racha de días y el historial de mis pausas,
**para** entender cómo vengo y mantenerme motivado aunque no tenga conexión.

## Contexto

Cubre RF02. Completa los casos de uso de lectura sobre las pausas y la pantalla Actividad.
La pantalla de Inicio la dibuja Abril (US-05) consumiendo el `HomeSummary` que sale de acá.

## Alcance

- [ ] `GetHomeSummary`: saldo = puntos de pausas − puntos de canjes no reembolsados (no se guarda, se calcula combinando los `Flow` de Room), avance hacia la meta y racha.
- [ ] Racha: días consecutivos con al menos una pausa válida, contando hoy solo si ya hubo una.
- [ ] `SetGoal`: elegir un premio como meta y guardarlo en DataStore, junto con la meta diaria de minutos que alimenta el anillo de Inicio.
- [ ] Lo que falta para la meta se expone en puntos y en horas ("te falta 1 h"), porque la moneda es el tiempo (principio P2).
- [ ] `GetBreakHistory`: pausas de los últimos 30 días agrupadas por día, con puntos y motivo cuando no sumó.
- [ ] `ActivityViewModel` + `ActivityScreen` según las pantallas 23 y 24 de Figma: gráfico de minutos sin pantalla por día (el gráfico que se movió de Inicio a Actividad), lista agrupada por día, total del día, chip de racha y estado vacío para usuarios nuevos.
- [ ] Textos del motivo en lenguaje simple ("Fue de noche, no suma", "Muy corta: mínimo 30 min"), para que ninguna regla quede oculta (principio P4).

## Criterios de aceptación

- [ ] En modo avión, Inicio y Actividad muestran saldo, meta, racha y las pausas de los últimos 30 días.
- [ ] Cada pausa que no sumó indica el motivo.
- [ ] Al canjear un premio el saldo baja al instante, y si el canje se reembolsa vuelve a subir, sin reiniciar la app.
- [ ] Un usuario sin pausas ve el estado vacío de la pantalla 24, no una lista vacía.
- [ ] La racha se corta si pasa un día entero sin pausas válidas.

## Depende de

US-00. Usa las pausas que guarda US-01, pero se desarrolla con pausas cargadas a mano en Room o con un repositorio *fake*.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

---

# ÉPICA 2 · Catálogo y canjes

### US-03 · API del backend: catálogo, canjes y despliegue

```markdown
**Dev:** Juan · **Sprint:** 1 · **Puntos:** 8 · **Labels:** `tipo:feature` `area:backend`

## Historia

**Como** comercio adherido,
**quiero** que mis premios estén publicados en la plataforma y que cada canje genere un código válido por un tiempo limitado,
**para** que los usuarios lleguen a mi local y yo pueda verificar el descuento.

## Contexto

Backend en Ktor + Exposed + PostgreSQL (`tpo-da1-backend`), todo en Kotlin. Los endpoints y los
DTOs ya están declarados en el esqueleto; esta historia implementa la lógica y lo deja publicado.
No hay pagos reales: los comercios y premios son datos semilla.

## Alcance

- [ ] `Seed.kt`: 5 o 6 comercios de ejemplo con nombre, dirección, barrio, horario y coordenadas reales de CABA, y 2 o 3 premios cada uno con stock diario (se repone cada día). Idempotente.
- [ ] `GET /rewards?since=`: catálogo completo o solo lo modificado desde `since` (incluye premios dados de baja para que la app los borre).
- [ ] `POST /redemptions`: recibe el UUID generado en el teléfono. Idempotente: 201 si es nuevo, 200 con el mismo canje si es un reintento, 409 si no hay stock. Descuenta stock en una transacción y genera un código de 6 caracteres que vence a los 10 minutos.
- [ ] `GET /redemptions/{id}`: estado del canje (`ACTIVE`, `USED`, `EXPIRED`, `REJECTED`), 404 si no existe.
- [ ] Errores en JSON uniformes con StatusPages.
- [ ] Despliegue en Render con PostgreSQL administrado, variables `DB_URL` y `JWT_SECRET` por entorno.
- [ ] README con los endpoints, ejemplos de request/response y cómo correrlo local.

## Criterios de aceptación

- [ ] Mandar dos veces el mismo `POST /redemptions` crea un solo canje y descuenta stock una sola vez.
- [ ] Dos canjes simultáneos del último premio en stock: uno recibe 201 y el otro 409.
- [ ] Un código consultado después de 10 minutos figura como `EXPIRED`.
- [ ] `GET /rewards?since=<fecha>` devuelve solo lo que cambió después de esa fecha.
- [ ] La API responde por HTTPS en Render y la app en un emulador puede consumirla cambiando solo `BASE_URL`.
- [ ] Ningún endpoint recibe ni guarda pausas: el servidor solo conoce comercios, premios, usuarios y canjes.

## Depende de

US-00.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

### US-04 · Sincronización offline-first del catálogo y canjes pendientes

```markdown
**Dev:** Juan · **Sprint:** 2 · **Puntos:** 13 · **Labels:** `tipo:feature` `area:app`

## Historia

**Como** usuario que muchas veces no tiene señal,
**quiero** ver el catálogo guardado y poder canjear igual aunque esté sin conexión,
**para** que la falta de red nunca me impida usar mis puntos.

## Contexto

Cubre la estrategia offline-first de la sección 8 y la parte de datos de RF03 y RF04. Room es la
única fuente de verdad: la red actualiza Room y la UI solo observa Room. Implementa los `TODO` de
`RedemptionRepositoryImpl` y los workers de sincronización.

## Alcance

- [ ] `CatalogSyncWorker`: cada 6 h con red, y al abrir Explorar si pasó más de 1 h desde la última sincronización. Pide `GET /rewards?since=` y aplica altas, cambios y bajas en Room en una transacción.
- [ ] Guardar la hora de la última sincronización en DataStore y exponerla para el aviso "Actualizado hace X" de la UI.
- [ ] `RedeemReward` / `RedemptionRepositoryImpl.redeem`: guardar el canje `PENDING` con UUID propio (los puntos quedan reservados), mandarlo a la API y pasarlo a `ACTIVE` con el código. Sin red, dejarlo pendiente y agendar `RedemptionSyncWorker`.
- [ ] `RedemptionSyncWorker`: con la restricción de red y *backoff* exponencial reenvía los pendientes. Cuando se confirma, notifica "Canje confirmado" con el código. Si el servidor lo rechaza porque el premio se agotó o se dio de baja, el canje queda `REFUNDED` ("devuelto"), los puntos vuelven al saldo y se avisa (Figma 22).
- [ ] Para el catálogo y el stock manda el servidor: el stock se vuelve a validar al canjear aunque el catálogo guardado esté viejo.
- [ ] `AndroidNetworkMonitor` como `Flow<Boolean>` usado por los ViewModels para la marca offline.
- [ ] Pantalla **Mis canjes** (Figma 26): canjes activos con cuenta regresiva, pendientes, usados y reembolsados, con su estado consultado por `GET /redemptions/{id}` cuando hay red.
- [ ] Manejo de errores de red y del servidor mapeado a errores de dominio, sin excepciones de Retrofit fuera de `data/`.

## Criterios de aceptación

- [ ] Con conexión, el código de canje aparece en menos de 3 segundos.
- [ ] En modo avión el canje queda pendiente con los puntos reservados, y al volver la red se confirma solo, sin abrir la app.
- [ ] Al confirmarse un canje pendiente llega una notificación con el código.
- [ ] Si el premio se agotó mientras el canje estaba pendiente, los puntos vuelven al saldo y llega un aviso.
- [ ] Reintentar un canje nunca crea un canje duplicado en el backend.
- [ ] Sin conexión, Explorar muestra el catálogo guardado con la hora de la última actualización. La primera vez sin red y sin catálogo guardado, muestra el error con *Reintentar* (Figma 16); Inicio funciona igual.
- [ ] La primera vez que se abre la app con red, el catálogo semilla aparece sin intervención del usuario.

## Depende de

US-00. Se desarrolla contra el backend local con los DTOs del esqueleto; no necesita esperar a que US-03 esté desplegado.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

---

# ÉPICA 3 · Experiencia de usuario

### US-05 · Onboarding, permisos e Inicio

```markdown
**Dev:** Abril · **Sprint:** 1 · **Puntos:** 8 · **Labels:** `tipo:feature` `area:app` `ui`

## Historia

**Como** usuario nuevo,
**quiero** entender en pocos segundos qué hace la app, otorgar los permisos necesarios sabiendo para qué sirven y ver mi progreso apenas entro,
**para** empezar a sumar puntos sin fricción.

## Contexto

Pantallas 01 a 12 de Figma. Diseño minimalista inspirado en pasito.app: verde bosque y lima sobre
crema, botones píldora, Bricolage Grotesque para títulos y DM Sans para texto. Todo en Jetpack
Compose; la UI no decide nada, solo dibuja el `UiState` del ViewModel.

## Alcance

- [ ] Fuentes Bricolage Grotesque y DM Sans en `ui/theme/Type.kt` y ajuste fino de colores, formas y espaciados contra Figma.
- [ ] Splash (01) y onboarding de 3 pasos (02–04) con la ecuación "1 hora = 1 recompensa", que solo se muestra la primera vez (marca en DataStore). Después sigue la pantalla de acceso (05, US-07) y recién ahí los permisos, como en el flujo de Figma.
- [ ] Pantalla de permisos (06): *Acceso a datos de uso* (obligatorio; abre Ajustes y detecta la vuelta), notificaciones (recomendado; `POST_NOTIFICATIONS` en API 33+) y explicación de por qué se pide cada uno.
- [ ] Pantalla de permiso rechazado (07): explica qué se pierde y ofrece *Reintentar* o *Entrar igual a ver premios*, sin bloquear el resto de la app.
- [ ] Si se rechazan las notificaciones, la app sigue sumando y lo indica en Inicio y en Perfil, sin insistir.
- [ ] Inicio (08–12): tarjeta de saldo con el número grande en lima y el anillo del avance del día contra la meta diaria; tarjeta de meta con lo que falta en puntos y en horas, que muestra el botón *Canjear* cuando ya alcanza (09); sección "Te alcanza hoy" con los premios que ya se pueden canjear; racha; y los estados cargando (11), vacío (10), validado (09) y offline (12) con el aviso "Sin conexión · tus pausas se siguen contando".
- [ ] Componentes reutilizables: `PillButton`, fila de premio (chip lima si alcanza, gris si no), chip de racha, banner offline.
- [ ] Previews de Compose de cada estado con datos *fake*.

## Criterios de aceptación

- [ ] Una persona que nunca vio la app llega a Inicio con los permisos otorgados en menos de 1 minuto.
- [ ] Si rechaza el acceso a datos de uso, ve la pantalla 07 y puede reintentar o entrar a ver premios; la app no crashea ni queda en blanco.
- [ ] Inicio muestra los 5 estados de Figma según el `UiState` del ViewModel.
- [ ] La acción principal de cada pantalla mide 56 × 320 dp y está abajo, al alcance del pulgar; la barra inferior tiene 3 destinos de 120 dp (ley de Fitts, sección 6 del documento).
- [ ] Objetivos táctiles de 48 dp o más, contraste AA y `contentDescription` en todos los íconos (RNF05, RNF06).
- [ ] Con la fuente del sistema al 200 % ningún texto queda cortado.

## Depende de

US-00. Los datos de Inicio vienen de `GetHomeSummary` (US-02) y "Te alcanza hoy" de `GetRewards` (US-04), pero se dibujan con datos *fake* mientras tanto.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

### US-06 · Explorar premios con mapa y lista, detalle y canje

```markdown
**Dev:** Abril · **Sprint:** 2 · **Puntos:** 13 · **Labels:** `tipo:feature` `area:app` `ui`

## Historia

**Como** usuario con puntos acumulados,
**quiero** ver en un mapa y en una lista qué premios tengo cerca, saber cuáles me alcanzan y canjear uno con un gesto,
**para** ir al local y usar mi descuento en el momento.

## Contexto

Cubre la UI de RF03 y RF04 (pantallas 13 a 22 de Figma). Canjear desde Inicio tiene que llevar
como máximo 2 toques y 1 gesto de mantener presionado (RNF05).

## Alcance

- [ ] Google Maps Compose con marcadores de los comercios; API key fuera del repo (`local.properties` → `BuildConfig` / manifest placeholder).
- [ ] `FusedLocationProvider`: una sola lectura en primer plano, bajo demanda; nunca en segundo plano.
- [ ] Hoja inferior con la lista de premios sobre el mapa: el mapa orienta y la lista, al alcance del pulgar, es la que se toca. Cada fila muestra ícono, nombre, comercio, distancia y el chip de puntos (lima si alcanza, gris si no).
- [ ] Lista ordenada por distancia con permiso de ubicación, o de la A a la Z sin permiso, y filtro "Me alcanza".
- [ ] Estados de Explorar: con ubicación (13), sin ubicación (14), offline con hora de actualización (15) y error con *Reintentar* (16). Si no cargan los tiles del mapa, queda solo la lista.
- [ ] Detalle del premio (17) y variante con puntos insuficientes (18) mostrando cuánto falta en puntos y en horas; botón "Fijar como meta".
- [ ] Confirmar canje (19) con un botón de 64 dp que se mantiene presionado, con feedback háptico y sin diálogo extra (canjear no se puede deshacer).
- [ ] Código de canje (20) con cuenta regresiva de 10 minutos, pendiente sin red con los puntos reservados (21) y fallido con puntos devueltos (22).

## Criterios de aceptación

- [ ] Con permiso de ubicación, la lista se ordena por distancia y el mapa se centra en el usuario.
- [ ] Sin permiso, la lista aparece de la A a la Z y la pantalla no se bloquea ni insiste con el pedido.
- [ ] Desde Inicio se llega al código de canje en 2 toques y 1 gesto de mantener (fila del premio, *Canjear*, mantener).
- [ ] Fijar una meta lleva 2 toques (premio, *Fijar como meta*).
- [ ] El manifest no declara `ACCESS_BACKGROUND_LOCATION` y la ubicación no se envía al backend (RNF03).
- [ ] Cada estado de Figma 13–22 tiene su preview de Compose.

## Depende de

US-00. Usa `GetRewards` y `RedeemReward` (US-04) a través de sus interfaces, con repositorios *fake* hasta que estén listos.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

---

# ÉPICA 4 · Cuenta y perfil

### US-07 · Acceso con Google o email y sesión segura

```markdown
**Dev:** Joa · **Sprint:** 1 · **Puntos:** 8 · **Labels:** `tipo:feature` `area:app` `area:backend`

## Historia

**Como** usuario,
**quiero** entrar con mi cuenta de Google en un toque, o con mi email si no uso Google,
**para** empezar rápido y que mis canjes queden asociados a mí de forma segura.

## Contexto

Pantalla 05 de Figma ("Continuar con Google" y "Continuar con email") y el alcance del documento
("Acceso con Google o email"). Cruza app y backend, por eso lo toma el rol de arquitectura e
integración. Cubre RNF10 (HTTPS y token cifrado con Android Keystore).

## Alcance

### App
- [ ] Credential Manager con *Sign in with Google*; el client ID va en `local.properties`, no en el repo.
- [ ] Acceso con email y contraseña (registro e ingreso en la misma pantalla), con validación de formato y mensajes de error claros.
- [ ] Pantalla de acceso (05) después del onboarding y antes de los permisos, con estado de carga y error.
- [ ] Guardar el token de sesión cifrado con Android Keystore.
- [ ] Interceptor de OkHttp que agrega `Authorization: Bearer` y, ante un 401, limpia la sesión y vuelve a la pantalla de acceso.
- [ ] Network security config: sin *cleartext* en release; en debug solo se permite `10.0.2.2`.

### Backend
- [ ] `POST /auth/google`: verificar el ID token de Google (firma, `aud`, `exp`), crear o recuperar el usuario y devolver un JWT de sesión.
- [ ] `POST /auth/email`: registro e ingreso con email y contraseña guardada con hash (bcrypt), devuelve el mismo JWT.
- [ ] Tabla `users` y canjes asociados al usuario; `POST /redemptions` y `GET /redemptions/{id}` exigen JWT.

### Documento
- [ ] Agregar `POST /auth/email` a la tabla de endpoints de la sección 7 (hoy solo figura el de Google).

## Criterios de aceptación

- [ ] Un usuario nuevo entra con Google en menos de 3 toques y queda logueado al reabrir la app.
- [ ] Un usuario sin Google puede registrarse e ingresar con email; un email repetido o una contraseña incorrecta muestran un error claro.
- [ ] El token de sesión no aparece en texto plano en DataStore ni en los logs.
- [ ] Un request sin token o con token vencido a `/redemptions` recibe 401 y la app vuelve al acceso sin crashear.
- [ ] La detección de pausas y la consulta del historial siguen funcionando sin sesión y sin conexión.

## Depende de

US-00.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

### US-08 · Perfil, ajustes e integración de la navegación completa

```markdown
**Dev:** Joa · **Sprint:** 2 · **Puntos:** 8 · **Labels:** `tipo:feature` `area:app`

## Historia

**Como** usuario,
**quiero** gestionar mi perfil y mis preferencias, y moverme por toda la app sin cortes,
**para** sentir la app como una sola experiencia y no como pantallas sueltas.

## Contexto

Pantalla 25 de Figma y el rol de integración: une las funcionalidades de US-01 a US-07 en un flujo
completo, resuelve el *back stack* y los deep links.

## Alcance

- [ ] Perfil (25), al que se entra desde el avatar arriba en Inicio (lo que se usa poco va arriba): nombre y foto, saldo total histórico, activar o desactivar notificaciones, cambiar meta y meta diaria, acceso a Mis canjes, estado de los permisos y cerrar sesión.
- [ ] Recuperar un código ya generado lleva 3 toques: avatar, Mis canjes, Mostrar.
- [ ] Preferencias en DataStore a través de `SettingsRepository`.
- [ ] Deep link `takeabreak://reward/{id}`: la notificación de pausa validada abre Inicio y, si ya alcanza para la meta, el premio meta; la de canje confirmado abre el código.
- [ ] Grafo de navegación final según el flujo de Figma: splash → onboarding → acceso → permisos → pestañas (Inicio, Explorar, Actividad) + Perfil; *back stack* correcto en todos los flujos (canje, detalle, perfil) y estado de pestaña preservado.
- [ ] Banner global de offline con `NetworkMonitor` y manejo de *process death* (los ViewModels se recuperan sin perder la pantalla).
- [ ] Criterio único de errores para toda la app: cada error se muestra con un mensaje que dice qué pasó y qué puede hacer el usuario (*Reintentar*, ir a Ajustes, seguir sin conexión), como pide la consigna en 7.3.
- [ ] Revisión de los PR de los demás para que respeten la arquitectura (sin Room ni Retrofit en ViewModels, dominio sin Android).

## Criterios de aceptación

- [ ] Tocar la notificación abre la app en la pantalla correcta, esté la app cerrada o en segundo plano.
- [ ] El botón atrás nunca vuelve al onboarding ni a la pantalla de acceso una vez logueado.
- [ ] Desactivar las notificaciones en Perfil hace que el worker deje de notificar, pero siga sumando puntos.
- [ ] Cerrar sesión borra el token y vuelve a la pantalla de acceso, sin borrar las pausas guardadas.
- [ ] Rotar la pantalla o forzar *process death* en cualquier pantalla no pierde el estado.

## Depende de

US-00 y US-07. Se integra con las pantallas de los demás a medida que se mergean a `dev`.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

---

# ÉPICA 5 · Testing y cierre

### US-09 · Tests unitarios del dominio y de los ViewModels

```markdown
**Dev:** Valentin · **Sprint:** 3 · **Puntos:** 8 · **Labels:** `tipo:test` `area:app`

## Historia

**Como** equipo,
**queremos** que las reglas de puntos, los casos de uso y los ViewModels estén cubiertos por tests automáticos,
**para** poder cambiar cualquier regla con la seguridad de no romper el cálculo de puntos.

## Alcance

- [ ] JUnit + `kotlinx-coroutines-test` + Turbine en el source set `test` (JVM, sin emulador).
- [ ] `BreakRules` y `Pause.minutesOutside`: tabla de casos con día hábil y fin de semana, bordes de 29/30 y 44/45 min, pausas que cruzan las 23 h, la medianoche y las 9 h, pausas de varios días y tope de 240.
- [ ] `SyncBreaks`: acumulación del tope a lo largo del día, motivo de cada estado y guardar dos veces la misma pausa no la duplica (RNF04).
- [ ] Armado de pausas desde una secuencia *fake* de eventos (pantalla encendida por notificación sin desbloquear, eventos desordenados, checkpoint).
- [ ] `GetHomeSummary` (saldo con canjes reembolsados, racha), `RedeemReward`, `SetGoal` con repositorios *fake*.
- [ ] Cada ViewModel: emisión de Loading → Content / Empty / Error y marca offline con Turbine.
- [ ] Kover configurado para fallar el build si `domain` baja del 80 %.

## Criterios de aceptación

- [ ] `./gradlew testDebugUnitTest` corre verde desde Android Studio y en el CI.
- [ ] El reporte de Kover muestra 80 % o más de cobertura en `domain` (RNF09).
- [ ] Todos los ejemplos de la tabla de reglas del documento tienen su test.
- [ ] Ningún test depende de la hora real del sistema (se inyecta un `Clock`).

## Depende de

US-01 y US-02.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

### US-10 · Tests de datos, sincronización y backend

```markdown
**Dev:** Juan · **Sprint:** 3 · **Puntos:** 8 · **Labels:** `tipo:test` `area:app` `area:backend`

## Historia

**Como** equipo,
**queremos** probar automáticamente la persistencia, la sincronización offline y la API,
**para** garantizar que ningún canje se pierda ni se duplique, haya o no conexión.

## Alcance

### App
- [ ] Tests instrumentados de Room (`androidTest`): DAOs, índice único de pausas, cascada comercio → premio → canje.
- [ ] Repositorios con MockWebServer: catálogo con `since`, canje 201 / 200 / 409, errores de red mapeados a dominio.
- [ ] Workers con `work-testing` (`TestListenableWorkerBuilder`): reintento de pendientes, reembolso ante 409, actualización de la última sincronización.
- [ ] Test instrumentado de RNF04: matar el proceso entre guardar la pausa y actualizar el checkpoint.

### Backend
- [ ] `testApplication` de Ktor con Postgres en Testcontainers (o H2 en modo PostgreSQL).
- [ ] Idempotencia de `POST /redemptions`, concurrencia sobre el último stock, reposición del stock diario, vencimiento a 10 min, filtro `since`, 401 sin JWT.
- [ ] `POST /auth/email`: registro, email repetido, contraseña incorrecta y que la contraseña nunca se guarde en texto plano.

## Criterios de aceptación

- [ ] `./gradlew connectedDebugAndroidTest` corre verde en un emulador API 28 y uno API 35.
- [ ] `./gradlew test` del backend corre verde en el CI.
- [ ] Hay un test que demuestra que reintentar un canje no lo duplica, tanto en la app como en el backend.

## Depende de

US-03 y US-04.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

### US-11 · Tests de UI, accesibilidad y prueba con usuarios

```markdown
**Dev:** Abril · **Sprint:** 3 · **Puntos:** 8 · **Labels:** `tipo:test` `area:app` `ui`

## Historia

**Como** equipo,
**queremos** verificar que las pantallas se ven y se usan bien para cualquier persona,
**para** cumplir los requisitos de usabilidad y accesibilidad y validar el diseño con usuarios reales.

## Alcance

- [ ] Tests de Compose (`createComposeRule`) para Inicio, Explorar, Detalle, Canje y Actividad en cada estado de `UiState`, con ViewModels alimentados por *fakes*.
- [ ] Test del gesto de mantener presionado para confirmar el canje y del flujo Inicio → Código en 2 toques + 1 gesto.
- [ ] Revisión con Accessibility Scanner y TalkBack en todas las pantallas; fuente al 200 %; corrección de lo que aparezca.
- [ ] Prueba con usuarios según el plan de validación del documento (sección "Testear"), ahora sobre la app real: 5 personas del perfil de usuario, entrevista corta y las 4 tareas (T1 entender cómo se ganan puntos, T2 encontrar un premio que alcance y canjearlo, T3 decir por qué una pausa de anoche no sumó, T4 canjear sin conexión y explicar qué pasó).
- [ ] Medir si completan cada tarea, el tiempo, la cantidad de toques y los errores, y aplicar el cuestionario SUS al final.
- [ ] Si 2 de 5 personas no completan una tarea, rediseñar esa parte y volver a probarla.

## Criterios de aceptación

- [ ] Los tests de UI corren verdes en el emulador desde Android Studio.
- [ ] Accessibility Scanner no reporta problemas de contraste, tamaño táctil ni etiquetas (RNF05, RNF06).
- [ ] La app se puede usar de punta a punta solo con TalkBack.
- [ ] El informe de la prueba con usuarios (resultados por tarea, puntaje SUS y cambios hechos) está en el repo `docs`.

## Depende de

US-05 y US-06.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```

### US-12 · Pruebas de punta a punta, entrega técnica y defensa

```markdown
**Dev:** Joa · **Sprint:** 3 · **Puntos:** 8 · **Labels:** `tipo:test` `tipo:docs` `area:app` `area:backend`

## Historia

**Como** equipo,
**queremos** probar la app completa en condiciones reales, dejar una versión estable en `main` y preparar la demo,
**para** llegar a la defensa con algo que funciona y que todos podemos explicar.

## Contexto

Cubre las secciones 7.2, 7.4 y 7.5 de la consigna. La versión final no se evalúa por recorrer
pantallas: las operaciones tienen que producir efectos reales y consistentes.

## Alcance

### Pruebas
- [ ] Plan de pruebas manuales de punta a punta en el repo `docs`: instalar → onboarding → acceso → permisos → pausa real → notificación → canje online → canje en modo avión → reconexión → permisos rechazados.
- [ ] Ejecutarlo en emulador API 28, API 35 y en al menos un teléfono físico, registrando resultados.
- [ ] Batería: medición de 24 h con Battery Historian, consumo atribuido menor al 1 % (RNF01).
- [ ] Arranque en frío menor a 2 s con Macrobenchmark en un módulo `:benchmark` (RNF07).
- [ ] Revisión final de privacidad y seguridad: manifest, *cleartext*, tokens, logs sin datos sensibles.

### Entrega técnica (7.4)
- [ ] README de `tpo-da1` que una persona externa al equipo entienda solo: qué hace la app, instrucciones de ejecución en Android Studio (incluidas las claves de Maps y Google en `local.properties`), arquitectura final con su diagrama, tecnologías utilizadas, funcionalidades implementadas, requisitos funcionales alcanzados (RF01–RF04, uno por uno), decisiones relevantes y limitaciones conocidas.
- [ ] Limitaciones conocidas, como mínimo: el servidor confía en los puntos calculados en el teléfono, no hay pagos reales y los comercios son datos semilla.
- [ ] README del backend con endpoints, ejecución local y URL de Render.
- [ ] Documento final en `docs` con la arquitectura real y los cambios respecto de la preentrega justificados (consigna, sección 2).
- [ ] APK de release firmado, PR de `dev` a `main` en los tres repos y tag `v1.0`.

### Demo y defensa (7.5)
- [ ] Guion de demo con la estructura Problema → Escenario → Acción del usuario → Respuesta de la app → Valor, sobre el escenario de Martina en la cena: pausa (simulada con el modo de US-01), notificación, Inicio, Explorar, canje con código y canje sin conexión.
- [ ] Datos de demo preparados: backend en Render con el catálogo semilla y una cuenta con saldo.
- [ ] Ensayo con los 4 integrantes; cada uno explica la app completa y su parte (código, arquitectura, estado, navegación, persistencia, networking, sincronización, sensores, decisiones de UX y organización del trabajo).

## Criterios de aceptación

- [ ] El plan de pruebas se ejecuta completo sin bloqueantes abiertos.
- [ ] Battery Historian y Macrobenchmark cumplen RNF01 y RNF07, con capturas en `docs`.
- [ ] `main` de los tres repos compila desde cero en Android Studio siguiendo solo el README.
- [ ] El README cubre los 9 puntos de la sección 7.4 de la consigna.
- [ ] La demo se puede hacer completa sin esperar una pausa real.
- [ ] Todos los issues del backlog están cerrados o movidos explícitamente a trabajo futuro.

## Depende de

US-09, US-10 y US-11.

## Definición de terminado

- [ ] Entregada en PR parciales a `dev`, con commits chicos y frecuentes, no en un único PR al final.
- [ ] Cada PR tiene la plantilla completa, incluidas las preguntas de uso de IA de la consigna, y 1 revisión aprobada.
- [ ] CI en verde.
- [ ] El autor puede explicar el código que integró sin leerlo, como se pide en la defensa.
```
