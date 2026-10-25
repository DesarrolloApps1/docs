<#
.SYNOPSIS
    Crea en GitHub los issues del backlog de Take a Break a partir de backlog/user-stories.md.

.DESCRIPTION
    Lee backlog/user-stories.md como unica fuente de verdad, crea las labels necesarias,
    crea un issue por cada historia US-NN y los agrega al Project "DA1 | Board" con
    Status = Backlog y Size segun los puntos.

    Es idempotente: identifica los issues por el prefijo "US-NN" del titulo, asi que
    correrlo varias veces no duplica nada, solo crea lo que falta.

.EXAMPLE
    pwsh ./Crear-Issues.ps1 -DryRun
    Muestra todo lo que haria sin tocar GitHub.

.EXAMPLE
    pwsh ./Crear-Issues.ps1 -Solo US-00
    Crea una sola historia, para revisar el formato antes de la corrida completa.

.EXAMPLE
    pwsh ./Crear-Issues.ps1 -Actualizar
    Ademas de crear lo que falta, reescribe titulo y body de los issues que ya existen
    con lo que dice el documento y les agrega las labels nuevas.

.EXAMPLE
    pwsh ./Crear-Issues.ps1 -ProjectNumber ''
    Crea las historias sin agregarlas a ningun Project.
#>
[CmdletBinding()]
param(
    [string] $Repo             = 'DesarrolloApps1/tpo-da1',
    [string] $ArchivoHistorias = (Join-Path $PSScriptRoot 'user-stories.md'),
    [string] $ProjectOwner     = 'DesarrolloApps1',
    [string] $ProjectNumber    = '1',
    [string] $Solo             = '',
    [switch] $DryRun,
    [switch] $SinLabels,
    [switch] $Actualizar
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Caracteres no ASCII usados en el documento, definidos por codepoint para que este
# script funcione sin importar como lo lea el interprete.
$PUNTO_MEDIO = [char]0x00B7   # el separador  ·  de los titulos y la metadata
$E_ACENTUADA = [char]0x00C9   # la  É  de "ÉPICA"

# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

# Nombre en el documento -> usuario de GitHub. "Todos" no se asigna a nadie.
$MapaDevs = @{
    'Joa'      = 'JoaVelazquez'
    'Valentin' = 'valentinpapa12'
    'Juan'     = 'Juanjerezz'
    'Abril'    = 'amaci003'
    'Todos'    = ''
}

# Numero de epica -> label. Sale del heading "# EPICA N ..." del documento.
$MapaEpicas = @{
    '0' = 'epic:arquitectura'
    '1' = 'epic:pausas'
    '2' = 'epic:catalogo-canjes'
    '3' = 'epic:experiencia'
    '4' = 'epic:cuenta'
    '5' = 'epic:testing'
}

$Labels = @(
    @{ n = 'epic:arquitectura';    c = '6E7781'; d = 'Arquitectura base de la app y del backend' }
    @{ n = 'epic:pausas';          c = '0E8A16'; d = 'Deteccion de pausas, reglas de puntos y actividad' }
    @{ n = 'epic:catalogo-canjes'; c = '1D76DB'; d = 'Backend, catalogo, canjes y sincronizacion offline' }
    @{ n = 'epic:experiencia';     c = 'D93F0B'; d = 'Onboarding, inicio, explorar y canje' }
    @{ n = 'epic:cuenta';          c = '5319E7'; d = 'Acceso con Google, perfil e integracion' }
    @{ n = 'epic:testing';         c = '008672'; d = 'Tests, pruebas de punta a punta y entrega' }
    @{ n = 'tipo:feature';         c = 'C5DEF5'; d = 'Funcionalidad de la app' }
    @{ n = 'tipo:infra';           c = 'C5DEF5'; d = 'Build, configuracion y tooling' }
    @{ n = 'tipo:test';            c = 'C5DEF5'; d = 'Tests automaticos y pruebas' }
    @{ n = 'tipo:docs';            c = 'C5DEF5'; d = 'Documentacion' }
    @{ n = 'area:app';             c = 'BFD4F2'; d = 'Repo tpo-da1 (Kotlin + Compose)' }
    @{ n = 'area:backend';         c = 'BFD4F2'; d = 'Repo tpo-da1-backend (Ktor)' }
    @{ n = 'ui';                   c = 'F9D0C4'; d = 'Pantallas y componentes de Compose' }
    @{ n = 'sprint:0';             c = 'EDEDED'; d = 'Arquitectura base' }
    @{ n = 'sprint:1';             c = 'EDEDED'; d = 'Funcionalidades, primera tanda' }
    @{ n = 'sprint:2';             c = 'EDEDED'; d = 'Funcionalidades, segunda tanda' }
    @{ n = 'sprint:3';             c = 'EDEDED'; d = 'Testing y entrega' }
    @{ n = 'dev:joa';              c = 'D4C5F9'; d = 'Joa - arquitectura, integracion y acceso' }
    @{ n = 'dev:valentin';         c = 'D4C5F9'; d = 'Valentin - deteccion, reglas y actividad' }
    @{ n = 'dev:juan';             c = 'D4C5F9'; d = 'Juan - backend, sincronizacion y canjes' }
    @{ n = 'dev:abril';            c = 'D4C5F9'; d = 'Abril - UI y UX' }
    @{ n = 'dev:todos';            c = 'D4C5F9'; d = 'Tarea conjunta del equipo' }
    @{ n = 'bloqueante';           c = 'E99695'; d = 'Si se demora, frena el trabajo de otros' }
)

# Puntos de la historia -> opcion del campo Size del Project.
$MapaSize = @{ '1' = 'XS'; '2' = 'S'; '3' = 'S'; '5' = 'M'; '8' = 'L'; '13' = 'XL' }
$StatusInicial = 'Backlog'

$MillisEntreCreaciones = 300   # limite secundario de GitHub: ~80 creaciones/minuto
$ArchivoSalida = Join-Path $PSScriptRoot 'issues-creados.csv'

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

function Write-Paso  { param([string]$m) Write-Host "`n== $m" -ForegroundColor Cyan }
function Write-Ok    { param([string]$m) Write-Host "   ok   $m" -ForegroundColor Green }
function Write-Skip  { param([string]$m) Write-Host "   --   $m" -ForegroundColor DarkGray }
function Write-Aviso { param([string]$m) Write-Host "   !    $m" -ForegroundColor Yellow }
function Write-Falla { param([string]$m) Write-Host "   XX   $m" -ForegroundColor Red }

# Ejecuta gh y devuelve @{ Ok = bool; Salida = string }. Nunca tira excepcion.
function Invoke-Gh {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]] $Argumentos)
    $salida = & gh @Argumentos 2>&1 | Out-String
    return @{ Ok = ($LASTEXITCODE -eq 0); Salida = $salida.Trim() }
}

