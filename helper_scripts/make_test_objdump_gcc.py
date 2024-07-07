# objdump -d --no-show-raw-insn /usr/bin/x86_64-linux-gnu-gcc-9 -M suffix | cut -d ':' -f 2- > gcc-9.s
# objdump -d --no-show-raw-insn /usr/bin/x86_64-linux-gnu-gcc-9 -M intel | cut -d ':' -f 2- > gcc-9i.s

import sys, re
sys.path.insert(0, '..')
import symasm

for lang in ['att', 'masm']:
    print(lang + ':')

    src = open('gcc-9' + 'i'*(lang == 'masm') + '.s').read()
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

    mnemonics = set()
    for src_line, line in translation:
        if line == '':
            sline = src[src_line[0].start : src_line[-1].end]
            s = sline.split()
            if len(s) != 0 and s[0] not in mnemonics:
                mnemonics.add(s[0])
                print(sline)
    print()
