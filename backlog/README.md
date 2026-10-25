# backlog/

Backlog de Take a Break y la automatización para cargarlo a GitHub.

- [`user-stories.md`](user-stories.md): fuente de verdad de las historias `US-NN`.
- `Crear-Issues.ps1`: crea las labels en `DesarrolloApps1/tpo-da1`, un issue por historia (con
  assignee y labels) y los agrega al Project **DA1 | Board** con `Status = Backlog` y `Size` según
  los puntos (3 → S, 5 → M, 8 → L, 13 → XL).
- `issues-creados.csv`: registro `us_id,numero,url,estado` que deja el script.

**Esto lo corre una sola persona.** Es idempotente: identifica los issues por el prefijo `US-NN` del
título, así que correrlo de nuevo solo crea lo que falta. Si corregís una historia en el markdown,
corré el script con `-Actualizar`: reescribe título y body de los issues existentes y les agrega
las labels nuevas, sin tocar el Status del board.

## Uso

Requiere `gh` autenticado con el scope `project` (`gh auth refresh -s project`).

```bash
pwsh backlog/Crear-Issues.ps1 -DryRun              # ver qué haría, sin tocar GitHub
pwsh backlog/Crear-Issues.ps1 -DryRun -Solo US-05  # ver título y body exactos de una historia
pwsh backlog/Crear-Issues.ps1 -Solo US-00          # crear una sola de prueba
pwsh backlog/Crear-Issues.ps1                      # crear todo y cargarlo al board
```

| Parámetro | Default | Para qué |
|---|---|---|
| `-Repo` | `DesarrolloApps1/tpo-da1` | Repo donde se crean los issues |
| `-ArchivoHistorias` | `backlog/user-stories.md` | Fuente de verdad |
| `-ProjectOwner` | `DesarrolloApps1` | Dueño del Project |
| `-ProjectNumber` | `1` | `''` para no tocar ningún Project |
| `-DryRun` | apagado | Imprime todo sin tocar GitHub |
| `-Solo US-NN` | *(vacío)* | Procesa una sola historia |
| `-SinLabels` | apagado | Saltea la creación de labels |
| `-Actualizar` | apagado | Reescribe los issues que ya existen con lo que dice el markdown |

## Mapa de devs

| Dev | Usuario de GitHub | Área |
|---|---|---|
| Joa | `JoaVelazquez` | Arquitectura, integración, acceso y perfil |
| Valentin | `valentinpapa12` | Detección de pausas, reglas y actividad |
| Juan | `Juanjerezz` | Backend, sincronización y canjes |
| Abril | `amaci003` | UI/UX: onboarding, inicio, explorar y canje |

Si cambia alguno, se edita `$MapaDevs` arriba de todo en `Crear-Issues.ps1`.
