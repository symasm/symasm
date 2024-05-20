import os, tempfile, symasm, sys
from typing import List

def kdiff3(str1, str2):
    for envvar in ['ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432']:
        os.environ['PATH'] += os.pathsep + os.getenv(envvar, '') + r'\KDiff3'
    command = 'kdiff3'
    for file in [('left', str1), ('right', str2)]:
        full_fname = os.path.join(tempfile.gettempdir(), file[0])
        command += ' "' + full_fname + '"'
        open(full_fname, 'w', encoding = 'utf-8-sig').write(file[1])
    os.system(command)

for fname in os.listdir('tests'):
    if fname == 'masm.txt':
        for test in open('tests/' + fname, encoding = 'utf-8').read().split("\n\n" + '-' * ord('*') + "\n\n"):
            errors: List[symasm.Error] = []
            tokens = symasm.tokenize(test, errors)
            translation = symasm.translate_masm_to_symasm(tokens, test)
            longest_src_line_len = max(src_line[-1].end - src_line[0].start for src_line, line in translation if src_line[-1].string != ':')
            annotated = ''
            for src_line, line in translation:
                i = src_line[0].start
                while i >= 0 and test[i] != "\n":
                    i -= 1
                indent = test[i+1 : src_line[0].start]
                annotated += indent + (test[src_line[0].start : src_line[-1].end].ljust(longest_src_line_len) + (' ; ' + line if line != '' else '')).rstrip(' ') + "\n"
            if annotated != test + "\n":
                print("Mismatch for test:\n" + test + "\nAnnotated:\n" + annotated)
                kdiff3(annotated, test + "\n")
                sys.exit(1)

print('All tests passed!')
