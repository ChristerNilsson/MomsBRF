import time

def filtrera(inFil, utFil):
	print("Filtrerar en text-fil konverterad från SIE4 ")
	print('Läser från ' + inFil)

	# Öppna infil och spara i lista
	with open(inFil, 'r', encoding='utf8') as f:
		lines = f.readlines()
	lines = [line.strip() for line in lines]
	utRader = ''
	antalVerifikationer = 0
	level = 1

	konton = {}

	for radNr in range(len(lines)):

		line = lines[radNr]
		if line == "": continue

		# Exempel: #VER "49" "220046" 20220101 "Storholmen Förvaltning AB (SIE)"

		if level == 1:
			# Startnivå: Letar efter kontouppgifter och verifikationer.

			if line.startswith("#KONTO"):
				cols = line.split(" ")
				kontoNr = cols[1]
				kontoNamn = ''
				for i in range(2,len(cols)):
					kontoNamn += ' ' + cols[i]
				konton[kontoNr] = kontoNamn # .strip('"')

			# Kontouppgifter. Exempel: "#KONTO 4620 "Uppvärmning""

		 # Verifikationer. Exempel:  = '#VER "49" "220046" 20220101'
			if line.startswith("#VER"):
				level = 2
				verifTitel = line # (För felmeddelanden)
				verif = line + '\n' # Lägg till första raden i en verifikation
				sparaVerif = False # Var pessimistisk tills konto 2640 hittats

		elif level == 2:
			# Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes
			# Exempel: {
			if line == "{":
				level = 3
				verif += '{\n' # Lägg till {-parentes
			else:
				print(f'*** Filter(rad {radNr} ): Förväntade "{{" efter verifikationstitel "{verifTitel}" men fann istället "{line}"')
				level = 10

		elif level == 3:
			# Verifikationsnivå: Har läst titelrad till verifikation och inledande krullparentes {
			# Förväntar transaktioner.
			# Exempel: #TRANS 2440 {} -34823 20220101
			#			 #TRANS 2640 {} 0 20220101
			#			 ...
			if line.startswith('#TRANS'):
				# Ta med verifikationer som har kontering till ingående moms > 0
				# Filtrera bort rader med kontering till moms = 0
				cols = line.split(' ')
				kontoNr = cols[1]
				laggTillRad = True
				if kontoNr == '2640':
					belopp = float(cols[3])
					if belopp != 0: sparaVerif = True
					if belopp == 0: laggTillRad = False

				# Skriv verifikation exklusive transdata men med tillagd transtext = "kontonamn"
				# Undantag: Utelämna momsrader med belopp 0
				if laggTillRad:
					verif += f"#TRANS {cols[1]} {cols[2]} {cols[3]}{konton[kontoNr]}\n"

				if kontoNr == '2640':
					belopp = float(cols[3])
					if belopp != 0: sparaVerif = True

			else:
				# Troligen slut på verifikation
				if line == '}':
					verif += '}' + '\n'  # Lägg till }-parentes
					if sparaVerif:
						# Addera verifikationen till utRader
						utRader += verif
						antalVerifikationer +=1
					level = 1
				else:
					print(f'*** Filter(rad {radNr}): Förväntade {{ efter verifikationstitel {verifTitel} men fann istället "{line}"')
					level = 10
		elif level == 10:
			# Stanna här tills filen är slut
			pass

	if level == 1:
		# Kopiera utRader till utfil och spara utfil.
		print(f'Antal utvalda verifikationer = {antalVerifikationer}')
		print('Skriver till ' + utFil)
		sie_fil_reducerad = open(utFil, "w", encoding='utf8')
		sie_fil_reducerad.write(utRader)
	else:
		print(f'*** filtrera: Förväntade att level skulle vara 1 (normalt slut) men den var {level}')

start = time.time()
filtrera('2206A.txt','2206B.txt')
secs = f"{time.time() - start:.6f}"
print(secs)
