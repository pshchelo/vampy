#!/usr/bin/env python
'''various utils for programming with command-line interface'''
def ask_bool(mesg, default):
    '''ask a yes or no question'''
    answer = None
    if default:
        default = 'y'
        mesg += ' [y]/n: '
    else:
        default = 'n'
        mesg += ' y/[n]: '
    while answer not in ('y', 'n'):
        answer = raw_input(mesg)
        if answer == '':
            answer = default
    if answer == 'y':
        answer = True
    else:
        answer = False
    return answer

def ask_choice(choices, mesg, default):
    '''ask for a value from list of string choices'''
    for choice in choices:
        if choice == default:
            mesg += '[%s]/'%default
        else:
            mesg += '%s/'%choice
    mesg = mesg[:-1]+': '
    answer = None
    while answer not in choices:
        answer = raw_input(mesg)
        if answer == '':
            answer = default
    return answer

def ask_float(mesg, default):
    '''ask for a float number'''
    mesg += '[%s]: '%default
    answer = None
    while not isinstance(answer, float):
        answer = raw_input(mesg)
        if answer == '':
            answer = default
        try:
            answer = float(answer)
        except(ValueError):
            print 'This must be float. Try again.'
    return answer

def ask_int(mesg, default):
    '''ask for a int number'''
    mesg += '[%s]: '%default
    answer = None
    while not isinstance(answer, int):
        answer = raw_input(mesg)
        if answer == '':
            answer = default
        try:
            answer = int(answer)
        except(ValueError):
            print 'This must be integer. Try again.'
    return answer

def ask_string(mesg, default):
    '''ask for a string'''
    mesg += '[%s]: '%default
    answer = raw_input(mesg)
    if answer == '':
        answer = default
    return answer

if __name__ == '__main__':
    # this is executed only if this source file is run separately
    # and not imported as module to another source file.
    print __doc__