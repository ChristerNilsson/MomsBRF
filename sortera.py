SIE_FIL = "2023"

preludium = []
verifikationer = []

with open(SIE_FIL + '.txt', "r", encoding="utf-8") as f:
	lines = f.readlines()

for line in lines:
	line = line.strip()

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