function Write-Utf8SinBom {
    param([string] $Ruta, [string] $Contenido)
    [System.IO.File]::WriteAllText($Ruta, $Contenido, (New-Object System.Text.UTF8Encoding $false))
}

# ---------------------------------------------------------------------------
# Etapa 1: preflight
# ---------------------------------------------------------------------------

function Test-Preflight {
    Write-Paso 'Preflight'

    if (-not (Test-Path $ArchivoHistorias)) {
        throw "No encuentro el archivo de historias: $ArchivoHistorias"
    }
    Write-Ok "Historias: $((Resolve-Path $ArchivoHistorias).Path)"

    $colaboradores = @{}

    # En -DryRun no se llama a gh en ningun momento, asi que tampoco hace falta
    # tenerlo instalado: se puede validar el parseo del documento sin nada mas.
    if ($DryRun) {
        Write-Aviso 'Modo -DryRun: no se va a tocar nada en GitHub'
        return $colaboradores
    }

    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "gh CLI no esta instalado. Instalalo con:  winget install --id GitHub.cli -e   (y despues reabri la terminal)"
    }
    Write-Ok "gh encontrado: $((Get-Command gh).Source)"

    $auth = Invoke-Gh auth status
    if (-not $auth.Ok) {
        throw "No estas autenticado en GitHub. Corre:  gh auth login --hostname github.com --git-protocol https --web"
    }
    Write-Ok 'Autenticado en GitHub'

    if ($ProjectNumber -and $auth.Salida -notmatch 'project') {
        throw "Falta el scope 'project' para poder agregar items al Project. Corre:  gh auth refresh --hostname github.com -s project"
    }
    if ($ProjectNumber) { Write-Ok "Scope 'project' presente" }

    $repoOk = Invoke-Gh repo view $Repo --json name
    if (-not $repoOk.Ok) { throw "No puedo acceder al repo '$Repo'. Detalle: $($repoOk.Salida)" }
    Write-Ok "Repo accesible: $Repo"

    # GitHub ignora en silencio un assignee que no es colaborador del repo,
    # asi que hay que chequearlo nosotros o el dato se pierde sin aviso.
    foreach ($dev in $MapaDevs.Keys) {
        $usuario = $MapaDevs[$dev]
        if (-not $usuario) { continue }
        $r = Invoke-Gh api --silent "repos/$Repo/collaborators/$usuario"
        if ($r.Ok) {
            $colaboradores[$dev] = $usuario
            Write-Ok "$dev -> @$usuario (colaborador)"
        } else {
            $colaboradores[$dev] = ''
            Write-Aviso "$dev -> @$usuario NO es colaborador de $Repo. Sus issues van sin assignee, solo con la label dev:$($dev.ToLower()). Invitalo al repo y volve a correr el script."
        }
    }

    if ($ProjectNumber) {
        $p = Invoke-Gh project view $ProjectNumber --owner $ProjectOwner --format json
        if (-not $p.Ok) {
            throw "No encuentro el Project #$ProjectNumber de '$ProjectOwner'. Lista los disponibles con:  gh project list --owner $ProjectOwner"
        }
        Write-Ok "Project #$ProjectNumber de $ProjectOwner accesible"
    }

    return $colaboradores
}

