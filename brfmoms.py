# SIE_FIL = "202206"
# SIE_FIL = "2022"
SIE_FIL = "2023"

UNDRE_MOMS_ANDEL = 13 # %
ÖVRE_MOMS_ANDEL = 16 # %
MOMS_KONTO = '2640'

konton = {}
ignorerade = [] # pga div med noll

def Verifikat(line:str):
	line = line.split(" ")
	result = {}
	result['serie'] = line[1]
	result['id'] = line[2]
	result['datum'] = line[3]
	result['text'] = " ".join(line[4:len(line)])
	result['transaktioner'] = []
	return result
# 	def __str__(self): return f"{self.serie} {self.id} {self.datum} {self.text}"
# 	def __eq__(self, other): return str(self) == str(other) and self.transaktioner == other.transaktioner

def Transaktion(line:str):
	line = line.split(' ')
	result = {}
	result['konto'] = line[1]
	result['belopp'] = float(line[3])
	return result
# 	def __str__(self): return f"{self.konto} {self.belopp:.2f} {konton[self.konto]}"

def getSie(lines):
	verifikationer = []
	for line in lines:
		line = line.strip()
		if not line: continue
		if line in ['{', '}']: continue
		if line.startswith("#VER"):
			verifikationer.append(Verifikat(line))
		if line.startswith("#TRANS"):
			verifikationer[-1]['transaktioner'].append(Transaktion(line))
		if line.startswith("#KONTO"):
			konto = line[7:11]
			namn = line[13:-1]
			konton[konto] = namn
	return konton,verifikationer

def read_sie(infile:str):
	with open(SIE_FIL + '.txt', "r", encoding="utf-8") as f:
		lines = f.readlines()

	konton, verifikationer = getSie(lines)

	summaUtgiftSomBerörs = 0 # ören
	summaMomsadeLokaler = 0
	summaHuvudIntakter = 0
	filtrerade1 = []
	filtrerade2 = []
	lista = []
	for verifikat in verifikationer:
		id = verifikat['id']
		filter1 = any([t['konto'] == MOMS_KONTO and t['belopp'] != 0 for t in verifikat['transaktioner']])
		filter2 = any(['3000' <= t['konto'] < '3100' for t in verifikat['transaktioner']])
		if filter1: filtrerade1.append(id)
		if filter2: filtrerade2.append(id)

		ingåendeMoms = 0 # ören
		kontonPlus = 0 # ören

		if filter1:
			print(verifikat)

		for transaktion in verifikat['transaktioner']:
			konto = transaktion['konto']
			belopp = 100 * transaktion['belopp']  # pga avrundningsfel i python räknas i ören

			if filter1:
				if konto == MOMS_KONTO: ingåendeMoms += belopp
				if konto[0] != '2': kontonPlus += belopp
				print('  ',transaktion) #f"{belopp/100:.2f}", konton[konto])
			if filter2:
				if konto[0:2] == '30': summaHuvudIntakter -= belopp
				if konto in ['3053', '3065']: summaMomsadeLokaler -= belopp

		if filter1:
			summaUtgiftInklMoms = kontonPlus + ingåendeMoms # ören
			if summaUtgiftInklMoms == 0:
				ignorerade.append(id)
				print("   *** DIV MED NOLL",summaUtgiftInklMoms)
			else:
				momsAndel = ingåendeMoms / summaUtgiftInklMoms / 0.2 * 100
				if UNDRE_MOMS_ANDEL < momsAndel < ÖVRE_MOMS_ANDEL:
					summaUtgiftSomBerörs += summaUtgiftInklMoms
					print(f"   momsAndel: {momsAndel:.2f}%")
				else:
					print(f"   momsAndel: {momsAndel:.2f}% summaUtgiftInklMoms: {summaUtgiftInklMoms/100:.2f}", kontonPlus/100, ingåendeMoms/100)
				# lista.append([momsAndel,verifikat.id])
			print()
			# lista.append([ingåendeMoms/100,verifikat.id])
			# lista.append([summaUtgiftInklMoms/100, verifikat.id])
			lista.append([kontonPlus/100, id])

	print()
	print("Fil:",SIE_FIL)
	print("IGNORERADE VERIFIKAT:", len(ignorerade), '(', ' '.join(ignorerade), ')')
	print('Antal verifikat:', len(verifikationer))
	print('Antal filtrerade1 verifikat:', len(filtrerade1), '(', ' '.join(filtrerade1), ')')
	print('Antal filtrerade2 verifikat:', len(filtrerade2), '(', ' '.join(filtrerade2), ')')
	print('summaUtgiftSomBerörs:',summaUtgiftSomBerörs/100)
	print('summaMomsadeLokaler:',summaMomsadeLokaler/100)
	print('summaHuvudIntakter:',summaHuvudIntakter/100)
	print()

	sorterad_lista = sorted(lista, key=lambda x: x[0]) # -x[1]
	for i in range(20):
		print(sorterad_lista[i])

# if __name__ == "__main__":
read_sie(SIE_FIL)