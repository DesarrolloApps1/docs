# Take a Break · Diseño (Figma)

Frames de la preentrega. Todo sale de `build.py`, así que **no se editan los SVG a mano**: se cambia el script y se regenera.

```
figma/
├── build.py        # genera todo (tokens, componentes, pantallas, tableros)
├── screens/        # 27 frames Android 360×800 dp  → importar en Figma
├── boards/         # flujo principal, sistema de diseño, ley de Fitts
├── png/            # exportes @2x para el documento LaTeX
└── index.html      # galería con el estado y la decisión de diseño de cada frame
```

## Regenerar

```bash
python build.py          # SVG + index.html
python build.py --png    # además exporta png/ (usa Edge headless)
```

## Importar en Figma

1. Crear un archivo nuevo en Figma con las páginas `Pantallas`, `Flujo` y `Sistema`.
2. Arrastrar todos los `.svg` de `screens/` al lienzo: cada archivo queda como un frame de 360×800 con su nombre (`08-inicio`, …).
   Los textos quedan editables; Figma ya incluye **Bricolage Grotesque**, **DM Sans** y **JetBrains Mono**.
3. Arrastrar los tres `.svg` de `boards/` a sus páginas.
4. (Opcional) Con los frames seleccionados: *Tidy up* → *Create prototype connections* siguiendo `boards/00-flujo-principal.svg`.

## Pantallas

| Sección | Frames |
|---|---|
| A · Primer uso | 01 Splash · 02–04 Onboarding · 05 Acceso · 06 Permisos · 07 Permiso rechazado |
| B · Inicio | 08 Contenido · 09 Break validado · 10 Vacío · 11 Cargando · 12 Offline |
| C · Explorar | 13 Mapa + lista · 14 Sin ubicación · 15 Offline · 16 Error sin caché |
| D · Canje | 17 Detalle · 18 Puntos insuficientes · 19 Mantener para canjear · 20 Código · 21 Pendiente · 22 Fallido |
| E · Actividad | 23 Semana e historial · 24 Vacío + reglas |
| F · Perfil | 25 Perfil y ajustes · 26 Mis canjes |
| G · Sistema | 27 Notificación |

Todas las pantallas principales cubren la secuencia **carga → contenido → vacío → error → offline** que pide la consigna (§4.8).

## Principios aplicados

- **Cero fricción en el caso central:** la pausa se detecta sola (0 toques); de la notificación al premio hay 1 toque.
- **Ley de Fitts:** los objetivos táctiles miden ≥ 48 dp y el CTA primario 56 dp × 320 dp, siempre abajo, en la zona natural del pulgar. La navegación tiene 3 destinos de 120 dp.
- **Ley de Hick:** una sola acción primaria por pantalla; login y registro unificados en «Continuar con…».
- **Prevención de errores:** canjear (irreversible) se confirma manteniendo presionado, no con un diálogo extra.
- **Sin callejones sin salida:** si no alcanzan los puntos, se ofrece «Fijar como meta»; sin permisos o sin red, la app se degrada pero sigue funcionando.
- **Look & feel:** minimalista, inspirado en Pasito: verde bosque + lima sobre crema, formas de píldora y sin sombras.
