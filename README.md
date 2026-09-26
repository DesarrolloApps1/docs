# Take a Break · Documentación

Documentación del TPO de Desarrollo de Aplicaciones I (UADE). El código de la app está en [tpo-da1](https://github.com/DesarrolloApps1/tpo-da1).

| Carpeta | Contenido |
|---|---|
| `preentrega/` | Documento de la preentrega en LaTeX (`main.tex` y una sección por archivo en `secciones/`) |
| `figma/` | Pantallas y tableros de diseño, importables en Figma, generados con `build.py` |

## Compilar el documento

```bash
cd preentrega
latexmk -pdf main.tex
```

Las imágenes se toman de `figma/png/`. Si se cambia algo en el diseño, primero se regenera con `python figma/build.py --png`.

Los datos que faltan completar aparecen en rojo entre corchetes en el PDF.
