Filtrera ut verifikationser som refererar till konto  2640 (ingående moms)
från SIE-fil konverterad till UTF-8

Exempel:
python filter.py "2022-01-01_2022-12-31.txt" "2022-01-01_2022-12-31-filtrerad.txt"

Exempel verifikation efter filtrering och tillägg av kontonamn:
```
In:
#VER "49" "220492" 20220404 "Stockholm Exergi (SIE)"
{
#TRANS 2440 {} -194116 20220404
#TRANS 2640 {} 0 20220404
#TRANS 2640 {} 8741.95 20220404
#TRANS 4620 {} 194116 20220404
#TRANS 4620 {} -8741.95 20220404
}
#

Ut:
#VER "49" "220492" 20220404 "Stockholm Exergi (SIE)"
{
#TRANS 2440 {} -194116 20220404 "Leverantörsskulder"
#TRANS 2640 {} 8741.95 20220404 "Ingående moms"
#TRANS 4620 {} 194116 20220404 "Uppvärmning"
#TRANS 4620 {} -8741.95 20220404 "Uppvärmning"
}
```
Filtrera SIE-fil (konverterad til UTF-8)
Läs verifikationer och skriv de som refererar till
Ingående moms (2640).
Undantag: Om verifikationen bara har referens till 2640 belopp 0
	 så tas den inte heller med.

Lägg till (frivillig) transtext = "Kontonamn", t ex "Ingående moms"

```
Exempel input:
#VER "49" "220492" 20220404 "Stockholm Exergi (SIE)"
{
#TRANS 2440 {} -194116 20220404
#TRANS 2640 {} 0 20220404
#TRANS 2640 {} 8741.95 20220404
#TRANS 4620 {} 194116 20220404
#TRANS 4620 {} -8741.95 20220404
}

Ut:
#VER "49" "220492" 20220404 "Stockholm Exergi (SIE)"
{
#TRANS 2440 {} -194116 20220404 "Leverantörsskulder"
#TRANS 2640 {} 8741.95 20220404 "Ingående moms"
#TRANS 4620 {} 194116 20220404 "Uppvärmning"
#TRANS 4620 {} -8741.95 20220404 "Uppvärmning"
}
```


