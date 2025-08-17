# analys2.py

# Räkna ut kvoten mellan inkomster från momsade lokaler (3053 och 3055) och alla huvudintäkter (30xx)

# Exempel:
# python analys.py "2022-01-01_2022-12-31-filtrerad.txt" "2022-01-01_2022-12-31-analyserad.txt"

# Exempel input:

# #VER "28" "220001" 20221210 "Kundfaktura Gustaf Isaksson Eldh"
# {
# #TRANS 1510 {} 2053 "Kundreskontra"
# #TRANS 3021 {} -2053 "Årsavgifter bostäder"
# }
# Addera 2053 till summaHuvudintakter

# #VER "28" "220119" 20221210 "Kundfaktura Scandinavia Concessions Management AB"
# {
# #TRANS 1510 {} 107860 "Kundreskontra"
# #TRANS 2610 {} -21572 "Utgående moms"
# #TRANS 3053 {} -75263 "Hyresintäkter lokaler, moms"
# #TRANS 3065 {} -7196 "Deb. fastighetsskatt, moms"
# #TRANS 3065 {} -3829 "Deb. fastighetsskatt, moms"
# }
# addera 75263, 7196 och 3829 till summaHuvudIntakter och till summaMomsadeLokalIntakter

# Efter att hela filen har lästs, skriver man ut kvoten mellan momsadeLokalIntakter och 
# huvudIntakter. Den bör kunna tjäna som norm för hur stor del av momsen som kan dras av
# för utgifter som varken kan hänföras till momsade lokaler eller till lägenheter.


import sys
import os
import ctypes
import re


def analys2(inFil) -> None:
   # Läg till en rad till varje verifikaton med uträknad moms-andel

   print("Räknar ut momsandel från filtrerad SIE4-fil.")

   # Öppna infil och spara i lista
   with open(inFil, 'r') as f:
      inRadTab = f.read().splitlines()

   summaHuvudIntakter = 0
   summaMomsadeLokalIntakter = 0
   level = 1   

   for radNr in range(len(inRadTab)):

      inRad = inRadTab[radNr]

      # Exempel: #VER "28" "220119" 20221210 "Kundfaktura Scandinavia Concessions Management AB"

      if level == 1:
         # Startnivå: Letar efter verifikationer.
         # Exempel:  = '#VER "28" "220119" 20221210 ...'
         match = re.search(r"^#VER .*$", inRad)

         if match:
            level = 2
            verifTitel = inRad # (För felmeddelanden)
            verif = inRad + '\n' # Lägg till första raden i en verifikation


      elif level == 2:
         # Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes
         # Exempel: {
         match = re.search(r"^{$", inRad)
         if match:
            level = 3
            verif = verif + '{' + '\n' # Lägg till {-parentes
            ingaendeMoms = 0

         else:
            print('*** analys2(rad ' + int(radNr) + '): Förväntade "{" efter verifikationstitel "' + 
               verifTitel + '" men fann istället "' + inRad + '".')
            level = 10
      
      elif level == 3:
         # Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes {
         # Förväntar transaktioner. Exempel:
         # #TRANS 1510 {} 107860 "Kundreskontra"
         # #TRANS 2610 {} -21572 "Utgående moms"
         # #TRANS 3053 {} -75263 "Hyresintäkter lokaler, moms"
         # #TRANS 3065 {} -7196 "Deb. fastighetsskatt, moms"
         # #TRANS 3065 {} -3829 "Deb. fastighetsskatt, moms"
         
         match = re.search(r"^#TRANS (\d\d\d\d) (\{[^\}]*\}) (-?\d+).*$",inRad)
         if match:
            kontoNr = int(match.group(1))
            belopp = int(match.group(3))

            # 1. Addera alla belopp till konto 30xx (fast *-1) till summaHuvudIntakter
            if 3000<=kontoNr<3100:
               summaHuvudIntakter -= belopp # Kom ihåg: minus belopp behndlas som +

            if kontoNr==3053 or kontoNr==3065:
               summaMomsadeLokalIntakter -= belopp
            # Kopiera transaktionsrad till utfil
            verif = verif + inRad + '\n'

         else:
            # Troligen slut på verifikation
            match = re.search(r"^}$", inRad)
            if match:
               # Skriv avslutande krullparentes
               # Gå tillbaka till nivå 1.
               level = 1
            else:
               print('*** analys2(rad ' + str(radNr) + '): Förväntade "}" efter verifikationstitel "' +
                  verifTitel + '" men fann istället "' + inRad+ '".')
               level = 10
      elif level == 10:
         # Stanna här tills filen är slut
         None
    
   if level == 1:
      # Räkna ut kvot mellan momsadelokalintäkter och alla huvudintälter
      kvot = summaMomsadeLokalIntakter/summaHuvudIntakter * 100

      print('Andelen momsade lokalintäkter är '+ str(kvot) + 
         ' (' + str(summaMomsadeLokalIntakter) + "/" +
         str(summaHuvudIntakter) + '.')

   else:
      print('*** analys2: Förväntade att level skulle vara 1 (normalt slut) men den var ' + str(level) + '.');



# Examples:
# python analys2.py "2022-01-01_2022-12-31-filtrerad2.txt"

def test():

   numOfArguments = len(sys.argv)-1

   if numOfArguments==1:
      # Check that input file exists first
      if os.path.exists(sys.argv[1]):
         print('File ' + sys.argv[1] + ' exists.')
         ctypes.windll.user32.MessageBoxW(0, 'File ' + sys.argv[1] + ' exists.', 'xxx', 1)
         analys2(sys.argv[1])
      else:
         print('*** Analys2: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".')
         ctypes.windll.user32.MessageBoxW(0,
            '*** Analys2: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".',
            'xxx', 1)
   else: print('*** Analys2: 1 argument was expected but '+str(numOfArguments)+ ' were found.')


test()