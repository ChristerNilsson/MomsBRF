


# Räkna ut avdragen moms i % för alla utfitrerade verifikationer, enligt resonemang nedan.

# Summan konton till kontont >=4000 är belopp exlusive moms.
# Summan till konto 2640 är momsen.
# Dessa summor tillsammans är kostnaden inkl moms.
# Full moms (100%) är 20% av kostnaden inkl moms.
# Avdragen moms (summa till 2640) / Full moms är den andel moms
# som dragits av (baserat på yta).

# Exempel:
# python analys_bertil.py "2022-01-01_2022-12-31-filtrerad.txt" "2022-01-01_2022-12-31-analyserad.txt"

# Exempel input:

# #VER "48" "220225" 20221230 "Korr: 49-221713"
# {
# #TRANS 2640 {} -255 "Ingående moms"
# #TRANS 6320 {} 255 "Juridiska åtgärder"
# }
# #VER "49" "220504" 20220408 "Lennart Söderbergs Elektriska Service AB (SIE)"
# {
# #TRANS 2440 {} -20735 "Leverantörsskulder"
# #TRANS 2640 {} 613 "Ingående moms"
# #TRANS 4344 {} 20735 "Elinstallationer"
# #TRANS 4344 {} -613 "Elinstallationer"
# }

# Exempel output:

# #VER "48" "220225" 20221230 "Korr: 49-221713"
# {
# #TRANS 2640 {} -255 "Ingående moms"
# #TRANS 6320 {} 255 "Juridiska åtgärder"
# }
# #PROSA "Moms negativ"
# #VER "49" "220504" 20220408 "Lennart Söderbergs Elektriska Service AB (SIE)"
# {
# #TRANS 2440 {} -20735 "Leverantörsskulder"
# #TRANS 2640 {} 613 "Ingående moms"
# #TRANS 4344 {} 20735 "Elinstallationer"
# #TRANS 4344 {} -613 "Elinstallationer"
# }
# #PROSA "Momsandel=14.78%"

# Beräkning görs så att man summerar 2640 med alla belopp med kontonr >= 4000 (eller kanske 3000)?
# och sedam dividerar 2640 (ingående moms), med detta och sedan dividerar resultatet
# med 0.2 (20% är momsandelen av totala utgiften)
# Exempel från X-script baserat på verif "49" "220504" som finns i kommentar ovan:
# enter:<def momsandel,<calc ($1/($1+$2+$3))/0.2*100,2>>
# enter:<momsandel 613,20735,-613>
# 14.78

import re

def analys(inFil: object, utFil: object) -> None:
   # Läg till en rad till varje verifikaton med uträknad moms-andel

   print("Räknar ut momsandel från filtrerad SIE4-fil.")

   # Öppna infil och spara i lista
   with open(inFil, 'r') as f:
      inRadTab = f.read().splitlines()

   utRader = ''
   level = 1
   nr= 1
   summaUtgiftSomBerors = 0

   for radNr in range(len(inRadTab)):

      inRad = inRadTab[radNr]

      # Exempel: #VER "49" "220504" 20220408 "Lennart Söderbergs Elektriska Service AB (SIE)"

      if level == 1:
         # Startnivå: Letar efter verifikationer.
         # Exempel:  = '#VER "49" "220504" 20220408 ...'
         match = re.search(r"^#VER .*$", inRad)

         if match:
            level = 2
            verifTitel = inRad # (För felmeddelanden)
            verif = inRad + '\n' # Lägg till första raden i en verifikation
            manuellVerif = True # Var pessimistisk till att börja med

      elif level == 2:
         # Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes
         # Exempel: {
         match = re.search(r"^{$", inRad)
         if match:
            level = 3
            verif = verif + '{' + '\n' # Lägg till {-parentes
            ingaendeMoms = 0
            konton1xxxOch3000Plus = 0

         else:
            print('*** analys(rad ' + int(radNr) + '): Förväntade "{" efter verifikationstitel "' +
               verifTitel + '" men fann istället "' + inRad + '".')
            level = 10

      elif level == 3:
         # Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes {
         # Förväntar transaktioner. Exempel:
         # #TRANS 2440 {} -20735 "Leverantörsskulder"
         # #TRANS 2640 {} 613 "Ingående moms"
         # #TRANS 4344 {} 20735 "Elinstallationer"
         # #TRANS 4344 {} -613 "Elinstallationer"

         match = re.search(r"^#TRANS (\d\d\d\d) (\{[^\}]*\}) (-?\d+).*$",inRad)
         if match:
            kontoNr = int(match.group(1))
            belopp = int(match.group(3))
            if kontoNr==2640:
               ingaendeMoms += belopp

            if kontoNr>=3000 or kontoNr<2000:
               konton1xxxOch3000Plus += belopp

            # Kopiera transaktionsrad till utfil
            verif = verif + inRad + '\n'

         else:
            # Troligen slut på verifikation
            match = re.search(r"^}$", inRad)
            if match:
               # Räkna ut momsandel enligt definition:
               # <def momsandel3,<calc ($1/($1+$2+$3))/0.2*100,2>>
               momsAndel = 0.1
               summaUtgiftInklMoms = konton1xxxOch3000Plus+ingaendeMoms
               if summaUtgiftInklMoms==0:
                  print('*** ' + verifTitel + ': Verifikation : förväntade summaUtgiftInklMoms > 0' + \
                   ' men det var 0.')
               else:
                  momsAndel = ingaendeMoms / summaUtgiftInklMoms / 0.2 * 100

               # Lägg till resultat av momsanalys.
               # Exempel: #PROSA "Momsandel=14.78%"
               momsAndelStr = '{:.2f}'.format(momsAndel)
               verif = verif + '#PROSA "Momsandel = ' + momsAndelStr + ' %"' + '\n}\n'

               if momsAndel > 13 and momsAndel < 16:
                  summaUtgiftSomBerors += summaUtgiftInklMoms

               # Skriv avslutande krullparentes
               utRader += verif
               # Gå tillbaka till nivå 1.
               level = 1
            else:
               print('*** analys(rad ' + str(radNr) + '): Förväntade "}" efter verifikationstitel "' +
                  verifTitel + '" men fann istället "' + inRad+ '".')
               level = 10
      elif level == 10:
         # Stanna här tills filen är slut
         None

   if level == 1:
      # Kopiera utRader till utfil och spara utfil.

      sie_fil_reducerad = open(utFil, "w")
      sie_fil_reducerad.write(utRader)
      print('Summa utgifter som berörs = '+str(summaUtgiftSomBerors) + '.')

   else:
      print('*** analys: Förväntade att level skulle vara 1 (normalt slut) men den var ' + str(level) + '.');

analys('2206B.txt', '2206C_bertil.txt')

# def test():
#
#    numOfArguments = len(sys.argv)-1
#
#    if numOfArguments==2:
#       # Check that input file exists first
#       if os.path.exists(sys.argv[1]):
#          print('File ' + sys.argv[1] + ' exists.')
#          ctypes.windll.user32.MessageBoxW(0, 'File ' + sys.argv[1] + ' exists.', 'xxx', 1)
#          analys(sys.argv[1], sys.argv[2])
#       else:
#          print('*** analys: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".')
#          ctypes.windll.user32.MessageBoxW(0,
#             '*** ConvFromCP437: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".',
#             'xxx', 1)
#    else: print('2 arguments were expected but '+str(numOfArguments)+ ' were found.')
#
#
# test()