# ---------------------------------------------------------------------------
# Etapa 2: parseo del markdown
# ---------------------------------------------------------------------------

function Get-Historias {
    Write-Paso 'Parseando historias'

    $lineas     = @(Get-Content -LiteralPath $ArchivoHistorias -Encoding utf8)
    $historias  = [System.Collections.Generic.List[object]]::new()
    $labelEpica = ''
    $reEpica    = '^#\s+' + $E_ACENTUADA + 'PICA\s+(\d+)'
    # El sufijo opcional es la marca de estado del backlog (`OK`, `PARCIAL`, `PENDIENTE`,
    # `NUEVA`). Sirve para leer el markdown de un vistazo y no tiene que entrar al titulo del
    # issue: el estado real de un issue en GitHub es si esta abierto o cerrado.
    $reTitulo   = '^###\s+(US-\d+)\s*' + $PUNTO_MEDIO + '\s*(.+?)(?:\s+`[A-Z]+`)?\s*$'
    $reDev      = '\*\*Dev:\*\*\s*([^' + $PUNTO_MEDIO + ']+)'
    $i = 0

    while ($i -lt $lineas.Count) {
        $linea = $lineas[$i]

        # "# EPICA 3 - Motor de juego y estrategias (Joa)"
        if ($linea -match $reEpica) {
            $labelEpica = $MapaEpicas[$Matches[1]]
            if (-not $labelEpica) { Write-Aviso "Epica $($Matches[1]) sin label mapeada" }
            $i++
            continue
        }

        # "### US-04 - Modelar el personaje con los atributos del juego"
        if ($linea -match $reTitulo) {
            $id     = $Matches[1]
            $titulo = $Matches[2]

            $j = $i + 1
            while ($j -lt $lineas.Count -and $lineas[$j].Trim() -eq '') { $j++ }

            $apertura = '``' + '`markdown'
            $cierre   = '``' + '`'

            if ($j -ge $lineas.Count -or $lineas[$j].Trim() -ne $apertura) {
                Write-Aviso "$id no tiene un bloque de codigo markdown despues del titulo. Se saltea."
                $i++
                continue
            }

            $j++
            $cuerpo = [System.Collections.Generic.List[string]]::new()
            while ($j -lt $lineas.Count -and $lineas[$j].Trim() -ne $cierre) {
                $cuerpo.Add($lineas[$j])
                $j++
            }

            $meta = $cuerpo | Where-Object { $_ -match '^\*\*Dev:\*\*' } | Select-Object -First 1
            if (-not $meta) {
                Write-Aviso "$id no tiene linea de metadata (**Dev:** ...). Se saltea."
                $i = $j
                continue
            }

            $dev = if ($meta -match $reDev)                     { $Matches[1].Trim() } else { '' }
            $spr = if ($meta -match '\*\*Sprint:\*\*\s*(\d+)')  { $Matches[1] }       else { '' }
            $pts = if ($meta -match '\*\*Puntos:\*\*\s*(\d+)')  { $Matches[1] }       else { '' }

            $labels = [System.Collections.Generic.List[string]]::new()
            if ($meta -match '\*\*Labels:\*\*\s*(.+)$') {
                foreach ($m in [regex]::Matches($Matches[1], '`([^`]+)`')) {
                    $labels.Add($m.Groups[1].Value.Trim())
                }
            }
            if ($labelEpica) { $labels.Add($labelEpica) }
            if ($spr)        { $labels.Add("sprint:$spr") }
            if ($dev)        { $labels.Add("dev:$($dev.ToLower())") }

            $faltantes = @()
            if (-not $dev) { $faltantes += 'Dev' }
            if (-not $spr) { $faltantes += 'Sprint' }
            if (-not $pts) { $faltantes += 'Puntos' }
            if ($faltantes.Count -gt 0) {
                Write-Aviso "$id : metadata incompleta (falta $($faltantes -join ', ')). Se saltea."
                $i = $j
                continue
            }

            $historias.Add([pscustomobject]@{
                Id     = $id
                Titulo = "$id $PUNTO_MEDIO $titulo"
                Body   = ($cuerpo -join "`n").Trim()
                Dev    = $dev
                Sprint = $spr
                Puntos = $pts
                Labels = @($labels | Select-Object -Unique)
            })

            $i = $j + 1
            continue
        }

        $i++
    }

    if ($historias.Count -eq 0) {
        throw "No se parseo ninguna historia de $ArchivoHistorias. Revisa que el formato del documento no haya cambiado."
    }
    Write-Ok "$($historias.Count) historias parseadas"
    if ($historias.Count -ne 13) {
        Write-Aviso "Se esperaban 13 historias (US-00 a US-12). Si agregaste o quitaste alguna esta bien; si no, revisa el formato del documento."
    }

    if ($Solo) {
        $filtradas = @($historias | Where-Object { $_.Id -eq $Solo })
        if ($filtradas.Count -eq 0) { throw "No existe la historia '$Solo' en el documento." }
        Write-Aviso "Filtrado por -Solo $Solo"
        return $filtradas
    }

    return $historias.ToArray()
}

