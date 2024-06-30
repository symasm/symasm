import requests, os, textwrap
from bs4 import BeautifulSoup
from collections import OrderedDict

sources = [('https://www.felixcloutier.com/x86/jcc', '', 'rel8'),
           ('https://www.felixcloutier.com/x86/cmovcc', 'REX.W + ', ''),
           ('https://www.felixcloutier.com/x86/setcc', 'REX + ', ''),
          ]

unambiguous_cc = set()
ambiguous_cc = set()

for source, startswith, endswith in sources:
    instructions = []

    soup = BeautifulSoup(requests.get(source).text, 'lxml')
    for row in soup.find('table').find_all('tr'):
        cols = row.find_all('td')
        if len(cols) == 0: # this is a header row
            continue

        if cols[0].string.startswith(startswith) and cols[1].text.endswith(endswith):
            instructions.append((cols[0].string, cols[1].text))

    commonprefix = os.path.commonprefix([i[1] for i in instructions])
    for opcode, inst in instructions:
        cc = inst.split(' ')[0][len(commonprefix):]
        found = None

        if cc[0] == 'N' and cc not in ('NP', 'NC'):
            for i in instructions:
                if i[0] == opcode and i[1][len(commonprefix)] != 'N':
                    #found = i[1].split(' ')[0][len(commonprefix):] # there is an instruction with the same opcode, but without N
                    break
        elif cc == 'PE':
            found = 'P'
        elif cc == 'PO':
            found = 'NP'

        if found is not None:
            ambiguous_cc.add((cc, found))
        else:
            unambiguous_cc.add(cc)

# Assign symbolic designation to each condition code
cc_to_sym = OrderedDict()
sym_used = set()
for cc in sorted(unambiguous_cc):
    orig_cc = cc
    sym = ''
    if cc[0] == 'N' and cc[1] in 'ABGL':
        sym = '!'
        cc = cc[1:]
    if cc[0] in 'ABGL':
        sym += 'u' * (cc[0] in 'AB') + ('>' if cc[0] in 'AG' else '<')
        if cc[1:] == 'E':
            sym += '='
        else:
            assert(len(cc) == 1)
    elif cc == 'E':
        sym = '=='
    elif cc == 'NE':
        sym = '!='
    elif cc.endswith('CXZ'):
        sym = cc[:-1] + '_==_0'
    elif cc[-1] in 'OCZSP':
        if cc[0] == 'N':
            assert(len(cc) == 2)
            sym = '!' + cc[-1]
        else:
            assert len(cc) == 1, cc
            sym = cc[0]
    else:
        assert False, sym

    assert sym not in sym_used, sym
    sym_used.add(sym)

    cc_to_sym[orig_cc] = sym

acc_to_sym = OrderedDict()
for cc, dcc in sorted(ambiguous_cc):
    acc_to_sym[cc] = cc_to_sym[dcc]

print(textwrap.fill('cc_to_sym = ' + repr(dict(cc_to_sym)).lower()).replace('_==_', ' == '))
print()
print(textwrap.fill('cc_to_sym.update(' + repr(dict(acc_to_sym)).lower()) + ')')

# >[https://www.felixcloutier.com/x86/setcc]:‘Appendix B, “EFLAGS Condition Codes,” in the Intel® 64 and IA-32 Architectures Software Developer's Manual, Volume 1, shows the alternate mnemonics for various test conditions.’
