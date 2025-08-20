import re
from pathlib import Path
import time

# SIE_FIL = "202206"
# SIE_FIL = "2022"
SIE_FIL = "2023"

preludium = []
verifikationer = []

path = Path(SIE_FIL + '.txt')
text = path.read_text(encoding="utf8")
for raw_line in text.splitlines():

	line = raw_line.strip()

	if not line: continue
	if line in ['{','}']: continue

	if line.startswith("#VER"):
		l = line.split(' ')
		verifikationer.append({'sort':[l[3],l[2],l[1]], 'text': line, 'transaktioner': []})

	elif line.startswith("#TRANS"):
		verifikationer[-1]["transaktioner"].append(line)

	else:
		preludium.append(line)

verifikationer = sorted(verifikationer, key=lambda x: x['sort'])

with open(SIE_FIL + '_sort.txt', "w", encoding="utf-8") as g:
	for p in preludium:
		g.write(p + "\n")

	for v in verifikationer:
		g.write(v["text"] + "\n")
		g.write("{\n")
		for t in v["transaktioner"]:
			g.write(t + "\n")
		g.write("}\n")
