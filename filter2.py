# filter2.py

# Filtrera ut verifikationer som refererar till konto  30xx (rörelsens huvudintäckter)
# från SIE-fil konverterad till UTF-8. Lägg till kontonamn på utfiltrerade verifikationer.
# Ta bort gammal "trans"-text om det behövs.
# Debiterade förbrukningskostnader tas tillsvidare inte med. Jag antar att de kommer från
# den gemensammal elen. Om lägenheternas el debiteras via föreningen ska väl inte påverka kvoten
# mellan inkomster från momsade lokaler och inkomster från alla lokaler och lägenheter?

# Exempel:
# python filter2.py "2022-01-01_2022-12-31.txt"
# python filter2.py "2022-01-01_2022-12-31.txt" "2022-01-01_2022-12-31-filtrerad2.txt"

# Exempel verifikation med konton i 30xx, före och efter filtrering och tillägg av kontonamn:
# In:
# #VER "28" "220119" 20221210 "Kundfaktura Scandinavia Concessions Management AB"
# {
# #TRANS 1510 {} 107860 20221210
# #TRANS 2610 {} -21572 20221210
# #TRANS 3053 {} -75263 20221210 "Hyra lokal, januari-mars[br]Baskostnad 63 375 kr, indexkostnad 11 888 kr"
# #TRANS 3065 {} -7196 20221210 "Preliminär fastighetsskatt, januari-mars"
# #TRANS 3065 {} -3829 20221210 "Retroaktiv Fastighetsskatt 2022, januari-januari"
# }
# 
# Ut:
# #VER "28" "220119" 20221210 "Kundfaktura Scandinavia Concessions Management AB"
# {
# #TRANS 1510 {} 107860 20221210 "Kundreskontra"
# #TRANS 2610 {} -21572 20221210 "Utgående moms"
# #TRANS 3053 {} -75263 20221210 "Hyresintäkter lokaler, moms"
# #TRANS 3065 {} -7196 20221210 "Deb. fastighetsskatt, moms"
# #TRANS 3065 {} -3829 20221210 "Deb. fastighetsskatt, moms"
# }

import sys
import os
import ctypes
import re

