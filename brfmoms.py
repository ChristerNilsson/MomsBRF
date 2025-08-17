import re
import time
from pathlib import Path

#SIE_FIL = "202206.sie4"
SIE_FIL = "2022.sie4"
#SIE_FIL = "2023.sie4"

UNDRE_MOMS_ANDEL = 13 # %
ÖVRE_MOMS_ANDEL = 16 # %

TILLGÅNGAR = '1'
EGET_KAPITAL_OCH_SKULDER = '2'
MOMS_KONTO = '2640'
INTÄKTER = '3'
INKöP_AV_VAROR_OCH_MATERIAL = '30'
VARUKOSTNADER = '4'
PERSONALKOSTNADER = '7'
FINANSIELLA_OCH_ÖVRIGA_INTÄKTER_O_KOSTNADER = '8'

VER_RE = re.compile(r'#VER\s+"(?P<serie>\d+)"\s+"(?P<id>\d+)"\s+(?P<datum>\d{8})\s+"(?P<text>[^"]*)"')
TRANS_RE = re.compile(r'#TRANS\s+(?P<konto>\d+)\s+{}\s+(?P<belopp>[-+]?\d+(?:[.,]\d+)?)')

class Verifikat:
	def __init__(s,serie,id,datum,text):
		s.serie = serie
		s.id = id
		s.datum = datum
		s.text = text
		s.transaktioner = []
	def addTransaktion(s,konto,belopp):
		s.transaktioner.append(Transaktion(konto,belopp))
	def __str__(s):
		return f"{s.serie} {s.id} {s.datum} {s.text}"

class Transaktion:
	def __init__(s,konto,belopp):
		s.konto = konto
		s.belopp = belopp
	def __str__(s):
		return f"{s.konto} {s.belopp:.2f} {konton[s.konto]}"

ignorerade = []

def read_sie(infile):
	path = Path(infile)
	text = path.read_text(encoding="cp437")

	verifikat = None
	in_block = False
	konton = {}
	verifikationer = []

	for raw_line in text.splitlines():
		line = raw_line.strip()
		if not line: continue

		if line.startswith("#KONTO"):
			konto = line[7:11]
			namn = line[13:-1]
			konton[konto] = namn

		if line.startswith("#VER"):
			m = VER_RE.match(line)
			if not m: raise ValueError(f"Kunde inte tolka VER-raden: {line}")
			verifikat = Verifikat(m.group("serie"), m.group("id"), m.group("datum"), m.group("text"))
			continue

		if line == "{":
			if verifikat is None: raise ValueError("Hittade '{' utan föregående VER")
			in_block = True
			continue

		if line == "}":
			if not in_block: raise ValueError("Hittade '}' utan ett pågående block")
			verifikationer.append(verifikat)
			verifikat = None
			in_block = False
			continue

		if in_block:
			tm = TRANS_RE.match(line)
			if not tm: raise ValueError(f"Kunde inte tolka TRANS-rad: {line}")
			konto = tm.group("konto")
			belopp = float(tm.group("belopp"))
			verifikat.addTransaktion(konto, belopp)

	return konton,verifikationer

start = time.time()
konton,verifikationer = read_sie(SIE_FIL)
filtrerade = [v for v in verifikationer if any([t.konto == MOMS_KONTO and t.belopp != 0 for t in v.transaktioner])]

#filtrerade2 = [v for v in verifikationer if any([t.konto[0:2] == INTÄKTER for t in v.transaktioner])]

summaUtgiftSomBerörs = 0 # ören
for verifikat in filtrerade:
	ingåendeMoms = 0 # ören
	kontonPlus = 0 # ören
	print(verifikat)
	for transaktion in verifikat.transaktioner:
		konto = transaktion.konto
		belopp = 100 * transaktion.belopp # pga avrundningsfel i python räknas i ören
		if konto == MOMS_KONTO: ingåendeMoms += belopp
		if konto[0] != EGET_KAPITAL_OCH_SKULDER: kontonPlus += belopp
		if belopp != 0: print('  ',transaktion) #f"{belopp/100:.2f}", konton[konto])

	summaUtgiftInklMoms = kontonPlus + ingåendeMoms # ören
	if summaUtgiftInklMoms == 0:
		ignorerade.append(verifikat.id)
		print("   *** DIV MED NOLL",summaUtgiftInklMoms)
	else:
		momsAndel = ingåendeMoms / summaUtgiftInklMoms / 0.2 * 100
		if UNDRE_MOMS_ANDEL < momsAndel < ÖVRE_MOMS_ANDEL:
			summaUtgiftSomBerörs += summaUtgiftInklMoms
			print(f"   momsAndel: {momsAndel:.2f}%")
		else:
			print(f"   momsAndel: {momsAndel:.2f}% summaUtgiftInklMoms: {summaUtgiftInklMoms/100:.2f}", kontonPlus/100, ingåendeMoms/100)
	print()

print("IGNORERADE VERIFIKAT:", len(ignorerade), '(', ' '.join(ignorerade), ')')
print('Antal verifikat:', len(verifikationer))
print('Antal filtrerade verifikat:', len(filtrerade))
print('summaUtgiftSomBerörs:',summaUtgiftSomBerörs/100)
print()

print(f'cpu: {time.time() - start:.6f}')
