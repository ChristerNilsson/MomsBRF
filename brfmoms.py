# SIE_FIL = "202206"
# SIE_FIL = "2022"
SIE_FIL = "2023"

UNDRE_MOMS_ANDEL = 13  # %
ÖVRE_MOMS_ANDEL = 16  # %
MOMS_KONTO = '2640'

konton = {}
ignorerade = []  # pga div med noll


def fakturanr(text):
	arr = text.split(',')
	if len(arr) == 2: return arr[0]
	return ''


def Verifikat(original: str):
	line = original.split(" ")
	serie = int(line[1].strip('"'))
	id = int(line[2].strip('"'))
	datum = line[4]
	text = ' '.join(line[4:])
	return {'serie': serie, 'id': id, 'datum': datum, 'transaktioner': [], 'fakturanr': fakturanr(text),
			'str': original}


def Transaktion(original: str):
	line = original.split(' ')
	konto = line[1]
	belopp = float(line[3])
	return {'konto': konto, 'belopp': belopp, 'str': original + ' ' + konton[konto]}


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
	return konton, verifikationer


def read_sie():
	with open(SIE_FIL + '.txt', "r", encoding="utf-8") as f:
		lines = f.readlines()

	konton, verifikationer = getSie(lines)

	summaUtgiftSomBerörs = 0  # ören
	summaMomsadeLokaler = 0
	summaHuvudIntakter = 0
	filtrerade1 = []
	filtrerade2 = []
	lista = []
	senaste = None
	for verifikat in verifikationer:
		id = verifikat['id']
		# filter0 ska vara True om text[0] är lika för de två senaste verifikaten
		# id ska ligga i konsekutiv följd, dvs öka med ett.
		# 2640 ska finnas i det första verifikatet.
		if verifikat['id'] == 230036:
			z = 99
		filter0 = senaste != None
		filter0 = filter0 and verifikat['fakturanr'] != ''
		filter0 = filter0 and verifikat['fakturanr'] == senaste['fakturanr']
		filter0 = filter0 and senaste['id'] + 1 == verifikat['id']
		filter0 = filter0 and any([t['konto'] == MOMS_KONTO and t['belopp'] != 0 for t in senaste['transaktioner']])
		if filter0:
			print('tvillingar', senaste['id'], verifikat['id'])

		filter1 = any([t['konto'] == MOMS_KONTO and t['belopp'] != 0 for t in verifikat['transaktioner']])
		filter2 = any(['3000' <= t['konto'] < '3100' for t in verifikat['transaktioner']])
		if filter1: filtrerade1.append(str(id))
		if filter2: filtrerade2.append(str(id))

		senaste = verifikat

		ingåendeMoms = 0  # ören
		kontonPlus = 0  # ören

		# if filter1:
		# 	print(verifikat['str'])

		for transaktion in verifikat['transaktioner']:
			konto = transaktion['konto']
			belopp = 100 * transaktion['belopp']  # pga avrundningsfel i python räknas i ören

			if filter1:
				if konto == MOMS_KONTO: ingåendeMoms += belopp
				if konto[0] != '2': kontonPlus += belopp
			# print('  ',transaktion['str']) #f"{belopp/100:.2f}", konton[konto])
			if filter2:
				if konto[0:2] == '30': summaHuvudIntakter -= belopp
				if konto in ['3053', '3065']: summaMomsadeLokaler -= belopp

		if filter1:
			summaUtgiftInklMoms = kontonPlus + ingåendeMoms  # ören
			if summaUtgiftInklMoms == 0:
				ignorerade.append(str(id))
			# print("   *** DIV MED NOLL",summaUtgiftInklMoms)
			else:
				momsAndel = ingåendeMoms / summaUtgiftInklMoms / 0.2 * 100
				if UNDRE_MOMS_ANDEL < momsAndel < ÖVRE_MOMS_ANDEL:
					summaUtgiftSomBerörs += summaUtgiftInklMoms
				#	print(f"   momsAndel: {momsAndel:.2f}%")
				else:
					pass
			#	print(f"   momsAndel: {momsAndel:.2f}% summaUtgiftInklMoms: {summaUtgiftInklMoms/100:.2f}", kontonPlus/100, ingåendeMoms/100)
			# lista.append([momsAndel,verifikat.id])
			# print()
			# lista.append([ingåendeMoms/100,verifikat.id])
			# lista.append([summaUtgiftInklMoms/100, verifikat.id])
			lista.append([round(kontonPlus / 100, 2), id])

	print()
	print("Fil:", SIE_FIL)
	print("IGNORERADE VERIFIKAT:", len(ignorerade), '(', ' '.join(ignorerade), ')')
	print('Antal verifikat:', len(verifikationer))
	print('Antal filtrerade1 verifikat:', len(filtrerade1), '(', ' '.join(filtrerade1), ')')
	print('Antal filtrerade2 verifikat:', len(filtrerade2), '(', ' '.join(filtrerade2), ')')
	print('summaUtgiftSomBerörs:', summaUtgiftSomBerörs / 100)
	print('summaMomsadeLokaler:', summaMomsadeLokaler / 100)
	print('summaHuvudIntakter:', summaHuvudIntakter / 100)
	print()

	sorterad_lista = sorted(lista, key=lambda x: x[0])  # -x[1]
	for i in range(min(20, len(lista))):
		print(sorterad_lista[i])


read_sie()