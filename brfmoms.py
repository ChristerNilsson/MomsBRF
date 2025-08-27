# SIE_FIL = "202206"
#SIE_FIL = "2022"
SIE_FIL = "2023"

UNDRE_MOMS_ANDEL = 13  # %
ÖVRE_MOMS_ANDEL = 16  # %
MOMS_KONTO = '2640'

konton = {}

class Total:
	def __init__(self):
		self.UtgiftSomBerörs = 0  # ören
		self.MomsAvdragSomBerörs = 0
		self.MomsAvdragSomEjBerörs = 0

total = Total()

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

def dump(letter, verifikationer, extra=''):
	with open(SIE_FIL + "_" + letter + ".txt", "w", encoding="utf-8") as g:
		for verifikat in verifikationer:
			if extra != '' and extra in verifikat:
				g.write(verifikat["str"] + str(verifikat[extra]) + "\n")
			else:
				g.write(verifikat["str"] + "\n")
			for t in verifikat["transaktioner"]:
				g.write(t["str"] + "\n")
			g.write("\n")

def step_1(file): # Konvertera cp437 till utf8
	with open(file + ".sie4", "r", encoding="cp437") as f:
		with open(file + "_A.txt", "w", encoding="utf-8") as g:
			s = f.read()
			g.write(s)
	lines = s.split('\n')
	konton,verifikationer = getSie(lines)
	print(f'STEP 1: {file}.sie4 (cp437) konverterad till {file}_A.txt (utf8)')
	print('  ',len(konton),'konton och',len(verifikationer), 'verifikationer')
	return verifikationer

def step_2(verifikationer): # Hopslagning mha fakturanummer
	mergade = []
	result = []
	senaste = None
	for verifikat in verifikationer:
		filter = senaste != None
		filter = filter and verifikat['fakturanr'] != ''
		filter = filter and verifikat['fakturanr'] == senaste['fakturanr']
		filter = filter and senaste['id'] + 1 == verifikat['id']
		filter = filter and any([t['konto'] == MOMS_KONTO and t['belopp'] != 0 for t in senaste['transaktioner']])
		if filter:
			senaste['transaktioner'] += verifikat['transaktioner']
			mergade.append([senaste['id'],verifikat['id']])
		else:
			result.append(verifikat)
		senaste = verifikat

	print(f'STEP 2:', len(result), 'verifikationer',len(mergade), 'hopslagna mha fakturanummer')

	dump('B',result)
	return result

def step_3(verifikationer):

	filtrerade = []
	ignorerade = []

	for verifikat in verifikationer:
		if all([t['konto'] != MOMS_KONTO for t in verifikat['transaktioner']]): continue
		filtrerade.append(verifikat)

		ingåendeMoms = 0  # ören
		kontonPlus = 0  # ören

		for transaktion in verifikat['transaktioner']:
			konto = transaktion['konto']
			belopp = 100 * transaktion['belopp']  # pga avrundningsfel i python räknas i ören
			if konto == MOMS_KONTO:
				ingåendeMoms += belopp
			if not '2000' <= konto < '3000':
				kontonPlus += belopp

		UtgiftInklMoms = kontonPlus + ingåendeMoms  # ören
		if UtgiftInklMoms == 0:
			ignorerade.append(str(verifikat['id']))
		else:
			momsAndel = ingåendeMoms / UtgiftInklMoms / 0.2 * 100
			if UNDRE_MOMS_ANDEL < momsAndel < ÖVRE_MOMS_ANDEL:
				total.UtgiftSomBerörs += UtgiftInklMoms
				total.MomsAvdragSomBerörs += ingåendeMoms
			else:
				total.MomsAvdragSomEjBerörs += ingåendeMoms

			# total.MomsAvdrag += ingåendeMoms
			verifikat['momsAndel'] = f' momsandel: {momsAndel:.2f}%'
#			print(f"   momsAndel: {momsAndel:.2f}% UtgiftInklMoms: {UtgiftInklMoms/100:.2f} =", kontonPlus/100, '+', ingåendeMoms/100)

	print(f'STEP 3:', len(filtrerade), 'verifikationer berör konto 2640')
	print("   Ignorerade verifikat pga div med noll:", len(ignorerade))
	print('     ', ' '.join(ignorerade))
	dump('C',filtrerade, 'momsAndel')
	return filtrerade

def step_4(verifikationer): # analys
	filtrerade = []

	for verifikat in verifikationer:

		filter = any([t['konto'][0:2] == '30' for t in verifikat['transaktioner']])
		if not filter: continue

		filtrerade.append(verifikat)

		ingåendeMoms = 0  # ören
		kontonPlus = 0  # ören

		for transaktion in verifikat['transaktioner']:
			konto = transaktion['konto']
			belopp = 100 * transaktion['belopp']  # pga avrundningsfel i python räknas i ören
			if konto == MOMS_KONTO:
				ingåendeMoms += belopp
			if konto[0] != '2':
				kontonPlus += belopp

	print('STEP 4:')
	print('   Antal verifikat:', len(verifikationer))
	print('   total.UtgiftSomBerörs:', total.UtgiftSomBerörs / 100)
	print('   total.MomsAvdragSomBerörs:', total.MomsAvdragSomBerörs/100)
	print('   total.MomsAvdragSomEjBerörs:', total.MomsAvdragSomEjBerörs/100)

	dump('D',filtrerade)

verifikationer = step_1(SIE_FIL) # konvertera till utf8
verifikationer = step_2(verifikationer) # Hopslagning mha fakturanummer
verifikationer = step_3(verifikationer) # Beräkna momsandel
verifikationer = step_4(verifikationer) # Beräkna kvot