# ---------------------------------------------------------------------------
# Etapa 3: labels
# ---------------------------------------------------------------------------

function Set-Labels {
    Write-Paso 'Labels'
    if ($SinLabels) { Write-Skip 'Salteado por -SinLabels'; return }

    foreach ($l in $Labels) {
        if ($DryRun) { Write-Skip "crearia label $($l.n) (#$($l.c))"; continue }
        # --force actualiza la label si ya existe, asi que esto es idempotente.
        $r = Invoke-Gh label create $l.n --repo $Repo --color $l.c --description $l.d --force
        if ($r.Ok) { Write-Ok "label $($l.n)" } else { Write-Falla "label $($l.n): $($r.Salida)" }
    }
}

# ---------------------------------------------------------------------------
# Etapa 4: issues
# ---------------------------------------------------------------------------

function Get-IssuesExistentes {
    if ($DryRun) { return @{} }

    # Las comillas en 'number,title,url' son necesarias: sin ellas PowerShell lo
    # interpreta como un array de tres strings y gh recibe "number title url".
    $r = Invoke-Gh issue list --repo $Repo --state all --limit 200 --json 'number,title,url'
    if (-not $r.Ok) { throw "No pude listar los issues de '$Repo'. Detalle: $($r.Salida)" }

    $indice = @{}
    foreach ($issue in ($r.Salida | ConvertFrom-Json)) {
        # Se indexa por el prefijo US-NN y no por el titulo completo, asi renombrar
        # una historia no genera un duplicado.
        if ($issue.title -match '^(US-\d+)') { $indice[$Matches[1]] = $issue }
    }
    return $indice
}

