from brfmoms import getSie,Transaktion

def ass(a,b):
	if a==b: return
	print('Assert failed:')
	print('   ',a)
	print('   ',b)
	assert(a == b)

xkonton, xverifikationer = getSie(
"""
#KONTO 1510 "Kundreskontra"
#KONTO 1985 "Transaktionskonto"

#VER "17" "220063" 20221230 "BGI-import (betalning)"
{
#TRANS 1510 {} -3882 20221230 "BGIP:86159,BGC:394700108723"
#TRANS 1985 {} 3882 20221230 "BGIH:26352,BGC:244"
}

#VER "17" "220064" 20221230 "BGI-import (betalning)"
{
#TRANS 1510 {} -2017 20221230 "BGIP:86160,BGC:394700108722"
#TRANS 1985 {} 2017 20221230 "BGIH:26352,BGC:244"
}
"""
)

ass(2+3, 5)
assert 2+3 == 5
assert '2' + '3' == '23'

ass(len(xkonton),2)
ass(xkonton["1510"], "Kundreskontra")
ass(xkonton["1985"], "Transaktionskonto")
ass(str(xverifikationer[0]), '17 220063 20221230 BGI-import (betalning)')
ass(len(xverifikationer[0].transaktioner),2)
ass(str(xverifikationer[0].transaktioner[0]), '1510 -3882.00 Kundreskontra')
ass(str(xverifikationer[0].transaktioner[1]), '1985 3882.00 Transaktionskonto')
ass(str(xverifikationer[1]), '17 220064 20221230 BGI-import (betalning)')

ass(xverifikationer[0].transaktioner[0].konto, '1510')
ass(xverifikationer[0].transaktioner[0].belopp, -3882.0)
ass(str(xverifikationer[0].transaktioner[0]), str(Transaktion('1510', -3882.0)))

print('Ready!')
