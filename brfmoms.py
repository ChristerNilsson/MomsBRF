import re
from pathlib import Path
import time

#SIE_FIL = "202206"
SIE_FIL = "2022"
#SIE_FIL = "2023"

UNDRE_MOMS_ANDEL = 13 # %
ÖVRE_MOMS_ANDEL = 16 # %
MOMS_KONTO = '2640'

VER_RE = re.compile(r'#VER\s+"(?P<serie>\d+)"\s+"(?P<id>\d+)"\s+(?P<datum>\d{8})\s+"(?P<text>[^"]*)"')
TRANS_RE = re.compile(r'#TRANS\s+(?P<konto>\d+)\s+{}\s+(?P<belopp>[-+]?\d+(?:[.,]\d+)?)')

konton = {}
verifikationer = []
ignorerade = [] # pga div med noll

class Verifikat:
	def __init__(self,serie:str, id:str, datum:str, text:str):
		self.serie = serie
		self.id = id
		self.datum = datum
		self.text = text
		self.transaktioner = []
	def __str__(self): return f"{self.serie} {self.id} {self.datum} {self.text}"
	def __eq__(self, other): return str(self) == str(other) and self.transaktioner == other.transaktioner

	def addTransaktion(self,konto:str,belopp:str): self.transaktioner.append(Transaktion(konto,belopp))

	def dump(self):
		print()
		print(f"{self}")
		for t in self.transaktioner:
			print(f"   {t}")

class Transaktion:
	def __init__(self,konto:str,belopp:str):
		self.konto = konto
		self.belopp = belopp
	def __str__(self):
		return f"{self.konto} {self.belopp:.2f} {konton[self.konto]}"

def getSie(text: str):

	verifikat = None
	in_block = False
	# konton = {}
	# verifikationer = []

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

def read_sie(infile:str):
	start = time.time()
	path = Path(infile + '.txt')
	text = path.read_text(encoding="utf8")
	konton, verifikationer =  getSie(text)

	summaUtgiftSomBerörs = 0 # ören
	summaMomsadeLokaler = 0
	summaHuvudIntakter = 0
	filtrerade1 = []
	filtrerade2 = []
	for verifikat in verifikationer:
		filter1 = any([t.konto == MOMS_KONTO and t.belopp != 0 for t in verifikat.transaktioner])
		filter2 = any(['3000' <= t.konto < '3100' for t in verifikat.transaktioner])
		if filter1: filtrerade1.append(verifikat.id)
		if filter2: filtrerade2.append(verifikat.id)

		ingåendeMoms = 0 # ören
		kontonPlus = 0 # ören
		#print(verifikat)
		for transaktion in verifikat.transaktioner:
			konto = transaktion.konto
			belopp = 100 * transaktion.belopp  # pga avrundningsfel i python räknas i ören

			if filter1:
				if konto == MOMS_KONTO: ingåendeMoms += belopp
				if konto[0] != '2': kontonPlus += belopp
				if belopp != 0: print('  ',transaktion) #f"{belopp/100:.2f}", konton[konto])

			if filter2:
				if konto[0:2] == '30': summaHuvudIntakter -= belopp
				if konto in ['3053', '3065']: summaMomsadeLokaler -= belopp

		if filter1:
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

	print(f'cpu: {time.time() - start:.6f}')

if __name__ == "__main__":
	read_sie(SIE_FIL)