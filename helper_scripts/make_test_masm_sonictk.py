import requests, re

page = requests.get('https://sonictk.github.io/asm_tutorial/').text

i = page.find('correlation_avx:')
snippets = [page[i : page.find('ret', i) + 3]] # code snippet right after ‘Well...this is the assembly version that I'm going to be explaining next, in its full entirety:’
snippets += re.findall(r'correlation_ref PROC\n[\s\S]+?correlation_ref ENDP\n', page)
assert(len(snippets) == 3)

test_file = open('masm_sonictk.txt', 'w', newline="\n")

for snippet in snippets:
    mnemonics = set()

    asm = ''
    for line in snippet.split("\n"):
        s = line.split()
        if len(s) != 0 and s[0] not in mnemonics and s[0] != ';' and not s[0].startswith('multi'):
            mnemonics.add(s[0])
            comment = line.find(';')
            if comment != -1:
                line = line[:comment].rstrip(" \t")
            assert line != ''
            asm += line + "\n"

    test_file.write(asm.rstrip("\n"))

    if snippet is not snippets[-1]:
        test_file.write("\n\n" + '-' * ord('*') + "\n\n")
