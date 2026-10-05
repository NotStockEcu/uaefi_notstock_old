# AFR controller pro Bosch LSU 4.9 – specifikace (v0.1)

## Cíl
Samostatný širokopásmový řadič s TFT displejem, analogovým výstupem 0–5 V a CAN (AEM X-series).

## Architektura
- MCU: STM32G431CBT6 (LQFP48, footprint kompatibilní s G474)
- Bezčipové řízení LSU 4.9 (bez CJ125): regulátor Ip, měření Ri, PWM ohřevu ve firmwaru
- Display: TFT 2,0" / 2,4" ST7789, 240x320, SPI + DMA, částečné překreslování (framebuffer se do 32 kB RAM nevejde)
- Ovládání: 2–3 tlačítka

## Analogový výstup
- Rozsah 10–20 AFR = 0–5 V, lineárně:  V = (AFR - 10) * 0,5
- AFR 14,7 -> 2,35 V
- Mimo rozsah: oříznutí na 0 V / 5 V
- Výstup při zahřívání / chybě sondy: **TBD** (rozhodnout podle vstupu ECU)
- Realizace: DAC MCU (0–3,3 V) -> rail-to-rail opamp, zisk ~1,515 -> RC filtr -> ochrana

## CAN – AEM X-series (ověřit proti datasheetu AEM 30-0300 před implementací)
- 500 kbit/s, 29bitové ID, výchozí 0x00000180
- Rámec 8 bajtů, big-endian:
  - B0–B1: lambda, 0,0001 λ/bit (uint16)
  - B2–B3: kyslík, 0,001 %/bit (int16)
  - B4: napájení, 0,1 V/bit
  - B5: rezervováno
  - B6: příznaky (platnost lambdy, stav sondy)
  - B7: chybové příznaky
- AFR = lambda * stechiometrie (zvolené palivo, např. benzín 14,7)
- Volitelný 120 Ω terminátor přes jumper

## Napájení a ochrany
12 V auto: pojistka, ochrana proti přepólování, TVS (SMBJ24A), buck 5 V, LDO 3,3 V.
Ohřev LSU: low-side MOSFET + PWM, měření proudu (shunt), předehřívací rampa proti kondenzátu.

## Otevřené otázky
- Chování 0–5 V výstupu při zahřívání / chybě
- G431 vs. G474
- Konkrétní konektory
