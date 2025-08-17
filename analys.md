Räkna ut avdragen moms i % för alla utfitrerade verifikationer, enligt resonemang nedan.

* Summan konton till kontont >=4000 är belopp exlusive moms.
* Summan till konto 2640 är momsen.
* Dessa summor tillsammans är kostnaden inkl moms.
* Full moms (100%) är 20% av kostnaden inkl moms.
* Avdragen moms (summa till 2640) / Full moms är den andel moms som dragits av (baserat på yta).

Exempel:
```
python analys.py "2022-01-01_2022-12-31-filtrerad.txt" "2022-01-01_2022-12-31-analyserad.txt"

Exempel input:

#VER "48" "220225" 20221230 "Korr: 49-221713"
{
#TRANS 2640 {} -255 "Ingående moms"
#TRANS 6320 {} 255 "Juridiska åtgärder"
}
#VER "49" "220504" 20220408 "Lennart Söderbergs Elektriska Service AB (SIE)"
{
#TRANS 2440 {} -20735 "Leverantörsskulder"
#TRANS 2640 {} 613 "Ingående moms"
#TRANS 4344 {} 20735 "Elinstallationer"
#TRANS 4344 {} -613 "Elinstallationer"
}

Exempel output:

#VER "48" "220225" 20221230 "Korr: 49-221713"
{
#TRANS 2640 {} -255 "Ingående moms"
#TRANS 6320 {} 255 "Juridiska åtgärder"
}
#PROSA "Moms negativ"
#VER "49" "220504" 20220408 "Lennart Söderbergs Elektriska Service AB (SIE)"
{
#TRANS 2440 {} -20735 "Leverantörsskulder"
#TRANS 2640 {} 613 "Ingående moms"
#TRANS 4344 {} 20735 "Elinstallationer"
#TRANS 4344 {} -613 "Elinstallationer"
}
#PROSA "Momsandel=14.78%"
```
Beräkning:
* summera 2640 med alla belopp med kontonr >= 4000 (eller kanske 3000)?
* dividera 2640 (ingående moms), med detta
* dividera resultatet med 0.2 (20% är momsandelen av totala utgiften)

Exempel från X-script baserat på verif "49" "220504" som finns i kommentar ovan:
```
enter:<def momsandel,<calc ($1/($1+$2+$3))/0.2*100,2>>
enter:<momsandel 613,20735,-613>
```
14.78
