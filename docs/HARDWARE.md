# LILYGO T-Display-S3 original

Modelo de 1,9 pulgadas, ESP32-S3R8, 16 MB de flash y 8 MB de PSRAM octal.
Pantalla ST7789 170×320, bus i80 paralelo de 8 bits. No corresponde a las
variantes AMOLED, Pro ni a la T-Display clásica con ESP32.

La interfaz usa formato vertical con USB y botones arriba, giro de 180° del
panel y desplazamiento (35,0). Los GIF conservan su orientación interna.

| Función integrada | GPIO |
| --- | --- |
| Alimentación del panel | 15, nivel alto |
| Retroiluminación | 38, activo alto |
| RD / WR | 9, nivel alto / 8 |
| DC / CS / RST | 7 / 6 / 5 |
| Datos D0–D7 | 39, 40, 41, 42, 45, 46, 47, 48 |
| BOOT / segundo botón | 0 / 14 |
| Medición de batería de la placa | 4 |

## Propuesta para audio futuro

Estos pines están expuestos y libres respecto al panel y los botones en la
placa original. **No están configurados para audio en la variante actual.**
Se proponen dos buses I2S con relojes independientes para entrada a 16 kHz y
salida a 24 kHz; su funcionamiento eléctrico todavía no se ha probado.

| Señal | INMP441 | MAX98357A |
| --- | --- | --- |
| BCLK / SCK | GPIO1 | GPIO11 |
| WS / LRCLK / LRC | GPIO2 | GPIO12 |
| Datos | SD del micrófono → GPIO10 | GPIO13 → DIN del amplificador |

- INMP441: VDD a **3V3**, GND común, L/R a GND para canal izquierdo.
- MAX98357A: VIN puede usar 5V del USB; también admite 3V3 con menor potencia.
  Las señales digitales usan lógica de 3,3 V.
- Altavoz entre SPK+ y SPK−: **ninguna salida del altavoz se conecta a GND**.
  Se revisarán SD/GAIN y el altavoz según el módulo exacto antes de activar audio.
- GPIO11–13 no podrán usarse simultáneamente para una ampliación SD externa.
  No copiar los pines de audio de la guía Troko: varios pertenecen al LCD.

Fuentes: [pinout del fabricante](https://github.com/Xinyuan-LilyGO/T-Display-S3/blob/main/image/T-DISPLAY-S3.jpg),
[inicialización factory](https://github.com/Xinyuan-LilyGO/T-Display-S3/tree/main/examples/factory),
[INMP441](https://product.tdk.com/system/files/dam/doc/product/sw_piezo/mic/mems-mic/data_sheet/inmp441.pdf),
[MAX98357A](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX98357A-MAX98357B.pdf).
