# Desarrollo y actualizaciones

La raíz es el único repositorio Git de botesp. `xiaozhi-esp32/` es una copia
versionada del código base, no un repositorio anidado ni un submódulo. La revisión
de origen está en `upstream.json` y sus licencias permanecen intactas.

## Trabajar en una mejora

```powershell
git switch main
git pull --ff-only
git switch -c mejora/nombre-corto
. .\scripts\enter-idf.ps1
python scripts/prepare_troko_assets.py
python -m unittest discover -s services/tests -v
python -m unittest discover -s tests -v
python scripts/audit_public.py
.\scripts\build.ps1
```

Los cambios C++ deben respetar `xiaozhi-esp32/AGENTS.md` y su `.clang-format`.
No editar `build/`, `managed_components/`, `sdkconfig` ni cabeceras generadas.
Las modificaciones del hardware se concentran en la carpeta de la placa.

Las escenas propias se editan en `scripts/generate_idle_animations.py`.
`build.ps1` las regenera y empaqueta junto con los 21 GIF originales; esos
originales se verifican por hash y no deben sobrescribirse. Para ver las escenas
sin compilar, ejecuta `python scripts/prepare_troko_assets.py`: la vista previa
queda en `.local/idle-scenes-preview.png`.

## Publicar una actualización

```powershell
git add README.md docs scripts services tests .github xiaozhi-esp32
git diff --cached --stat
git diff --cached --check
python scripts/audit_public.py
git commit -m "Describe el cambio concreto"
git push -u origin mejora/nombre-corto
```

Abre una PR hacia `main`, indicando qué cambió, las comprobaciones realizadas y
qué requiere probarse en la placa. La CI ejecuta las pruebas de host, comprueba
los recursos y revisa archivos sensibles; no graba hardware ni usa tokens MCP.
No publica automáticamente binarios ni releases.

## Datos privados

Mantener fuera de Git: `.local/`, `.tools/`, `.env*`, claves, logs, respaldos,
binarios de flash, configuración Wi-Fi y endpoints MCP personales. `hardware.json`
es un registro local opcional, excluido porque describe una unidad concreta.
Los ejemplos de tokens de las pruebas son sintéticos.

Usa `scripts/backup.ps1` antes de la primera grabación de otra placa y conserva
el respaldo de forma privada. Las actualizaciones normales usan `flash.ps1`,
que escribe las particiones declaradas y conserva NVS. No ejecutes un borrado
completo de flash como parte de una actualización.

## Actualizar XiaoZhi o ESP-IDF

Haz la integración en una rama aparte. Compara con la revisión fijada en
`upstream.json`, conserva los cambios de CMake/Kconfig de esta placa y actualiza
la revisión declarada solo tras compilar y probarla en hardware. No hagas `git
pull` desde `xiaozhi-esp32/`: pertenece al repositorio raíz.

Para cambiar ESP-IDF, revisa también el commit fijado en `scripts/setup.ps1`.
El firmware base requiere ESP-IDF 6, no Arduino ni IDF 5.