function New-Issues {
    param($Historias, $Colaboradores)

    Write-Paso 'Issues'
    $existentes = Get-IssuesExistentes
    if ($existentes.Count -gt 0) { Write-Skip "$($existentes.Count) issues US-* ya existen en el repo" }

    $resultados = [System.Collections.Generic.List[object]]::new()

    foreach ($h in $Historias) {
        if ($existentes.ContainsKey($h.Id)) {
            $e = $existentes[$h.Id]
            if (-not $Actualizar) {
                Write-Skip "$($h.Id) ya existe como #$($e.number)"
                $resultados.Add([pscustomobject]@{ us_id = $h.Id; numero = $e.number; url = $e.url; estado = 'ya-existia' })
                continue
            }

            # Solo agrega labels: las que alguien puso a mano en GitHub se respetan.
            $tmp = Join-Path $PSScriptRoot "$($h.Id).tmp.md"
            Write-Utf8SinBom -Ruta $tmp -Contenido $h.Body
            try {
                $r = Invoke-Gh issue edit $e.number --repo $Repo --title $h.Titulo --body-file $tmp --add-label ($h.Labels -join ',')
            } finally {
                Remove-Item $tmp -ErrorAction SilentlyContinue
            }
            $estado = if ($r.Ok) { 'actualizado' } else { 'error' }
            if ($r.Ok) { Write-Ok "$($h.Id) actualizado (#$($e.number))" } else { Write-Falla "$($h.Id): $($r.Salida)" }
            $resultados.Add([pscustomobject]@{ us_id = $h.Id; numero = $e.number; url = $e.url; estado = $estado })
            Start-Sleep -Milliseconds $MillisEntreCreaciones
            continue
        }

        $assignee = ''
        if ($Colaboradores.ContainsKey($h.Dev)) { $assignee = $Colaboradores[$h.Dev] }
        elseif ($MapaDevs.ContainsKey($h.Dev))  { $assignee = $MapaDevs[$h.Dev] }

        if ($DryRun) {
            $quien = if ($assignee) { "@$assignee" } else { '(sin assignee)' }
            Write-Skip "crearia $($h.Id) | $quien | $($h.Labels -join ', ')"
            # Con -Solo se muestra ademas el contenido exacto, para poder revisar
            # el titulo y el body (acentos incluidos) antes de la corrida de verdad.
            if ($Solo) {
                Write-Host ''
                Write-Host "   titulo: $($h.Titulo)" -ForegroundColor White
                Write-Host '   body:' -ForegroundColor White
                foreach ($linea in ($h.Body -split "`n")) { Write-Host "     | $linea" -ForegroundColor DarkGray }
                Write-Host ''
            }
            $resultados.Add([pscustomobject]@{ us_id = $h.Id; numero = ''; url = ''; estado = 'dry-run' })
            continue
        }

        $tmp = Join-Path $PSScriptRoot "$($h.Id).tmp.md"
        Write-Utf8SinBom -Ruta $tmp -Contenido $h.Body
        try {
            $argumentos = @(
                'issue', 'create',
                '--repo', $Repo,
                '--title', $h.Titulo,
                '--body-file', $tmp,
                '--label', ($h.Labels -join ',')
            )
            if ($assignee) { $argumentos += @('--assignee', $assignee) }

            $r = Invoke-Gh @argumentos
            if ($r.Ok) {
                $url = ($r.Salida -split "`n" | Where-Object { $_ -match '^https?://' } | Select-Object -First 1)
                $num = if ($url -match '/(\d+)\s*$') { $Matches[1] } else { '' }
                Write-Ok "$($h.Id) -> #$num"
                $resultados.Add([pscustomobject]@{ us_id = $h.Id; numero = $num; url = $url; estado = 'creado' })
            } else {
                Write-Falla "$($h.Id): $($r.Salida)"
                $resultados.Add([pscustomobject]@{ us_id = $h.Id; numero = ''; url = ''; estado = 'error' })
            }
        } finally {
            Remove-Item $tmp -ErrorAction SilentlyContinue
        }

        Start-Sleep -Milliseconds $MillisEntreCreaciones
    }

    return $resultados
}

