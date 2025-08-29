


# Räkna ut avdragen moms i % för alla utfitrerade verifikationer, enligt resonemang nedan.

# Summan konton till kontont >=4000 är belopp exlusive moms.
# Summan till konto 2640 är momsen.
# Dessa summor tillsammans är kostnaden inkl moms.
# Full moms (100%) är 20% av kostnaden inkl moms.
# Avdragen moms (summa till 2640) / Full moms är den andel moms
# som dragits av (baserat på yta).

# Exempel:
# python analys.py "2022-01-01_2022-12-31-filtrerad.txt" "2022-01-01_2022-12-31-analyserad.txt"

# Input är redan filtrerad.
# Den innehåller bara verifikationer som referens till 2640 med belopp <>


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


import sys
import os
import ctypes
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

   # strategi: Räkna hela tiden ut kvoten mellan summa 2640 och 2440.
   # Den bör vara cirka 0.2*0.148 = 0.0296 (1/33.8)
   # testa vid var 5:e verifikation

   # (Osäker om det behövs någon initialisering av dessa här, de  0:as vid "{" i början på varje verifikat)
   summa2440 = 0 # Leverantörsskulder, per verifikat
   summa2640 = 0 # Ingående moms, per verifikat
   summa2650 = 0 # Momsavräkning

   Accumulerat2440 = 0 # Leverantörsskulder, accumulerat
   Accumulerat2610 = 0 # Utgående moms, accumulerat
   Accumulerat2640 = 0 # Ingående moms, accumulerat

   summaÅterbetalbarMoms = 0

   totalSummaRedovisad2640 = 0 # Total redovisad ingående moms
   summaNyckelMoms = 0 # Ingående Moms som påverkas av lagändringen
   summaFastMoms = 0 # Ingående Moms som inte påverkas av lagändringen

   # nominellKvot = 0.0296 # 0.2*0.148 = 1/33.78 # Kvot mellan Ingående moms och leverantörsskkuld
      # (kostnad inkl moms)

   verif = ''
   
   for radNr in range(len(inRadTab)):

      inRad = inRadTab[radNr]

      # Exempel: #VER "49" "220504" 20220408 "Lennart Söderbergs Elektriska Service AB (SIE)"

      if level == 1:
         # Startnivå: Letar efter verifikationer. Detektera bara serie och vernr
         # Exempel:  = '#VER "49" "220504" 20220408 ...'
         match = re.search(r'^#VER ("[^"]*"|[^ ]+) +("[^"]*"|[^ ]+).*$',inRad)

         if match:
            level = 2

            # För felmeddelanden och diagnostic:
            verifTitel = inRad 
            serieNr = match.group(1)
            verNr = match.group(2)

            verif+= inRad + '\n' # Lägg till första raden i en verifikation
            manuellVerif = True # Var pessimistisk till att börja med

      elif level == 2:
         # Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes
         # Exempel: {
         match = re.search(r"^{$", inRad)
         if match:
            level = 3
            verif = verif + '{' + '\n' # Lägg till {-parentes

            summa2440 = 0 # Leverantörsskkulder
            summa2610 = 0 # Utg. moms
            summa2640 = 0 # Ing. moms
            summa2650 = 0 # Momsavräkning
            summa3740 = 0 # Öresavrundning
            summaKonton1xxxOch4000Plus = 0

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

            # 1. Uträkning av ingående moms för att identifiera utgifter som 
            # varken kan hänföras till bostäder eller till momsade lokaler
            
            # Leverantörsskulder
            if kontoNr==2440: 
               summa2440 += belopp
               Accumulerat2440 += belopp

            # Utgående moms
            elif kontoNr==2610: 
               summa2610 += belopp
               Accumulerat2610 += belopp

            # Ingående moms
            elif kontoNr==2640: 
               summa2640 += belopp
               Accumulerat2640 += belopp

            # Momsavräkning
            elif kontoNr == 2650: 
               summa2650 += belopp

            # Investering (1xxx) eller kostnad (4000plus)
            elif kontoNr<2000 or kontoNr>=4000:
               summaKonton1xxxOch4000Plus += belopp

            # Öresavrundning
            elif kontoNr==3740:
               summa3740+= belopp

            else:
               print('*** Kontroll 1 ('+ serieNr+','+verNr+'): Förväntade Levskulder (2440), '+
                  'Ing. moms (2640), Momsavräkning (2650), investering/utgift (<2000/>=4000) eller '
                  + 'öresAvrundning (3740),  men fann ' + str(kontoNr) + '.')

            # Kopiera transaktionsrad till utfil
            verif = verif + inRad + '\n'

         else:
            # Troligen slut på verifikation
            match = re.search(r"^}$", inRad)
            if match:

               # Slut på transaktioner

               # Kolla om det är utgift, exempel:
               #TRANS 2440 {} -22538 "Leverantörsskulder"
               #TRANS 2640 {} 339 "Ingående moms"
               #TRANS 4610 {} 22538 "El"
               #TRANS 4610 {} -339 "El"
               # Den har rader på 2440 (leverantörsskulder) och på summaKonton1xxxOch4000Plus
               # Kontrollera att Leverantörsskulder (2440) och utgifter/investeringar 
               # (summaKonton1xxxOch4000Plus) finns med, men inte momsavräkning (2650)
               if (summa2440 != 0) and (summa2640 != 0) and (summaKonton1xxxOch4000Plus!=0) and (summa2650==0):

                  # Kontrollera att utgifter/investeringar + ing. moms + leverantörsskulder = 0
                  kontrollSumma = summaKonton1xxxOch4000Plus + summa2640 + summa2440
                  if -3<=kontrollSumma <= 3:
                     # Räkna ut momsandel som leverantörsskuld * 0.2
                     fullMoms = summa2440 * 0.2 * -1
                     ingåendeMoms = summa2640
                     momsAndel = ingåendeMoms / fullMoms
                     momsAndelProcent = momsAndel * 100
                     if momsAndelProcent>100:
                        print('*** Kontroll 1a ('+ serieNr+','+verNr+') - momsuträkning: '+
                           ', fullmoms = '+ str(fullMoms) + 'ingåendeMoms=' + str(ingåendeMoms) +
                           ', momsandel = ' + str(momsAndel) + ', momsAndelProcent = ' +
                           str(momsAndelProcent) + 
                           ', Förväntade att momsandel % skulle vara <100 men den var ' +
                           str(momsAndelProcent) + '.')

                     # Lägg till Momsandel som #PROSA. 
                     # Exempel: #PROSA "Momsandel=14.78%"
                     momsAndelStr = '{:.2f}'.format(momsAndelProcent)
                     verif = verif + '#PROSA "Momsandel = ' + momsAndelStr + ' %"' + '\n'

                     # Bedöm om momsen ska uppgraderas enligt ny momsnyckel eller inte
                     if momsAndelProcent > 13 and momsAndelProcent < 16:
                        summaNyckelMoms += summa2640
                        # Räkna ut ny avdragbar moms och återbetalbar moms
                        avdragbarMoms = 0.448 * fullMoms
                        återbetalbarMoms = avdragbarMoms-ingåendeMoms
                        summaÅterbetalbarMoms += återbetalbarMoms
                     else:
                        # Denna verifikation påverkas inte av lagändringen
                        summaFastMoms += ingåendeMoms
                  else:
                     # Kontroll 2
                     print('*** Kontroll 2 ('+ serieNr+','+verNr+'):  ' +
                        'Förväntade att kontrollSumma skulle vara -3..3  men den var '+
                        str(kontrollSumma)+ '.')

               # Smärre momsrättelse. Exempel:
               #TRANS 2640 {} -255 "Ingående moms"
               #TRANS 6320 {} 255 "Juridiska åtgärder"
               elif (summa2640 != 0) and (summaKonton1xxxOch4000Plus!=0) and summa2650==0:

                  # Rättelse av moms från tidigare verifikation. Exempel:
                  #TRANS 2640 {} -255 "Ingående moms"
                  #TRANS 6320 {} 255 "Juridiska åtgärder"
                  if abs(summa2640)<1000:
                     summaFastMoms += summa2640
                  else:
                     # Kontroll 1b:
                     print('*** Kontroll 1b ('+ serieNr+','+verNr+'):  ' +
                        'Förväntade momsrättelse<1000 kr men fann en rättelse på '+
                        str(abs(summa2640)) + 'kr.')
            
               # Momsredovisning
               # Exempel:
               # VER "49" "220443" 20220331 "Moms (SIE)"
               # {
               #TRANS 2610 {} 193904 "Utgående moms"
               #TRANS 2610 {} 76257 "Utgående moms"
               #TRANS 2640 {} -29382 "Ingående moms"
               #TRANS 2650 {} -240780 "Momsavräkning"
               #TRANS 3740 {} 0 "Öres- och kronutjämning"
               # }
               elif summa2650!=0:
                  # Momsredovisning
                  print('+++ momsredovisning: summa2640 = ' + str(summa2640) + '.')
                  # Kontrollera att 2610+2640+2650+3740 = 0
                  if abs(summa2610+summa2640+summa2650+summa3740) < 3:
                     # Räkna ut total summa redovisad ingående moms
                     totalSummaRedovisad2640 += summa2640
                  else:
                     print('*** Kontroll 4 ('+ serieNr+','+verNr+') - momsredovisning:  '+
                        ' Förväntade att summa 2610, 2640, 2650 och 3740 skulle vara inom -3 - 3,' +
                        ' men det var '+ str(summa2610+summa2640+summa2650+summa3740) + '.')

               # Kontroll 5:
               else:
                  print('*** Kontroll 5 ('+ serieNr+','+verNr+'): ' +
                     'Förväntade utgift eller momsredovisning, men fann något annat:' +
                     ' summa2440='+ str(summa2440) + ', summa2640 = ' + str(summa2640) +
                     ', summa2650 = ' + str(summa2650) + ', summa3740 = ' + str(summa3740) + 
                     ', summaKonton1xxxOch4000Plus = ' + str(summaKonton1xxxOch4000Plus) +  '.')

               # Skriv avslutande krullparentes
               verif += '}' + '\n'
               utRader += verif
               verif = ''

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

      # Kontroll
      sie_fil_reducerad = open(utFil, "w")
      sie_fil_reducerad.write(utRader)

      print('Accumulerat2440 (leverantörsskulder) = '+str(Accumulerat2440)+'.')
      print('Accumulerat2640 (Ing. Moms) = '+str(Accumulerat2640)+'.')
      print('summaFastMoms = '+str(summaFastMoms)+'.')

      # Utskrift för att se hur stor del av ingående moms som berörs.
      print('SummaNyckelMoms = ' + str(summaNyckelMoms) + '.')
      print('Summma avdragen ing. Moms = ' + str(summaNyckelMoms+summaFastMoms))
      print('Total summa redovisad ingående moms = '+str(totalSummaRedovisad2640) + '.')
      
   else:
      print('*** analys: Förväntade att level skulle vara 1 (normalt slut) men den var ' + str(level) + '.');


def test():

   numOfArguments = len(sys.argv)-1

   if numOfArguments==2:
      # Check that input file exists first
      if os.path.exists(sys.argv[1]):
         print('File ' + sys.argv[1] + ' exists.')
         ctypes.windll.user32.MessageBoxW(0, 'File ' + sys.argv[1] + ' exists.', 'xxx', 1)
         analys(sys.argv[1], sys.argv[2])
      else:
         print('*** analys: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".')
         ctypes.windll.user32.MessageBoxW(0,
            '*** ConvFromCP437: Expected name of existing file in command arg 1 but found "' + sys.argv[1] + '".',
            'xxx', 1)
   else: print('2 arguments were expected but '+str(numOfArguments)+ ' were found.')


test()