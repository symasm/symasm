# objdump -d --no-show-raw-insn /usr/bin/x86_64-linux-gnu-g++-9 -M suffix | cut -d ':' -f 2- > g++-9.s
# objdump -d --no-show-raw-insn /usr/bin/x86_64-linux-gnu-g++-9 -M intel | cut -d ':' -f 2- > g++-9i.s
# objdump -d --no-show-raw-insn /usr/bin/python3.6 -M intel | cut -d ':' -f 2- > python3i.s
# ldconfig -p | grep libgmp
# sudo apt-get install libgmp-dev & objdump -d --no-show-raw-insn /usr/lib/x86_64-linux-gnu/libgmp.so.10.3.2 -M intel | cut -d ':' -f 2- > libgmp.s
# sudo apt-get install gsl-bin    & objdump -d --no-show-raw-insn /usr/lib/x86_64-linux-gnu/libgsl.so.23.0.0 -M intel | cut -d ':' -f 2- > libgsl.s

import sys, re
sys.path.insert(0, '..')
import symasm
from typing import List, Dict, Tuple

for lang in ['att', 'masm'][1:]:
    asm_fname = 'g++-9' + 'i'*(lang == 'masm') + '.s'
    asm_fname = 'python3i.s'
    print(lang + ' (' + asm_fname + '):')

    src = open(asm_fname).read()
    src = re.sub(r'\n\?_\d{5}:', '\n', src) # remove inline labels (for `objconv` output)
    errors: List[symasm.Error] = []
    translation = symasm.translate_to_symasm(lang, symasm.tokenize(src, errors), src, errors)

    errors = list(filter(lambda e: not (src[e.pos:e.end] == 'movsd' and src[e.end+53:e.end+53+6] == " _ A5\n"), errors)) # for strange `objconv` output [`movsd` instruction without operands]

    def check_errors(errors, test):
        if len(errors) > 0:
            for e in errors:
                next_line_pos = test.find("\n", e.pos)
                if next_line_pos == -1:
                    next_line_pos = len(test)
                prev_line_pos = test.rfind("\n", 0, e.pos) + 1
                sys.stderr.write('Error: ' + e.message + "\n"
                                + test[prev_line_pos:next_line_pos] + "\n"
                                + re.sub(r'[^\t]', ' ', test[prev_line_pos:e.pos]) + '^'*max(1, e.end - e.pos) + "\n")
            sys.exit(len(errors))

    check_errors(errors, src)

    mnemonics: Dict[str, int] = {}
    instructions: List[Tuple[str, str]] = []
    as_is_mnemonics: Dict[str, int] = {}
    as_is_instructions: List[str] = []
    for src_line, line in translation:
        if line == '':
            sline = src[src_line[0].start : src_line[-1].end]
            s = sline.split()
            if len(s) != 0:# and s[0] not in mnemonics:
                mnem = s[0]
                if len(src_line) == 3 and src_line[1].string in ('label', 'LABEL', 'PROC', 'db', 'dw', 'dd', 'dq'):
                    mnem = src_line[1].string
                elif src_line[-1].string == ':':
                    mnem = ':'
                elif len(src_line) == 2 and src_line[0].string == 'int' and src_line[1].string == '3':
                    mnem = 'int_3'
                elif len(src_line) > 3 and src_line[1].string in ('db', 'dw', 'dd') and src_line[0].string.startswith('?_'):
                    mnem = src_line[1].string
                elif len(src_line) == 2 and src_line[1].string in ('ENDP', 'PROC'):
                    mnem = src_line[1].string
                if mnem not in mnemonics:
                    mnemonics[mnem] = 1
                    instructions.append((mnem, sline))
                else:
                    mnemonics[mnem] += 1
        elif line.startswith(src_line[0].string) and src_line[0].string != 'fst':
            assert(line.startswith(src_line[0].string + ' ') or line == src_line[0].string)
            if src_line[0].string not in as_is_mnemonics:
                as_is_mnemonics[src_line[0].string] = 1
                as_is_instructions.append(src_line[0].string)
            else:
                as_is_mnemonics[src_line[0].string] += 1

    total_instructions = len(translation)
    data_decls = ''
    total = 0
    for mnem, sline in instructions:
        s = f'x{mnemonics[mnem]}'.rjust(6) + ' ' + sline
        if mnem not in ('public', 'extern', 'ALIGN', 'label', 'LABEL', 'PROC', 'ENDP', 'db', 'dw', 'dd', 'dq', ':', 'int_3'):
            print(s)
            total += mnemonics[mnem]
        else:
            data_decls += s + "\n"
            total_instructions -= mnemonics[mnem]
    print(f'total: {total}/{total_instructions}')
    as_is_total = 0
    for mnem in as_is_instructions:
        print(f'x{as_is_mnemonics[mnem]}'.rjust(6) + ' ' + mnem)
        as_is_total += as_is_mnemonics[mnem]
    print(f'as_is_total: {as_is_total}')
    print()

    if data_decls != '':
        print('Data declarations:')
        print(data_decls)

    if lang == 'masm':
        total += as_is_total
        print('Symbolic coverage: %.3f%%' % ((total_instructions - total) * 100.0 / total_instructions))

        pprn_total = as_is_mnemonics['push'] + as_is_mnemonics['pop'] + mnemonics['ret'] + as_is_mnemonics['nop']
        print('Symbolic+4 coverage: %.3f%%' % ((total_instructions - (total - pprn_total)) * 100.0 / total_instructions))
