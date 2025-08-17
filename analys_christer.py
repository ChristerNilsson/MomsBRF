import sys
import os
import ctypes
import re

def analys(inFil, utFil):
	# Lägg till en rad till varje verifikaton med uträknad moms-andel

	print("Räknar ut momsandel från filtrerad SIE4-fil.")

	with open(inFil, 'r', encoding='utf8') as f:
		lines = f.readlines()

	utRader = ''
	level = 1
	summaUtgiftSomBerors = 0

	for radNr in range(len(lines)):

		line = lines[radNr].strip()

		# Exempel: #VER "49" "220504" 20220408 "Lennart Söderbergs Elektriska Service AB (SIE)"

		if level == 1:
			# Startnivå: Letar efter verifikationer.
			# Exempel:  = '#VER "49" "220504" 20220408 ...'
			#match = re.search(r"^#VER .*$", line)

			if line.startswith('#VER'):
				level = 2
				verifTitel = line # (För felmeddelanden)
				verif = line + '\n' # Lägg till första raden i en verifikation
				manuellVerif = True # Var pessimistisk till att börja med

		elif level == 2:
			# Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes
			# Exempel: {
			if line == '{':
				level = 3
				verif += '{\n'
				ingaendeMoms = 0
				konton1xxxOch3000Plus = 0
			else:
				print(f'*** analys(rad {radNr}): Förväntade {{ efter verifikationstitel {verifTitel} men fann istället {line}')
				level = 10

		elif level == 3:
			# Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes {
			# Förväntar transaktioner. Exempel:
			# #TRANS 2440 {} -20735 "Leverantörsskulder"
			# #TRANS 2640 {} 613 "Ingående moms"
			# #TRANS 4344 {} 20735 "Elinstallationer"
			# #TRANS 4344 {} -613 "Elinstallationer"

			if line.startswith('#TRANS'):
				cols = line.split(' ')
				kontoNr = cols[1]
				belopp = float(cols[3])
				#belopp = int(belopp) # Vad säger Bertil?

				if kontoNr == '2640':
					ingaendeMoms += belopp

				if kontoNr >= '3000' or kontoNr < '2000':
					konton1xxxOch3000Plus += belopp

				# Kopiera transaktionsrad till utfil
				verif += line + '\n'

			else:
				# Troligen slut på verifikation
				if line == '}':
					# Räkna ut momsandel enligt definition:
					# <def momsandel3,<calc ($1/($1+$2+$3))/0.2*100,2>>
					momsAndel = 0.1
					summaUtgiftInklMoms = konton1xxxOch3000Plus + ingaendeMoms
					if summaUtgiftInklMoms == 0:
						print(f'*** {verifTitel}: Verifikation : förväntade summaUtgiftInklMoms > 0 men det var 0')
					else:
						momsAndel = ingaendeMoms / summaUtgiftInklMoms / 0.2 * 100

					# Lägg till resultat av momsanalys.
					# Exempel: #PROSA "Momsandel=14.78%"
					momsAndelStr = '{:.2f}'.format(momsAndel)
					verif += f'#PROSA Momsandel = {momsAndelStr} %\n}}\n'

					if 13 < momsAndel < 16:
						summaUtgiftSomBerors += summaUtgiftInklMoms

					# Skriv avslutande krullparentes
					utRader += verif
					level = 1
				else:
					print(f'*** analys(rad {radNr}): Förväntade }} efter verifikationstitel {verifTitel} men fann istället {line} ')
					level = 10
		elif level == 10:
			pass

	if level == 1:
		# Kopiera utRader till utfil och spara utfil.

		sie_fil_reducerad = open(utFil, "w", encoding='utf8')
		sie_fil_reducerad.write(utRader)
		print('Summa utgifter som berörs = '+str(summaUtgiftSomBerors) + '.')

	else:
		print(f'*** analys: Förväntade att level skulle vara 1 (normalt slut) men den var {level}')

analys('2206B.txt', '2206C_christer.txt')
