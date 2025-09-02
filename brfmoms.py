import os # path

# SIE_FIL = "202206"
# SIE_FIL = "2022"
SIE_FIL = "2023"

# Ny: Sänks till 4 eftersom flera verifikationer verkar ha 4 istället för 14% inmatat
UNDRE_MOMS_ANDEL = 4  # %
# Gammal: UNDRE_MOMS_ANDEL = 12  # %

ÖVRE_MOMS_ANDEL = 16  # %
LEV_SKULDER_KONTO = '2440'
UTG_MOMS_KONTO = '2610'
ING_MOMS_KONTO = '2640'
MOMSAVRÄKNING_KONTO = '2650'
ÖRESUTJÄMNING_KONTO = '3740'
KLASS_TILLGÅNGAR = '1'
KLASS_UTGIFTER = '4'
GRUPP_KORTFRISTIGASKULDERLEV = '24'
GRUPP_KORTFRISTIGASKULDERÖVR = '28'

konton = {}

# Tabell med manuell klassifisering av momsade verifikationer
manuellaKlassningar = {}

class Total:
	def __init__(self):
		self.MomsAvdragSomBerörs = 0
		self.MomsAvdragSomEjBerörs = 0
		# Bfn:
		self.MomsAvdragSomBerörsAntal = 0
		self.MomsAvdragSomEjBerörsAntal = 0
		self.MomsAvdragSomEjKanKlassas = 0
		self.MomsAvdragSomEjKanKlassasAntal = 0

total = Total()

def fakturanr(text):
	arr = text.split(',')
	if len(arr) == 2: return arr[0]
	return ''

def Verifikat(original: str):
	line = original.split(" ")
	serie = int(line[1].strip('"'))
	id = int(line[2].strip('"'))
	# (ny:) BFn - rättning
	datum = line[3]
	# (gammal:) datum = line[4]
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
	verifikationer.sort(key=lambda a: a['datum'])
	return konton, verifikationer

def dump(letter, verifikationer, extra=''):
	with open(SIE_FIL + "_" + letter + ".txt", "w", encoding="utf-8") as g:
		# ++ BFn: Testa sortera efter datum
		# verifikationer.sort(key=lambda a: a['datum'])
		
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

# BFn: Ny: slår ihop alla som har samma fakturanr och ligger efter varandra
def step_2(verifikationer): # Hopslagning mha fakturanummer
	mergade = []
	result = []
	senaste = None
	for verifikat in verifikationer:
		filter = senaste != None
		filter = filter and verifikat['fakturanr'] != ''
		filter = filter and verifikat['fakturanr'] == senaste['fakturanr']
		# filter = filter and senaste['id'] + 1 == verifikat['id']
		# filter = filter and any([t['konto'] == ING_MOMS_KONTO and t['belopp'] != 0 for t in senaste['transaktioner']])
		if filter:
			senaste['transaktioner'] += verifikat['transaktioner']
			mergade.append([senaste['serie'],senaste['id'],verifikat['serie'],verifikat['id']])
		else:
			result.append(verifikat)
		senaste = verifikat

	print(f'STEP 2:', len(result), 'verifikationer',len(mergade), 'hopslagna mha fakturanummer')

	dump('B',result)
	return result

