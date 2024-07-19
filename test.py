import os, tempfile, symasm, sys, re
from typing import List

for envvar in ['ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432']:
    os.environ['PATH'] += os.pathsep + os.getenv(envvar, '') + r'\KDiff3'

def kdiff3(str1, str2):
    command = 'kdiff3'
    for file in [('left', str1), ('right', str2)]:
        full_fname = os.path.join(tempfile.gettempdir(), file[0])
        command += ' "' + full_fname + '"'
        open(full_fname, 'w', encoding = 'utf-8-sig').write(file[1])
    os.system(command)

for fname in os.listdir('tests'):
    if not fname.endswith('.txt'):
        continue

    for test in open('tests/' + fname, encoding = 'utf-8').read().split("\n\n" + '-' * ord('*') + "\n\n"):
        def check_errors(errors, test):
            if len(errors) > 0:
                sys.stderr.write('In ' + fname + ":\n\n")
                for e in errors:
                    next_line_pos = test.find("\n", e.pos)
                    if next_line_pos == -1:
                        next_line_pos = len(test)
                    prev_line_pos = test.rfind("\n", 0, e.pos) + 1
                    sys.stderr.write('Error: ' + e.message + "\n"
                                    + test[prev_line_pos:next_line_pos] + "\n"
                                    + re.sub(r'[^\t]', ' ', test[prev_line_pos:e.pos]) + '^'*max(1, e.end - e.pos) + "\n")
                sys.exit(len(errors))

        if fname == 'errors.txt':
            source = ''
            source_errors: List[symasm.Error] = []
            prev_line = ''
            for line in test.split("\n"):
                lline = line.lstrip(' ')
                if lline.startswith('^'):
                    if lline.lstrip('^').startswith('Error: '):
                        source_errors.append(symasm.Error(lline[lline.find(':') + 2:], len(source) + line.find('^'), len(source) + line.find('Error: ')))
                        continue
                source += prev_line
                prev_line = line + "\n"
            source += prev_line

            assert(len(source_errors) != 0)

            errors: List[symasm.Error] = []
            tokens = symasm.tokenize(source, errors)
            translation = symasm.translate_to_symasm('masm', tokens, source, errors)

            if len(errors) == 0:
                sys.exit("There should be error(s) in test:\n" + test)
            else:
                for i in range(min(len(source_errors), len(errors))):
                    if errors[i] != source_errors[i]:
                        sys.stderr.write(f"Mismatch for error #{i+1} in test:\n{test}\n")
                        kdiff3(str(errors[i]), str(source_errors[i]))
                        sys.exit(1)
                if len(source_errors) != len(errors):
                    if len(source_errors) > len(errors):
                        sys.exit(f"There should be an additional error '{source_errors[len(errors)].message}' in test:\n" + test)
                    else:
                        sys.exit(f"Extra error '{errors[len(source_errors)].message}' in test:\n" + test)

        elif fname.startswith('masm'):
            errors: List[symasm.Error] = []
            tokens = symasm.tokenize(test, errors)
            translation = symasm.translate_to_symasm('masm', tokens, test, errors)
            check_errors(errors, test)

            longest_src_line_len = max(src_line[-1].end - src_line[0].start for src_line, line in translation if src_line[-1].string != ':')
            annotated = ''
            for src_line, line in translation:
                i = src_line[0].start - 1
                while i >= 0 and test[i] != "\n":
                    i -= 1
                indent = test[i+1 : src_line[0].start]
                annotated += indent + (test[src_line[0].start : src_line[-1].end].ljust(longest_src_line_len) + (' ; ' + line if line != '' else '')).rstrip(' ') + "\n"

            if annotated != test + "\n":
                sys.stderr.write("Mismatch for test:\n" + test + "\nAnnotated:\n" + annotated + "\n[in file '" + fname + "']")
                kdiff3(annotated, test + "\n")
                sys.exit(1)

        elif fname.startswith('att'):
            errors: List[symasm.Error] = []
            _, att, masm, syma = test.split("\n\n")

            def translate(lang, src):
                translation = symasm.translate_to_symasm(lang, symasm.tokenize(src, errors), src, errors)
                check_errors(errors, src)
                return "\n".join((' ' * 8 if src_line[-1].string != ':' else '') + (line if line != '' else src[src_line[0].start : src_line[-1].end]) for src_line, line in translation if line != '-')

            att_translation = translate('att', att)
            masm_translation = translate('masm', masm)

            if att_translation != masm_translation:
                sys.stderr.write("Mismatch for test:\n" + test + "\n[between AT&T and MASM in file '" + fname + "']")
                kdiff3(att_translation, masm_translation)
                sys.exit(1)

            if masm_translation != syma:
                sys.stderr.write("Mismatch for test:\n" + test + "\n[between symasm and MASM in file '" + fname + "']")
                kdiff3(syma, masm_translation)
                sys.exit(1)

        else:
            sys.exit('Unknown test file: ' + fname)

if __name__ == '__main__':
    for fname in os.listdir('tests/cli'):
        if not fname.endswith('.in'):
            continue
        fname = 'tests/cli/' + fname

        cmd: str
        if sys.argv[0].endswith('.py'):
            cmd = 'python' + '3'*(os.name != 'nt') + ' symasm.py'
        else:
            cmd = './'*(os.name != 'nt') + 'symasm'

        try:
            os.remove('test_symasm_config.txt')
        except:
            pass
        if os.path.isfile(fname + '.config.txt'):
            open('test_symasm_config.txt', 'w').write(open(fname + '.config.txt').read())

        if os.system(cmd + f' {fname} -f {fname}.out --config test_symasm_config.txt 2>{fname}.err') != 0:
            if os.path.isfile(fname[:-2] + 'err'):
                if open(fname + '.err').read() != open(fname[:-2] + 'err').read():
                    sys.stderr.write('Mismatch for ' + fname + "\n")
                    os.system(f'kdiff3 {fname}.err {fname[:-2]}err')
                    sys.exit(1)
            else:
                sys.exit('Failure exit code returned for ' + fname)

        elif open(fname + '.out').read() != open(fname[:-2] + 'out').read():
            sys.stderr.write('Mismatch for ' + fname + "\n")
            os.system(f'kdiff3 {fname}.out {fname[:-2]}out')
            sys.exit(1)

        os.remove(fname + '.out')
        os.remove(fname + '.err')

    os.remove('test_symasm_config.txt')

    print('All tests passed!')
