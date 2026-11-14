# Procedencia y licencias

Las aportaciones propias de botesp se distribuyen bajo la [licencia MIT](LICENSE).
Los avisos de terceros se conservan en sus ubicaciones originales.

| Componente | Procedencia | Licencia / aviso |
| --- | --- | --- |
| Firmware base XiaoZhi | [78/xiaozhi-esp32](https://github.com/78/xiaozhi-esp32), revisión `4de00aed740595a8713b01f8332b9b2cf30685bc` | [MIT original](xiaozhi-esp32/LICENSE) |
| Inicialización del panel LILYGO | [Ejemplo factory](https://github.com/Xinyuan-LilyGO/T-Display-S3/tree/main/examples/factory) | [MIT, Xinyuan-LilyGO](xiaozhi-esp32/main/boards/lilygo/troko-t-display-s3/LICENSE.LILYGO) |
| 21 GIF originales de Troko | Paquete oficial `troko-firmware-es.zip` | [Licencia incluida en el paquete](xiaozhi-esp32/main/boards/lilygo/troko-t-display-s3/assets/LICENSE.TROKO) y [checksums de procedencia](xiaozhi-esp32/main/boards/lilygo/troko-t-display-s3/assets/provenance.json) |
| Cinco escenas de reposo | Generadas por `scripts/generate_idle_animations.py` | MIT de este proyecto |

`xiaozhi-esp32/` contiene una copia del código fuente de la revisión indicada,
con las modificaciones de la placa LILYGO. No es un submódulo: un clon normal
incluye las adaptaciones. Los archivos de terceros mantienen sus avisos propios;
no se atribuyen a botesp sus marcas, código ni ilustraciones.

No se distribuye el binario completo de Troko ni el respaldo de una placa.
Los 21 GIF se extrajeron sin modificar sus bytes y se verifican al compilar.
El SDK ESP-IDF y los componentes descargados por su gestor se instalan aparte
y conservan sus respectivas licencias.
