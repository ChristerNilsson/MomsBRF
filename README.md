
Detta paket innehåller filer för att analysera omprövning av moms för bostadsrättsföreningar:
   * conv.py + conv1.py In: bokföringsfil kodad i CP437. Ut: bokföringsfil kodad i UTF-8.
   * filter.py In: bokföringsfil kodad i UTF-8. Ut: Nerminskad fil.
   * analys.py In: Nerminskad fil. Ut: Nerminskad fil analys för varje verifikation
   * 2022-06-15_2022-06-30.SE: Källdata
   * Readme.md (denna fil)

Kör i kommandoprompt:
```
C: ...>python conv.py "2022-06-15_2022-06-30.SE" "2022-06-15_2022-06-30.txt"
C: ...>python filter.py "2022-06-15_2022-06-30.txt" "2022-06-15_2022-06-30-filtrerad.txt"
C: ...>python analys.py "2022-06-15_2022-06-30-filtrerad.txt" "2022-06-15_2022-06-30-analyserad.txt"
```
Bakgrund:
Genom ett domstolsutslag nyligen, får bostadsrättsföreningarna dra av en större del av momsen för kostnader som varken kan hänföras till lägenheter eller momsade lokaler.

Den preliminöra avsikten med detta skript är:
1. Visa hur stor del av momsen som föreningen dragit av tidigare, för kostnader som varken kan hänföras till lägenheter eller momsade lokaler.
2. Räkna ut summan av kostnader som varken kan hänföras till lägenheter eller momsade lokaler.

Utifrån detta, och om man vet hur stor del av inkomsterna som kommer från momsade lokaler, kan man räkna ut hur mycket bostadsrättsföreningen kan få tillbaka från skattemyndigheten för varje år.

Möjligheten för omprövning finns fr o m för 2019. Ansökan för 2019 måste vara inlämnad före årets (2025) slut.

En preliminär uppskattning av hur mycket momsskatt som Brf Rörstrand 29-37 kan få tillbaka, för år 2022, är 843 000 kronor.