def filtrera2(inFil: object, utFil: object) -> None:
   # Filtrera SIE-fil (konverterad til UTF-8)
   # Läs verifikationer och skriv de som refererar till 30xx

   # Ta bort transdatum och allt efter
   # Lägg till transtext = "Kontonamn", t ex ""Hyresintäkter lokaler, moms""

   # In:
   # #VER "28" "220119" 20221210 "Kundfaktura Scandinavia Concessions Management AB"
   # {
   # #TRANS 1510 {} 107860 20221210
   # #TRANS 2610 {} -21572 20221210
   # #TRANS 3053 {} -75263 20221210 "Hyra lokal, januari-mars[br]Baskostnad 63 375 kr, indexkostnad 11 888 kr"
   # #TRANS 3065 {} -7196 20221210 "Preliminär fastighetsskatt, januari-mars"
   # #TRANS 3065 {} -3829 20221210 "Retroaktiv Fastighetsskatt 2022, januari-januari"
   # }
   # 
   # Ut:
   # #VER "28" "220119" 20221210 "Kundfaktura Scandinavia Concessions Management AB"
   # {
   # #TRANS 1510 {} 107860 "Kundreskontra"
   # #TRANS 2610 {} -21572 "Utgående moms"
   # #TRANS 3053 {} -75263 "Hyresintäkter lokaler, moms"
   # #TRANS 3065 {} -7196 "Deb. fastighetsskatt, moms"
   # #TRANS 3065 {} -3829 "Deb. fastighetsskatt, moms"
   # }


   print("Filtrerar en text-fil konverterad från SIE4 för att hitta huvudintäkter")
   print('Läser från "' + inFil + '".')

   # Öppna infil och spara i lista
   with open(inFil, 'r') as f:
      inRadTab = f.read().splitlines()

   utRader = ''
   antalVerifikationer = 0
   level = 1
   nr= 1
   kontoNamnTab = {}

   for radNr in range(len(inRadTab)):

      inRad = inRadTab[radNr]

      # Exempel: #VER "28" "220119" 20221210 "Kundfaktura Scandinavia Concessions Management AB"

      if level == 1:
         # Startnivå: Letar efter kontouppgifter och verifikationer.

         # Kontouppgifter. Exempel: "#KONTO 4620 "Uppvärmning""
         match = re.search(r'^#KONTO (\d\d\d\d) "([^\"]*)".*$', inRad)

         if match:
            # Spara kontonamn i kontoNamnTab
            kontoNr = int(match.group(1))
            kontoNamnTab[kontoNr] = match.group(2)

         # Verifikationer. Exempel:  = '#VER "28" "220119" 20221210 "Kundfaktura Scandinavia Concessions Management AB"'
         match = re.search("^#VER .*$", inRad)

         if match:
            level = 2
            verifTitel = inRad # (För felmeddelanden)
            verif = inRad + '\n' # Lägg till första raden i en verifikation
            sparaVerif = False # Var pessimistisk tills konto 30xx hittats

      elif level == 2:
         # Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes
         # Exempel: {
         match = re.search("^{$", inRad)
         if match:
            level = 3
            verif = verif + '{' + '\n' # Lägg till {-parentes
         else:
            print('*** Filter2(rad ' + int(radNr) + '): Förväntade "{" efter verifikationstitel "' + 
               verifTitel + '" men fann istället "' + inRad + '".')
            level = 10
      
      elif level == 3:
         # Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes {
         # Förväntar transaktioner.
         # Exempel: #TRANS 1510 {} 107860 20221210
         #          #TRANS 2610 {} -21572 20221210
         #          #TRANS 3053 {} -75263 20221210 "Hyra lokal, januari-mars[br]Baskostnad 63 375 kr, indexkostnad 11 888 kr"
         #          ...
         match = re.search(r"^#TRANS (\d\d\d\d) (\{[^\}]*\}) (-?\d+).*$",inRad)
         if match:
            # Ta med verifikationer som har kontering till 30xx (rörelsens huvudintäkter)
            # Filtrera bort rader med kontering till moms = 0
            kontoNr = int(match.group(1))
            if 3000<=kontoNr<3100:
               # 30xx
               sparaVerif = True

            verif = verif + \
               '#TRANS ' + \
               match.group(1) + \
               ' ' + match.group(2) + \
               ' ' + match.group(3) + \
               ' ' + '"' + kontoNamnTab[kontoNr] + '"' + '\n'

         else:
            # Troligen slut på verifikation
            match = re.search("^}$", inRad)
            if match:
               verif = verif + '}' + '\n'  # Lägg till }-parentes
               if sparaVerif:
                  # Addera verifikationen till utRader
                  utRader += verif
                  antalVerifikationer +=1
               # Gå tillbaka till nivå 1.
               level = 1
            else:
               print('*** Filter2(rad ' + int(radNr) + '): Förväntade "{" efter verifikationstitel "' +
                  verifTitel + '" men fann istället "' + inRad+ '".')
               level = 10
      elif level == 10:
         # Stanna här tills filen är slut
         None

   # Efter for-loopen 
   if level == 1:

      # Kopiera utRader till utfil och spara utfil.
      print('Antal utvalda verifikationer = '+str(antalVerifikationer) + '.')
      print('Skriver till "' + utFil + '".')
      sie_fil_reducerad = open(utFil, "w")
      sie_fil_reducerad.write(utRader)
   else:
      print('*** filter2: Förväntade att level skulle vara 1 (normalt slut) men den var ' + str(level) + '.');

# Exempel:
# python filter2.py "2022-01-01_2022-12-31.txt"
# python filter2.py "2022-01-01_2022-12-31.txt" "2022-01-01_2022-12-31-filtrerad.txt"

def test():

   numOfArguments = len(sys.argv)-1

   if numOfArguments==1 or numOfArguments==2:
      # Check that input file exists first
      if os.path.exists(sys.argv[1]):
         print('File ' + sys.argv[1] + ' exists.')
         ctypes.windll.user32.MessageBoxW(0, 'File ' + sys.argv[1] + ' exists.', 'xxx', 1)
         if numOfArguments==2:
            filter(sys.argv[1], sys.argv[2])
         else:
            arg2 = os.path.splitext(sys.argv[1])[0]
            arg2 = arg2 + '-filtrerad2'+ '.txt'
            filtrera2(sys.argv[1], arg2)
      else:
         print('*** Filter1: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".')
         ctypes.windll.user32.MessageBoxW(0,
            '*** Filter1: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".',
            'xxx', 1)
   else: print('*** Filter2: 1-2 arguments were expected but '+str(numOfArguments)+ ' were found.')

test()