# ---------------------------------------------------------------------------
# Etapa 5: Project
# ---------------------------------------------------------------------------

function Add-AlProject {
    param($Resultados, $Historias)

    if (-not $ProjectNumber) {
        Write-Paso 'Project'
        Write-Skip 'No se paso -ProjectNumber, se saltea'
        return
    }

    Write-Paso "Project #$ProjectNumber"
    if ($DryRun) {
        foreach ($h in $Historias) {
            Write-Skip "agregaria $($h.Id) al project (Status $StatusInicial, Size $($MapaSize[$h.Puntos]))"
        }
        return
    }

    # IDs del Project y de las opciones de Status y Size, para completar los campos
    # del board y no tener que hacerlo a mano en la UI.
    $p = Invoke-Gh project view $ProjectNumber --owner $ProjectOwner --format json
    $projectId = ($p.Salida | ConvertFrom-Json).id
    $campos = (Invoke-Gh project field-list $ProjectNumber --owner $ProjectOwner --format json).Salida | ConvertFrom-Json
    $campoStatus = $campos.fields | Where-Object { $_.name -eq 'Status' } | Select-Object -First 1
    $campoSize   = $campos.fields | Where-Object { $_.name -eq 'Size' }   | Select-Object -First 1

    $puntosPorId = @{}
    foreach ($h in $Historias) { $puntosPorId[$h.Id] = $h.Puntos }

    foreach ($r in $Resultados) {
        if (-not $r.url) { continue }

        # Agregar dos veces el mismo item no lo duplica: devuelve el item que ya estaba.
        $a = Invoke-Gh project item-add $ProjectNumber --owner $ProjectOwner --url $r.url --format json
        if (-not $a.Ok) { Write-Falla "$($r.us_id): $($a.Salida)"; continue }
        $itemId = ($a.Salida | ConvertFrom-Json).id

        # Status solo se pone en los recien creados, para no pisar el avance del board.
        $valores = @()
        if ($campoStatus -and $r.estado -eq 'creado') {
            $valores += @{ Campo = $campoStatus; Opcion = $StatusInicial }
        }
        if ($campoSize) {
            $valores += @{ Campo = $campoSize; Opcion = $MapaSize[$puntosPorId[$r.us_id]] }
        }

        $extra = @()
        foreach ($v in $valores) {
            $opcion = $v.Campo.options | Where-Object { $_.name -eq $v.Opcion } | Select-Object -First 1
            if (-not $opcion) { Write-Aviso "$($r.us_id): el campo $($v.Campo.name) no tiene la opcion '$($v.Opcion)'"; continue }
            $e = Invoke-Gh project item-edit --id $itemId --project-id $projectId --field-id $v.Campo.id --single-select-option-id $opcion.id
            if ($e.Ok) { $extra += "$($v.Campo.name)=$($v.Opcion)" } else { Write-Falla "$($r.us_id) $($v.Campo.name): $($e.Salida)" }
        }
        Write-Ok "$($r.us_id) agregado $($extra -join ' ')"
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

try {
    $colaboradores = Test-Preflight
    $historias     = Get-Historias
    Set-Labels
    $resultados    = New-Issues -Historias $historias -Colaboradores $colaboradores
    Add-AlProject -Resultados $resultados -Historias $historias

    if (-not $DryRun) {
        $resultados | Export-Csv -LiteralPath $ArchivoSalida -NoTypeInformation -Encoding utf8
    }

    $creados = @($resultados | Where-Object { $_.estado -eq 'creado' }).Count
    $viejos  = @($resultados | Where-Object { $_.estado -eq 'ya-existia' }).Count
    $editados = @($resultados | Where-Object { $_.estado -eq 'actualizado' }).Count
    $errores = @($resultados | Where-Object { $_.estado -eq 'error' }).Count

    Write-Paso 'Resumen'
    Write-Host "   creados:     $creados"
    Write-Host "   ya existian: $viejos"
    Write-Host "   actualizados: $editados"
    Write-Host "   errores:     $errores"
    if (-not $DryRun) { Write-Host "   detalle en:  $ArchivoSalida" }

    if ($errores -gt 0) { exit 1 }
    exit 0
}
catch {
    Write-Host ''
    Write-Falla $_.Exception.Message
    exit 1
}
