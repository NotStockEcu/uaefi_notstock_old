# Analogový front-end LSU 4.9 (v0.1 – PŘEDBĚŽNÉ hodnoty)

Hodnoty níže vycházejí z výpočtu, ne z měření. Před výrobou je nutné ověřit simulací
(ngspice) a na prkénku s reálnou sondou. Pinout a parametry sondy ověřit proti Bosch datasheetu.

## Piny sondy (ověřit)
| Pin | Signál | Funkce |
|---|---|---|
| 1 | Ip (APE) | pumpovací proud |
| 2 | VM (Vs/Ip) | společný / virtuální zem |
| 3 | H- | topení – |
| 4 | H+ | topení + |
| 5 | Vs (RE) | Nernstova cela |
| 6 | Rcal | trimovací rezistor (spread sondy) |

## Princip
1. Nernst: Vs - VM se má držet na **450 mV**. Odchylka -> PI regulátor ve firmwaru -> nastavení Ip.
2. Ip teče pumpovací celou přes bočník 62 Ω; z úbytku se počítá lambda (tabulka Ip -> lambda).
3. Ri Nernstovy cely (~300 Ω při 780 °C, ověřit) se měří pulzem proudu a řídí PWM topení.

Regulační smyčka Ip je ve firmwaru (difuze plynu je pomalá, stačí ~ stovky Hz), takže analogová část je jen budič + měření.

## Referenční napětí
- **VM = 2,5 V** z přesné reference (např. REF3425 / LM4040-2.5), buffer opampem schopným ±5 mA
- **Vmid = 1,25 V** = VM děleno 2 (2x 10k 0,1 %) + buffer – střed pro měřicí zesilovače
- ADC reference = VDDA 3,3 V (filtrovaná, ferrit + 1 µF + 100 nF)

## Blok A – budič Ip
- DAC (0–3,3 V, střed 1,65 V) -> diferenční zesilovač, **zisk 0,5**, reference = VM
- Vdrv = VM + 0,5·(Vdac − 1,65 V)  ->  rozsah VM ± 0,83 V
- Vdrv -> bočník **62 Ω 0,1 %** -> pin Ip (přes 100 Ω ochranný rezistor mimo měřicí smyčku)
- Pumpovací cela + bočník ~ 180 Ω -> potřebný rozsah ±3 mA ~ ±0,55 V, rezerva zajištěna
- Rozlišení: 1 LSB DAC ~ 2 µA (po uzavření smyčky měřením je to dostatečné)

## Blok B – měření Ip
- Diferenční zesilovač přes bočník, **zisk 8** (Rin 10k, Rf 80k, 0,1 %), reference Vmid = 1,25 V
- Vout = 1,25 V + 8·(Ip·62 Ω)
- Rozsah Ip -2…+3 mA: Vout = 0,26 … 2,74 V (v rozsahu ADC 0–3,3 V)
- 1 LSB ADC (0,8 mV) ~ 1,6 µA; oversampling 16–64x zlepší rozlišení
- RC filtr před ADC: 1 kΩ + 100 nF (~1,6 kHz)

## Blok C – měření Vs (Nernst)
- Sledovač opampem (vstupní proud pA, aby neprotékal DC proud Nernstovou celou)
- Do ADC jde Vs i VM; Vs - VM ~ 450 mV
- Vstup chráněn 10 kΩ + Schottkyho dvojice; filtr 100 nF
- **Žádný DC proud do cely** (limit řádu µA)

## Blok D – měření Ri (pulz)
- GPIO MCU (0/3,3 V) přes **C 1 µF + R 22 kΩ** (střídavá vazba) do uzlu Vs
- Amplituda proudu ~ ±75 µA -> ΔVs ~ ±22 mV na 300 Ω
- ADC se vzorkuje synchronizovaně s hranou GPIO; Ri = ΔVs / ΔI
- Parametry (R, C, kmitočet) doladit na prkénku

## Blok E – Rcal
- Rcal (trim) měřit děličem z VDDA přes přesný rezistor + ADC (vzorkovat jen při startu)

## Topení (mimo front-end)
Low-side N-MOSFET + PWM, bočník pro měření proudu topení. Předehřívací rampa proti kondenzátu.

## Požadavky na součástky
- Opampy: **RRIO, offset < 0,5 mV, vstupní proud pA**, napájení 5 V; např. OPA2376 / TLV9062 / TLV9064
  (MCP6004 má offset až 4,5 mV – pro Vs 450 mV (±1 %) nevhodný)
- Rezistory v měřicích zesilovačích a děliči 0,1 %, bočník 62 Ω 0,1 %
- Kondenzátory C0G/X7R v filtrech

## Ověřit před schématem
- [ ] Pinout a Ri/Ip parametry z Bosch datasheetu LSU 4.9
- [ ] Simulace budiče Ip (stabilita s indukční zátěží kabelu)
- [ ] Nastavení Ri pulzu na reálné sondě
- [ ] Ochrana proti zkratu pinů sondy na baterii (12 V)