# (gammal: kräver samma id och att ING_MOMS_KONTO finns i första verifikationen) *)
def step_2_0(verifikationer): # Hopslagning mha fakturanummer
	mergade = []
	result = []
	senaste = None
	for verifikat in verifikationer:
		filter = senaste != None
		filter = filter and verifikat['fakturanr'] != ''
		filter = filter and verifikat['fakturanr'] == senaste['fakturanr']
		filter = filter and senaste['id'] + 1 == verifikat['id']
		filter = filter and any([t['konto'] == ING_MOMS_KONTO and t['belopp'] != 0 for t in senaste['transaktioner']])
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
		if all([t['konto'] != ING_MOMS_KONTO for t in verifikat['transaktioner']]): continue
		filtrerade.append(verifikat)

		ingåendeMoms = 0  # ören
		kontonPlus = 0  # ören

		for transaktion in verifikat['transaktioner']:
			konto = transaktion['konto']
			belopp = 100 * transaktion['belopp']  # pga avrundningsfel i python räknas i ören
			if konto == ING_MOMS_KONTO:
				ingåendeMoms += belopp
			if not '2000' <= konto < '3000':
				kontonPlus += belopp

		UtgiftInklMoms = kontonPlus + ingåendeMoms  # ören
		if UtgiftInklMoms == 0:
			ignorerade.append(str(verifikat['serie'])+':'+str(verifikat['id']))
		else:
			momsAndel = ingåendeMoms / UtgiftInklMoms / 0.2 * 100
			if UNDRE_MOMS_ANDEL < momsAndel < ÖVRE_MOMS_ANDEL:
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
			if konto == ING_MOMS_KONTO:
				ingåendeMoms += belopp
			if konto[0] != '2':
				kontonPlus += belopp

	print('STEP 4:')
	print('   Antal verifikat:', len(verifikationer))
	print('   total.MomsAvdragSomBerörs:', total.MomsAvdragSomBerörs/100)
	print('   total.MomsAvdragSomEjBerörs:', total.MomsAvdragSomEjBerörs/100)
	# BFn: Tillägg
	print('   total.MomsAvdragSomEjBerörsAntal:', total.MomsAvdragSomEjBerörsAntal)
	print('   total.MomsAvdragSomEjKanKlassas:', total.MomsAvdragSomEjKanKlassas/100)
	print('   total.MomsAvdragSomEjKanKlassasAntal:', total.MomsAvdragSomEjKanKlassasAntal)

	dump('D',filtrerade)


