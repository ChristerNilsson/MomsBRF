FILES = "2022 202206 2023".split(" ")

for file in FILES:
	print(f'{file}.sie4 (cp437) converted to {file}.txt (utf8)')
	with open(file + ".sie4", "r", encoding="cp437") as f:
		with open(file + ".txt", "w", encoding="utf-8") as g:
			g.write(f.read())
