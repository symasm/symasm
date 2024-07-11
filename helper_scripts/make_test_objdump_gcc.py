# objdump -d --no-show-raw-insn /usr/bin/x86_64-linux-gnu-g++-9 -M suffix | cut -d ':' -f 2- > g++-9.s
# objdump -d --no-show-raw-insn /usr/bin/x86_64-linux-gnu-g++-9 -M intel | cut -d ':' -f 2- > g++-9i.s
# sudo apt-get install libgmp-dev & objdump -d --no-show-raw-insn /usr/lib/x86_64-linux-gnu/libgmp.so.10.3.2 -M intel | cut -d ':' -f 2- > libgmp.s
# sudo apt-get install gsl-bin    & objdump -d --no-show-raw-insn /usr/lib/x86_64-linux-gnu/libgsl.so.23.0.0 -M intel | cut -d ':' -f 2- > libgsl.s

import sys, re
sys.path.insert(0, '..')
import symasm

for lang in ['att', 'masm']:
    print(lang + ':')

    src = open('g++-9' + 'i'*(lang == 'masm') + '.s').read()
    errors = []
    translation = symasm.translate_to_symasm(lang, symasm.tokenize(src, errors), src, errors)

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

    mnemonics = {}
    instructions = []
    as_is_mnemonics = {}
    as_is_instructions = []
    for src_line, line in translation:
        if line == '':
            sline = src[src_line[0].start : src_line[-1].end]
            s = sline.split()
            if len(s) != 0:# and s[0] not in mnemonics:
                if s[0] not in mnemonics:
                    mnemonics[s[0]] = 1
                    instructions.append((s[0], sline))
                else:
                    mnemonics[s[0]] += 1
        elif line.startswith(src_line[0].string):
            assert(line.startswith(src_line[0].string + ' ') or line == src_line[0].string)
            if src_line[0].string not in as_is_mnemonics:
                as_is_mnemonics[src_line[0].string] = 1
                as_is_instructions.append(src_line[0].string)
            else:
                as_is_mnemonics[src_line[0].string] += 1
    total = 0
    for mnem, sline in instructions:
        print(f'x{mnemonics[mnem]}'.rjust(6) + ' ' + sline)
        total += mnemonics[mnem]
    print(f'total: {total}/{len(translation)}')
    as_is_total = 0
    for mnem in as_is_instructions:
        print(f'x{as_is_mnemonics[mnem]}'.rjust(6) + ' ' + mnem)
        as_is_total += as_is_mnemonics[mnem]
    print(f'as_is_total: {as_is_total}')
    print()

    if lang == 'masm':
        total += as_is_total
        print('Symbolic coverage: %.3f%%' % ((len(translation) - total) * 100 / len(translation)))

        pprn_total = as_is_mnemonics['push'] + as_is_mnemonics['pop'] + mnemonics['ret'] + as_is_mnemonics['nop']
        print('Symbolic+4 coverage: %.3f%%' % ((len(translation) - (total - pprn_total)) * 100 / len(translation)))