# Baserad på step_3
def step_3a(verifikationer):

	filtrerade = []
	ignorerade = []
	
	summaRedovisadIngMoms = 0
	
	antalMomsadeUtgifter = 0
	antalMomsrättelser = 0
	antalMomsredovisningar = 0

	# Redovisad och inbetald moms
	summaRedovisadIngMoms = 0
	summaRedovisadUtgMoms = 0
	summaMomsAvräkning = 0
	antalMomsavräkningar = 0
	
	# Momsrättelser
	summaMomsRättelseUppåt = 0
	antalMomsRättelserUppåt = 0
	summaMomsRättelseNedåt = 0
	antalMomsRättelserNedåt = 0

	print()
	print('STEP 3a:')


	for verifikat in verifikationer:
		if all([t['konto'] != ING_MOMS_KONTO for t in verifikat['transaktioner']]): continue
		filtrerade.append(verifikat)

		levSkulder = 0  # ören
		utgåendeMoms = 0  # ören
		ingåendeMoms = 0  # ören
		momsAvräkning = 0  # ören
		tillgångarUtgifter = 0  # ören
		öresUtjämning = 0  # ören
		
		serie = str(verifikat['serie'])
		id = str(verifikat['id'])

		# Antag att det går bra.
		verifikatOK = True
			
		andraKonton = {}
		
		for transaktion in verifikat['transaktioner']:

			konto = transaktion['konto']
			belopp = 100 * transaktion['belopp']  # pga avrundningsfel i python räknas i ören

			# if konto == LEV_SKULDER_KONTO:
			if konto[:2] == GRUPP_KORTFRISTIGASKULDERLEV:
				levSkulder += belopp
			elif konto[:2] == GRUPP_KORTFRISTIGASKULDERÖVR:
				levSkulder += belopp
			elif konto == UTG_MOMS_KONTO:
				utgåendeMoms += belopp
			elif konto == ING_MOMS_KONTO:
				ingåendeMoms += belopp
			elif konto == MOMSAVRÄKNING_KONTO:
				momsAvräkning += belopp
			elif konto[0] == KLASS_TILLGÅNGAR or int(konto[0]) >= int(KLASS_UTGIFTER):
				tillgångarUtgifter += belopp
			elif konto == ÖRESUTJÄMNING_KONTO:
				öresUtjämning += belopp
			else:
				if konto in andraKonton:
					andraKonton[konto] = andraKonton[konto] + belopp
				else:
					andraKonton[konto] = belopp
			
		if andraKonton != {}:
			# print('*** Kontroll 1 ('+ serie+','+id+'): :Oväntade andra konton:' + str(andraKonton) + '.')
			for konto in andraKonton:
				if andraKonton[konto] != 0:
					print('*** Kontroll 1 ('+ serie+','+id+'): :Oväntade andra konton:' + str(andraKonton) + 'konto = ' + str(andraKonton[konto]) + '.')

		# Om levskulder saknas men finns från året innan, komplettera
		# Exempel:
		# 2023:
		# #VER "25" "230268" 20230401 "407210, Svenska Asbestsanerarna"
		# #TRANS 2440 {} 0 20230401 Leverantörsskulder
		# #TRANS 2640 {} 1206 20230401 Ingående moms
		# #TRANS 4385 {} 4825 20230401 Skador/klotter/skadegörelse
		# #TRANS 4385 {} -6031 20230401 Skador/klotter/skadegörelse
		# 2022:
		# #VER "49" "220078" 20220114 "Svenska Asbestsanerarna (SIE)"
		# #TRANS 2440 {} -6031 20220114 Leverantörsskulder
		# #TRANS 2640 {} 0 20220114 Ingående moms
		# #TRANS 4385 {} 6031 20220114 Skador/klotter/skadegörelse
		#

		

		
		# Kolla om det är en momsad utgift.
		#TRANS 2440 {} -22538 "Leverantörsskulder"
		#TRANS 2640 {} 339 "Ingående moms"
		#TRANS 4610 {} 22538 "El"
		#TRANS 4610 {} -339 "El"
		# Den har rader på 2440 (leverantörsskulder) och på summaKonton1xxxOch4000Plus
		# Kontrollera att Leverantörsskulder (2440) och utgifter/investeringar 
		# (summaKonton1xxxOch4000Plus) finns med, men inte momsavräkning (2650)
		if levSkulder != 0 and ingåendeMoms != 0 and tillgångarUtgifter!=0 and momsAvräkning==0:

			# Kontrollera att utgifter/investeringar + ing. moms + leverantörsskulder = 0
			kontrollSumma = tillgångarUtgifter + ingåendeMoms + levSkulder
			if abs(kontrollSumma)<100:
			
				# Summan är 0 +/- 1 kr
				antalMomsadeUtgifter += 1

				UtgiftInklMoms = tillgångarUtgifter + ingåendeMoms  # ören
				if UtgiftInklMoms == 0:
					# Kontroll 2
					print('*** Kontroll 2 ('+ serie+','+id+'):  ' +
						'tillgångarUtgifter + ingåendeMoms förväntades vara > 0 men det var 0.')
					ignorerade.append(str(verifikat['id']))
				else:
					momsAndel = ingåendeMoms / UtgiftInklMoms / 0.2 * 100
					# Detektera normala och onormala momsanderlar
					if UNDRE_MOMS_ANDEL < momsAndel < ÖVRE_MOMS_ANDEL:
						# Moms som varken kan hänföras till lägenheter/omomsade lokaler, eller momsade lokaler
						# har momsats enligt en "momsnyckel" = momsad lokalyta / total yta. Dessa känns igen
						# på att det har en viss uträknad momsprocent. P g a onoggranheter i bokföringen
						# sker klassningen med ett intervall: UNDRE_MOMS_ANDEL - ÖVRE_MOMS_ANDEL
						total.MomsAvdragSomBerörs += ingåendeMoms
						total.MomsAvdragSomBerörsAntal += 1
					elif round(momsAndel) == 100:
						# 100% är normalt för utgifter som helt kan hänföras till momsade lokaler.
						total.MomsAvdragSomEjBerörs += ingåendeMoms
						total.MomsAvdragSomEjBerörsAntal += 1
					elif round(momsAndel) == 0:
						# 0% är normalt för utgifter som helt kan hänföras till lägenheter och omomsade lokaler.
						total.MomsAvdragSomEjBerörs += ingåendeMoms
						total.MomsAvdragSomEjBerörsAntal += 1
					else:
						# Andra procent antal är oväntade och måste bedömas manuellt.
						# Klassas preliminärt som att de inte berörs:
						total.MomsAvdragSomEjBerörs += ingåendeMoms
						print('*** Oväntat momsavdrag. Preliminärt klassat som ej berörs: '+str(int(ingåendeMoms/100)) + ' kr, momsandel = '+ str(round(momsAndel)) + '%): "' + str(verifikat['str']) + '".')
						total.MomsAvdragSomEjBerörsAntal += 1
						
					verifikat['momsAndel'] = f' momsandel: {momsAndel:.2f}%'

			else:
				# Kontroll 3
				print('*** Kontroll 3 ('+ serie+','+id+'):  ' +
					'Förväntade att kontrollSumma skulle vara +/- 1 kr men den var '+
					str(kontrollSumma)+ '.')
				ignorerade.append(str(verifikat['serie'])+':'+str(verifikat['id']))
				verifikatOK = False

		# Manuellt klassad momsrättelse utan levskulder
		elif ingåendeMoms != 0 and tillgångarUtgifter!=0 and momsAvräkning==0 and (serie+','+id) in manuellaKlassningar.keys():
			if manuellaKlassningar[serie+','+id].lower() == 'Berörs'.lower():
				total.MomsAvdragSomBerörs += ingåendeMoms
				total.MomsAvdragSomBerörsAntal += 1
			elif manuellaKlassningar[serie+','+id].lower() == 'Berörs ej'.lower():
				total.MomsAvdragSomEjBerörs += ingåendeMoms
				total.MomsAvdragSomEjBerörsAntal += 1
			else:
				# Kontroll 4
				print('*** Kontroll 4 ('+ serie+','+id+'):  ' +
					'Förväntade att manuell klassning av ' + serie+','+id + ' skulle vara "Berörs" eller "Berörs ej",' +
					'men den var "'+manuellaKlassningar[serie+','+id]+'".')
				ignorerade.append(str(verifikat['serie'])+':'+str(verifikat['id']))
				verifikatOK = False
			
		# Momsrättelse. Exempel:
		#TRANS 2640 {} -255 "Ingående moms"
		#TRANS 6320 {} 255 "Juridiska åtgärder"
		elif ingåendeMoms != 0 and tillgångarUtgifter!=0 and momsAvräkning==0:
		
			# Rättelse av moms från tidigare verifikation. Exempel:
			#TRANS 2640 {} -255 "Ingående moms"
			#TRANS 6320 {} 255 "Juridiska åtgärder"
			
			# Kan ej klassas eftersom levskulder antagligen är 0
			
			# Klassa tillsvidare som MomsAvdragSomEjBerörs
			antalMomsrättelser +=1
			total.MomsAvdragSomEjKanKlassas += ingåendeMoms
			total.MomsAvdragSomEjKanKlassasAntal += 1

			# Rapportera oklassbara rättelser
			# Kontroll 5:
			print('*** Kontroll 5 ('+serie+','+id+'):  ' +
				'Oklassbar momsrättelse - förväntade utgift men fann ingen: ' + str(ingåendeMoms/100) + ' kr.')

			"""
			# Rapportera oklassbara rättelser > 1000 kr
			if abs(ingåendeMoms/100)>=1000:
				# Kontroll 3:
				print('*** Kontroll 3 ('+serie+','+id+'):  ' +
					'Oklassbar momsrättelse > 1000 kr: ' + str(ingåendeMoms/100) + ' kr.')
			"""
				
			if ingåendeMoms > 0:
				summaMomsRättelseUppåt += ingåendeMoms
				antalMomsRättelserUppåt += 1
				
			if ingåendeMoms < 0:
				summaMomsRättelseNedåt += ingåendeMoms
				antalMomsRättelserNedåt += 1
					
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
		elif momsAvräkning!=0:
			antalMomsavräkningar += 1
			# Momsredovisning
			# Kontrollera att momsredovisningssumman är noll
			momsRedovisningSumma = utgåendeMoms+ingåendeMoms+momsAvräkning+öresUtjämning;
			if momsRedovisningSumma == 0:
				# Uppdatera summa redovisad och återbetald moms
				summaRedovisadIngMoms += ingåendeMoms
				summaRedovisadUtgMoms += utgåendeMoms
				summaMomsAvräkning += momsAvräkning
			else:
				print('*** Kontroll 6 ('+ serie+','+id+') - momsredovisning:  '+
					' Förväntade att momsRedovisningens summa skulle vara 0,' +
					' men den var '+ str(momsRedovisningSumma) + '.')
				verifikatOK = False
		
		elif ingåendeMoms != 0:
			print('*** Kontroll 7 ('+ serie+','+id+'): ' + 
				'Känner inte igen verifikation men ingående moms != 0.')
			verifikatOK = False
		
		# Kontroll 8:
		else:
			print('*** Kontroll 8 ('+ serie+','+id+'): ' +
				'Förväntade utgift eller momsredovisning, men fann något annat.')
			verifikatOK = False

		if not verifikatOK:
			ignorerade.append(str(verifikat['serie'])+':'+str(verifikat['id']))
			data = ''
			if levSkulder: data += ' levSkulder='+ str(levSkulder/100)
			if utgåendeMoms: data += ' utgåendeMoms='+ str(utgåendeMoms/100)
			if ingåendeMoms: data += ' ingåendeMoms='+ str(ingåendeMoms/100)
			if momsAvräkning: data += ' momsAvräkning='+ str(momsAvräkning/100)
			if tillgångarUtgifter: data += ' tillgångarUtgifter='+ str(tillgångarUtgifter/100)
			if öresUtjämning: data += ' öresUtjämning='+ str(öresUtjämning/100)
			
			print('*** Data om ej igenkänd verifikation('+ serie+','+id+'): ' +
				data + '.')

	print(f'STEP 3a:', len(filtrerade), 'verifikationer berör konto 2640')
	print("   Ignorerade verifikat pga kontroller:", len(ignorerade))
	print('     ', ' '.join(ignorerade))

	# Skriv ut info om momsrättelser som inte kunnat hänföras till anna verifikat
	print()
	print('summaMomsRättelseUppåt = ' + str(summaMomsRättelseUppåt/100) + '.')
	print('summaMomsRättelseNedåt = ' + str(summaMomsRättelseNedåt/100) + '.')
	print('antalMomsRättelserUppåt = ' + str(antalMomsRättelserUppåt) + '.')
	print('antalMomsRättelserNedåt = ' + str(antalMomsRättelserNedåt) + '.')


	# Skriv ut redovisad och inbetald moms
	print()
	print('SummaRedovisadIngMoms = ' + str(round(summaRedovisadIngMoms/100)) + '.')
	print('SummaRedovisadUtgMoms = ' + str(round(summaRedovisadUtgMoms/100)) + '.')
	print('SummaMomsAvräkning = ' + str(round(summaMomsAvräkning/100)) + '.')
	print('Antal momsavräkningar = ' + str(antalMomsavräkningar) + '.')
	print()

	dump('E',filtrerade, 'momsAndel')
	return filtrerade


