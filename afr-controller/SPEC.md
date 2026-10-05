# AFR controller pro Bosch LSU 4.9 – specifikace (v0.1)

## Cíl
Samostatný širokopásmový řadič s TFT displejem, analogovým výstupem 0–5 V a CAN (AEM X-series).

## Architektura
- MCU: STM32G431CBT6 (LQFP48, footprint kompatibilní s G474)
- Bezčipové řízení LSU 4.9 (bez CJ125), zapojení podle ověřeného open-source modulu rusEFI wideband (viz FRONTEND.md)
- Display: TFT 2,0" / 2,4" ST7789, 240x320, SPI + DMA, částečné překreslování (framebuffer se do 32 kB RAM nevejde)
- Ovládání: 2–3 tlačítka

## Analogový výstup
- Rozsah 10–20 AFR = 0–5 V, lineárně:  V = (AFR - 10) * 0,5
- AFR 14,7 -> 2,35 V
- Mimo rozsah: oříznutí na 0 V / 5 V
- Výstup při zahřívání / chybě sondy: **TBD** (rozhodnout podle vstupu ECU)
- Realizace: DAC MCU (0–3,3 V) -> rail-to-rail opamp, zisk ~1,515 -> RC filtr -> ochrana

## CAN – rusEFI wideband protokol (převzato z rusefi/wideband, `for_rusefi/wideband_can.h`)
Zvoleno proto, aby šlo zařízení připojit k rusEFI/FOME a dalším jednotkám, které tento formát umí.
AEM X-series může přijít později jako volitelný režim (formát zatím neověřen).
- 500 kbit/s, standardní 11bitová ID, vysílání každých 10 ms
- Základní ID **0x190 + 2·(kanál + CanIndexOffset)**; každý kanál posílá 2 rámce
- Rámec 0 (ID 0x190…), 8 bajtů, little-endian (struktura `StandardData`):
  - B0 Version = 0xA0 (RUSEFI_WIDEBAND_VERSION)
  - B1 Valid (1 = topení běží v uzavřené smyčce a lambda je platná)
  - B2–B3 Lambda, 0,0001 λ/bit (uint16; 0 pokud není platná)
  - B4–B5 teplota sondy v °C
  - B6–B7 rezerva
- Rámec 1 (ID 0x191…), `DiagData`: ESR (uint16), Nernst DC v mV (uint16), PumpDuty (uint8, 255 = 100 %), Status (uint8), HeaterDuty (uint8), rezerva
- Status: 0 Preheat, 1 Warmup, 2 RunningClosedLoop, 3 SensorDidntHeat, 4 SensorOverheat, 5 SensorUnderheat
- Lambda je platná, když Nernst je v pásmu 0,45 ± 0,1 V a lambda > 0,6
- AFR (pro displej) = lambda · stechiometrie zvoleného paliva
- Volitelný 120 Ω terminátor přes jumper

## MCU – přiřazení pinů (STM32G431CBT6, LQFP-48)
Funkce pinů jsou ověřené proti seznamu alternativních funkcí ve standardním symbolu KiCadu (generátor to kontroluje).
| Pin | Funkce | Signál |
|---|---|---|
| PA0 | ADC1_IN1 | Ip_sense (proud pumpy) |
| PA1 | ADC1_IN2 | Un_sense (Nernst) |
| PA2 | ADC1_IN3 | VM |
| PA3 | ADC1_IN4 | VBAT_SENSE (dělič 100k/10k) |
| PA4 | DAC1_OUT1 | Ip_dac (budič pumpy) |
| PA5 | DAC1_OUT2 | AFR_DAC (výstup 0–5 V) |
| PA8 | TIM1_CH1 | heater_pwm |
| PB0 | GPIO | Nernst_esr_drive (Ri pulz) |
| PA11 / PA12 | FDCAN1_RX / TX | CAN |
| PB13 / PB15 | SPI2_SCK / MOSI | TFT |
| PB12 / PB10 / PB11 | GPIO | TFT CS / DC / RES |
| PB4 | TIM3_CH1 | podsvícení TFT (PWM) |
| PB5 / PB6 / PB7 | GPIO | tlačítka |
| PF0 / PF1 | RCC_OSC | krystal 8 MHz |
| PA13 / PA14 / PG10 | SWDIO / SWCLK / NRST | SWD |

## Napájení a ochrany
12 V auto: pojistka, ochrana proti přepólování, TVS (SMBJ24A), buck 5 V, LDO 3,3 V.
Ohřev LSU: low-side MOSFET + PWM, měření proudu (shunt), předehřívací rampa proti kondenzátu.

## Otevřené otázky
- Chování 0–5 V výstupu při zahřívání / chybě
- G431 vs. G474
- Konkrétní konektory
