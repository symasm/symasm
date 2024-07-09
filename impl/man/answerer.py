from .registers import *
from .instructions import *

extra_info = ''

def any_extra_info():
    return extra_info != ''

def answerer(request):
    request = request.upper()

    global extra_info
    if extra_info != '':
        if request == 'YES':
            ans = extra_info
            extra_info = ''
            return ans
        elif request == 'NO':
            extra_info = ''
            return 'Ok.'
        else:
            return 'Please answer "yes" or "no".'

    ans = ''
    if request in instructions_info:
        ans = instructions_info[request]
    elif request in registers_info:
        ans = registers_info[request]

    if ans == '':
        return '-'

    if '<EXTRA />' in ans:
        ans, extra_info = ans.split('<EXTRA />')

    return ans