import shlex

# (ny:)
def Klassning(original: str):
	parts = shlex.split(original)
	# Exempel: 25,230268 "Berörs ej"
	if len(parts) == 2:
		serieid,klass = parts
		serie,id = serieid.split(',')
	# Exempel: 25,230604 "Berörs" 3031.61
	elif len(parts) == 3:
		serieid = parts[0]
		klass = parts[1]
		serie,id = serieid.split(',')
	else:
		print('*** Klassning: Förväntade rad av typen \'25,230268 "Berörs ej"\' men fann "'+ original + '".')
		serie,id,klass = '','',''
	return serie,id,klass

# (gammal:)
def Klassning0(original: str):
	line = original.split(" ")
	serie = line[1].strip('"')
	id = line[2].strip('"')
	klass = line[3].strip('"')
	return serie,id,klass

def getKlassningar(lines):
	klassningar = {}
	for line in lines:
		# Exempel:
		# / Berörs ej eftersom 100%
		# 25-230268: Berörs ej
		line = line.strip()
		if not line: continue
		if line.startswith("/"): continue
		serie,id,klass = Klassning(line)
		klassningar[serie+','+id] = klass
	return klassningar

def step_0(): # Läs in manuell klassificering av momsade verifikat

	# Check if the file exists
	lines = ''
	file = SIE_FIL + '_klassningar.txt'
	if os.path.exists(file):
		with open(file, "r", encoding="utf-8") as f:
			s = f.read()
			lines = s.split('\n')
	else:
		print('step_0: Försökte öppna fil ' + file + ' men den fanns inte.')

	return getKlassningar(lines)


manuellaKlassningar = step_0() # Manuell klassificering av momsade verifikationer

verifikationer = step_1(SIE_FIL) # konvertera till utf8
verifikationer = step_2(verifikationer) # Hopslagning mha fakturanummer
# verifikationer = step_3(verifikationer) # Beräkna momsandel
verifikationer = step_3a(verifikationer) # Ny beräkna momsandel
verifikationer = step_4(verifikationer) # Beräkna kvot
