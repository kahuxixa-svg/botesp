# botesp

Asistente visual para **LILYGO T-Display-S3 de 1,9 pulgadas**, basado en
[XiaoZhi ESP32](https://github.com/78/xiaozhi-esp32), con los ojos originales de
[Troko](https://trokotec.com/troko/build) y cinco escenas propias de reposo.

La versión actual funciona **sin micrófono ni parlante**. El audio está pendiente.
No es compatible directamente con T-Display clásico, AMOLED ni Pro.

## Funciones

- Pantalla vertical de 170×320, con **USB y botones arriba**.
- Hora blanca sobre fondo negro y 21 gestos originales de Troko.
- Cinco escenas automáticas: perrito con pelota, cohete, acuario, malabares y
  perrito dormido. Se alternan con gestos tras 12 segundos de reposo.
- Ojitos blancos sin pupilas: miran hacia los objetos y sonríen con los párpados.
  En el cohete aparecen únicamente dentro de la cabina.
- Temporizador visual y modo de concentración de 25 minutos, también por MCP.
- Configuración Wi-Fi desde celular o laptop, sin recompilar.
- Puente MCP opcional en la laptop para consultar hora y estado general del PC.

Las animaciones se interrumpen para dar prioridad a avisos y estados del asistente.
Los temporizadores no suenan y se pierden al reiniciar.

## Preparar y compilar en Windows

Requisitos: Git, Python 3.11 y PowerShell. Usa una ruta corta sin espacios para
evitar problemas de herramientas de compilación en Windows.

```powershell
git clone https://github.com/kahuxixa-svg/botesp.git
cd botesp
.\scripts\setup.ps1
.\scripts\build.ps1
```

`setup.ps1` descarga ESP-IDF `release/v6.1`, lo fija en la revisión probada
`c1d1695f8f8310fa7e408ab97f95ab4e76b3be88`, instala las herramientas ESP32-S3
y las dependencias de Python. La primera preparación descarga varios GB.
El SDK queda en `.tools/`, excluido de Git.

Si PowerShell impide ejecutar scripts, permite su ejecución solo en esa terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

La compilación genera `xiaozhi-esp32/build/merged-binary.bin` y los archivos de
grabación. No modifica la placa. Antes de grabarla por primera vez, guarda una
copia privada de sus 16 MB; sustituye `COM3` por el puerto correspondiente:

```powershell
.\scripts\backup.ps1 -Port COM3
.\scripts\flash.ps1 -Port COM3
```

Los respaldos quedan en `.local/backups/` junto con sus checksums. Pueden contener
contraseñas Wi-Fi: no los publiques. `flash.ps1` escribe únicamente las particiones
de `build/flash_args`, sin sobrescribir NVS. Usa ese script para actualizar una
instalación existente; grabar un binario combinado completo puede borrar NVS.

## Botones y cambio de Wi-Fi

| Acción | Resultado |
| --- | --- |
| BOOT, pulsación corta | Muestra que el audio está pendiente |
| BOOT, mantener unos 2 segundos | Abre la configuración Wi-Fi |
| Botón GPIO14, pulsación corta | Cambia el gesto de los ojos |
| GPIO14, doble pulsación | Temporizador visual de prueba de 5 segundos |
| GPIO14, mantener pulsado | Inicia concentración de 25 minutos o cancela el temporizador activo |

Para añadir otra red, mantén BOOT con el equipo encendido, conéctate desde tu
celular o laptop a `Xiaozhi-…` y abre **http://192.168.4.1**. Selecciona una red
de **2,4 GHz**, introduce la contraseña y guarda. La vinculación con XiaoZhi se
conserva. Los datos de red se configuran en la placa, nunca en el código fuente.

## Hardware y audio pendiente

La placa utiliza ESP32-S3R8, 16 MB de flash, 8 MB de PSRAM y pantalla ST7789 por
bus **i80 paralelo de 8 bits**. La tabla SPI de la guía original de Troko no
corresponde a esta placa.

El cableado futuro propuesto para INMP441 y MAX98357A está en
[docs/HARDWARE.md](docs/HARDWARE.md). El firmware actual no configura esos GPIO
como audio y todavía no permite conversar por voz.

## Puente MCP opcional

El dispositivo tiene sus propias herramientas de temporizador. Adicionalmente,
`services/mcp_bridge.py` conecta la laptop al endpoint externo de XiaoZhi y ofrece
dos herramientas de consulta: `troko_pc_status` y `troko_local_time` (Guayaquil).
No permite ejecutar comandos ni leer archivos del equipo.

```powershell
.\scripts\start-mcp.ps1
# Para detenerlo:
.\scripts\stop-mcp.ps1
```

Pega tu endpoint personal cuando lo solicite la entrada oculta. El token se pasa
por el entorno del proceso y no se guarda en archivos ni argumentos. La laptop
debe permanecer encendida para que este endpoint siga conectado. No se instala
un servicio de inicio automático. Estado y registros privados quedan en `.local/`.

## Organización y desarrollo

| Ruta | Contenido |
| --- | --- |
| `xiaozhi-esp32/` | Código fuente base incluido, con la adaptación LILYGO |
| `xiaozhi-esp32/main/boards/lilygo/troko-t-display-s3/` | Panel, botones, ojos y temporizadores |
| `scripts/` | Preparación, generación de escenas, compilación, respaldo y grabación |
| `services/` | Puente MCP y pruebas |
| `docs/` | Hardware y flujo de desarrollo |
| `.tools/`, `.local/` | SDK, respaldos y resultados locales; excluidos de Git |

Un clon normal incluye el código adaptado; no depende de un submódulo privado.
La revisión base de XiaoZhi está fijada en `upstream.json`. Conserva las futuras
modificaciones de placa dentro de su carpeta para facilitar actualizaciones.
Consulta [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) antes de publicar cambios.

## Validación y límites

Se compiló y grabó en una T-Display-S3 real. Se verificaron el arranque del panel,
PSRAM, reconexión Wi-Fi/MQTT, conservación de NVS y reproducción de las cinco
escenas. Los 480 fotogramas propios se decodifican y los 21 GIF originales se
comprueban por SHA256. Las herramientas de temporizador se registran por MCP;
la respuesta física de todos los botones y el audio no se consideran validados.

Las pruebas de host incluidas en este proyecto se ejecutan en GitHub Actions.
No sustituyen una compilación ESP-IDF ni la revisión de la pantalla física.
La suite completa de pruebas del proyecto base tiene limitaciones adicionales
en Windows y no se declara íntegramente aprobada.

Tavily, Telegram, alarmas persistentes y la palabra de activación personalizada
de Troko no están implementados. Este proyecto reutiliza sus recursos gráficos;
no recompila ni publica el binario completo de Troko.

## Licencias

Aportaciones propias bajo [MIT](LICENSE). Se conservan los avisos de XiaoZhi,
LILYGO y del paquete de recursos de Troko: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
