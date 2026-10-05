# Analogový front-end LSU 4.9 (v0.2)

Revize po porovnání s open-source modulem **rusEFI/FOME wideband, board_module rev C**
(github.com/rusefi/wideband: `hardware/board_module/wideband_controller.kicad_sch`,
`firmware/wideband_config.h`, `firmware/sampling.cpp`, `firmware/boards/f0_module`).
Hodnoty označené „ref." jsou převzaté z tohoto ověřeného návrhu. Ostatní jsou moje a stále neověřené.
Pinout a parametry sondy ještě ověřit proti Bosch datasheetu.

## Co se změnilo oproti v0.1
| # | v0.1 (chyba / odchylka) | v0.2 |
|---|---|---|
| 1 | **„Žádný DC proud do Nernstovy cely"** – chybně | Cela dostává malý stálý proud ~20 µA: 62 kΩ z 3,3 V do uzlu Un (ref.). Bez něj nevzniká referenční kyslík. |
| 2 | VM = 2,5 V z druhé reference | VM = VDDA/2 = 1,65 V (dělič 1k/1k + buffer + 10 Ω + 1 µF), VDDA = 3,3 V z REF3033 (ref.) |
| 3 | Měření Ri přes střídavou vazbu (1 µF + 22 kΩ) | GPIO přímo přes 22 kΩ do uzlu Un, přepíná se 0/3,3 V; výpočet ve firmwaru (ref.) |
| 4 | Vs a VM čtené samostatně | Rozdílový zesilovač gain 2,7: Un_sense = 2,7·(Un − VM) (ref.) |
| 5 | Měření Ip: gain 8, střed 1,25 V, běžný opamp | Zero-drift opamp (AD8628) – offset přímo posouvá lambdu kolem Ip = 0. Střed na VM. |
| 6 | Blok E: měření Rcal děličem | V ref. se Rtrim nečte; 61,9 Ω je zapojen mezi piny Rtrim a Ip. Blok E zrušen, otázka níže. |
| 7 | MCP6004 označen jako nevhodný | Pro Nernst, VM a budič stačí (ref. je používá). Nevhodný je jen pro měření Ip. |

## Piny sondy (jména jako v ref.; pořadí na konektoru ověřit)
LSU_Ip, LSU_Vm, LSU_Rtrim, LSU_Un, heater+ / heater-.

## Napájení analogu
- VDDA = 3,3 V z REF3033 (ref.), filtr 1 µF + 100 nF. Opampy na 3,3 V (ref.).
- VM = VDDA/2 z děliče 1k/1k, buffer opampem, 10 Ω do pinu VM, 1 µF na pinu (ref.).

## Blok A – budič Ip
- Ref.: PWM 46,8 kHz z MCU přes RC filtr a opamp v diferenční konfiguraci (68k vstupy, 10k||33 nF zpětná vazba), výstup přes 47 Ω.
- Pro G431 navrhuji místo PWM použít **DAC**: nižší zvlnění. Zapojení opampu zůstane stejné; hodnoty ověřit simulací.
- Řízení: PID ve firmwaru, **kP 50, kI 10000**, perioda 2 ms (ref.), výstup v mA.
- Pumpu zapnout až když je sonda dost horká: teplota ≥ cíl − 200 °C (ref.), jinak Ip = 0, aby se sonda nepoškodila.

## Blok B – měření Ip
- Bočník **61,9 Ω** mezi LSU_Rtrim a LSU_Ip (ref.).
- Rozdílový zesilovač AD8628, **gain 10** (10k vstupy, 100k zpětná vazba a referenční odpor k VM), střed na VM (ref.).
- Rozsah ±(1,65 V / 10 / 61,9 Ω) = ±2,67 mA. Ip_mA = −1000 · Vsense / (10 · 61,9) (ref.).
- Filtr před ADC 3,3 kΩ + 100 nF (ref.); vzorkování 2,5 kHz, ADC oversampling 24x, digitální filtr ~50 Hz.
- Poznámka: ref. rozsah ±2,67 mA je těsný. Pokud sonda v čerstvém vzduchu dá > 2,5 mA, zvaž gain 8 (±3,3 mA).

## Blok C – měření Nernstu
- Buffer opampem z pinu Un (Un_sense_in), aby se nezatěžoval uzel.
- Rozdílový zesilovač: 10k vstupy, 27k zpětná vazba a 27k k zemi, **gain 2,7** (ref.). 450 mV -> 1,215 V.
- Cíl regulace: Nernst = **0,45 V** (ref.). Lambda platná, když je Nernst v pásmu 0,45 ± 0,1 V a lambda > 0,6.

## Blok D – Ri (ESR) a teplota
- GPIO 0/3,3 V přes **22 kΩ** do uzlu Un; GPIO se přepíná při každém vzorku (ref.).
- Ri = R / (Vcc / ΔV_AC − 1) − 10 Ω (sériový odpor VM) (ref.).
- ΔV_AC se získá z tří posledních vzorků, aby se odečetl trend DC složky.
- Teplota z tabulky Ri -> °C (ref., LSU 4.9): 80 Ω = 1030 °C, 300 Ω = 780 °C, 1000 Ω = 642 °C.
- Cíl topení: **780 °C ~ 300 Ω** (ref.).

## Blok E – topení
- Spínač low-side VND14NV04 (ref.), hradlo přes 1 kΩ + pull-down 1 kΩ, PWM z MCU.
- Řídicí logika (ref.): předehřev 5 s, napětí topení 7,5 V − PID(Ri), timeout rozehřátí 60 s,
  start až při baterii > 9,5 V, vypnutí pod 7 V.
- Referenční modul bez měření napětí topení předpokládá 13 V po 5 s. Pro přesnější řízení přidat dělič (VBatt_Sense 100k/10k jako v ref.).

## Požadavky na součástky
- Ip měření: zero-drift opamp (AD8628 / OPA2188), rezistory 0,1 %, bočník 61,9 Ω 0,1 %.
- Ostatní opampy: MCP6004 stačí (ref.).
- Reference: REF3033 (3,3 V).

## Otevřené otázky
- [ ] Trim odpor sondy: ref. ho nečte. Ověřit v Bosch datasheetu, zda je v proudové cestě a jestli ovlivňuje přesnost Ip.
- [ ] Pinout konektoru LSU 4.9 a Ri / Ip parametry z Bosch datasheetu
- [ ] Budič Ip s DAC místo PWM: ověřit stabilitu simulací
- [ ] Ochrana pinů proti zkratu na baterii
- [ ] Přepočet Ip -> lambda: tabulka je v `firmware/lambda_conversion.cpp` ref. repozitáře (licence ověřit před kopírováním)
