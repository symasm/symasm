import os, sys

for root, dirs, files in os.walk('.'):
    for name in files:
        if name.endswith(('.txt', '.py', '.in', '.out', '.err')):
            if b"\r" in open(os.path.join(root, name), 'rb').read():
                sys.exit(R"\r found in file '" + os.path.join(root, name) + "'")
            filestr : str
            try:
                filestr = open(os.path.join(root, name), 'r', encoding = 'utf-8-sig').read()
            except:
                sys.exit("Exception while reading file '" + os.path.join(root, name) + "'")
            if " \n" in filestr or "\t\n" in filestr or filestr.endswith((' ', "\t")):
                sys.exit(R"whitespace at the end of line found in file '" + os.path.join(root, name) + "'")

            if not name.startswith('pre_commit.'):
                if '== None' in filestr:
                    sys.exit(R"`== None` is prohibited, please use `is None` instead, file: '" + os.path.join(root, name) + "'")
                if '!= None' in filestr:
                    sys.exit(R"`!= None` is prohibited, please use `is not None` instead, file: '" + os.path.join(root, name) + "'")

            # check_balance_of_all_char_pairs:
            for pair in ('‘’', '()', '{}', '[]'):
                i = 0
                while i < len(filestr):
                    if filestr[i] == pair[0]:
                        start_i = i
                        nesting_level = 1
                        i += 1
                        while True:
                            if i == len(filestr):
                                sys.exit("Balance check error in file '" + os.path.join(root, name) + "'")
                            ch = filestr[i]
                            i += 1
                            if ch == pair[0]:
                                nesting_level += 1
                            elif ch == pair[1]:
                                if pair[0] == '(':
                                    assert(pair[1] == ')')
                                    if filestr[i-1:i] == ':' and filestr[i+1:i+3] == '(:':
                                        assert(filestr[i] == ')')
                                        i += 2 # so that smilies :)(: don't upset the balance
                                        continue
                                nesting_level -= 1
                                if nesting_level == 0:
                                    break
                    elif filestr[i] == pair[1]:
                        if pair[0] == '(':
                            assert(pair[1] == ')')
                            if filestr[i-1:i] == ':' and filestr[i+1:i+3] == '(:':
                                assert(filestr[i] == ')')
                                i += 2 # so that smilies :)(: don't upset the balance
                                continue
                        sys.exit("Balance check error in file '" + os.path.join(root, name) + "'")
                    else:
                        i += 1
