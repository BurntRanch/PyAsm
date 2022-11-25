import regex
import sys
import os
from helpers.pyasm_errors import AccessError

__out_function__ = ""
__skip_until__ = ""
__in_while_loop__ = False
__while_loop__ = []

def exit():
    sys.stdout.write("Goodbye!\n")
    sys.exit(0)

def __process_file__(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
        for i in lines:
            process(i)


def process(line, ignore_while_loop = False):
    global __out_function__, __skip_until__, __while_loop__, __in_while_loop__
    if line.startswith("$") or line == '' or (__skip_until__ and (not line.endswith(__skip_until__))):
        if line.endswith("ENDIF;"):
            __skip_until__ = ""
        return
    if line == "EXIT FUNC;":
        __out_function__ = ""
        return
    if __out_function__:
        globals()[__out_function__].append(line.removeprefix('    ').removeprefix('\t'))
        return
    if __in_while_loop__ and not line == "ENDWHILE;" and not ignore_while_loop:
        __while_loop__.append(line)
        return
    if regex.match("CALL .*;", line):
        if regex.match("CALL .* ARGS \(.*\);", line):
            if " ".join(line.split(" ")[3][:-1]) == "( )":
                sys.stdout.write("WARN: You shouldn't use CALL x ARGS (); to call a function that doesn't take an argument, use CALL x; instead.\n")
            if len(line.split(" ")) <= 3:
                exec(f'RETURN = {line.split(" ")[1]}{line.split(" ")[3].removesuffix(";")}', globals())
                if not globals()['RETURN']:
                    globals()['RETURN'] = "None"
            else:
                exec(f'RETURN = {line.split(" ")[1]}{" ".join(line.split(" ")[3:]).removesuffix(";")}', globals())
                if not globals()['RETURN']:
                    globals()['RETURN'] = "None"
        else:
            if isinstance(globals().get("".join(line.split(" ")[1]).removesuffix(";"), None), list):
                for i in globals().get("".join(line.split(" ")[1]).removesuffix(";"), None):
                    process(i)
            else:
                exec(f'RETURN = {"".join(line.split(" ")[1]).removesuffix(";")}()', globals())
    elif regex.match("SET .* TO .*;", line):
        if line.split(" ")[1] != 'RETURN' and not regex.match("__.*__", line.split(" ")[1]):
            exec(f'{line.split(" ")[1]} = {" ".join(line.split(" ")[3:]).removesuffix(";")}', globals())
        else:
            raise AccessError(line + ", You can't set PyAsm runtime variables.")
    elif regex.match("INCREMENT .* BY .*;", line):
        if line.split(" ")[-1].removesuffix(';').isnumeric():
            if not regex.match("__.*__", line.split(" ")[1]):
                globals()[line.split(" ")[1]] += int(line.split(" ")[-1].removesuffix(';'))
            else:
                raise AccessError("'" + line + "', You can't set PyAsm runtime variables.")
    elif regex.match("DECREMENT .* BY .*;", line):
        if line.split(" ")[-1].removesuffix(';').isnumeric():
            if not regex.match("__.*__", line.split(" ")[1]):
                globals()[line.split(" ")[1]] -= int(line.split(" ")[-1].removesuffix(';'))
            else:
                raise AccessError("'" + line + "', You can't set PyAsm runtime variables.")
    elif regex.match("DELETE VAR .*;", line):
        del globals()[line.split(" ")[2].removesuffix(";")]
    elif regex.match("DELETE FUNC .*;", line):
        del globals()[line.split(" ")[2].removesuffix(";")]
    elif regex.match("DEFINE FUNC .*;", line):
        if line.split(" ")[2].removesuffix(";") != 'RETURN' and not regex.match("__.*__", line.split(" ")[2].removesuffix(";")):
            __out_function__ = line.split(" ")[2].removesuffix(";")
            globals()[line.split(" ")[2].removesuffix(";")] = []
        else:
            raise AccessError("'" + line + "' You can't set PyAsm runtime variables.")
    elif regex.match("INCLUDE .*;", line):
        if regex.match("INCLUDE .* FROM .*;", line):
            exec(f'from {line.split(" ")[3].removesuffix(";")} import {line.split(" ")[1]}', globals())
        else:
            if os.path.exists(f'{line.split(" ")[1].removesuffix(";")}.pym'):
                __process_file__(f'{line.split(" ")[1].removesuffix(";")}.pym')
            else:
                exec(f'import {line.split(" ")[1].removesuffix(";")}', globals())
    elif regex.match("IF .*;", line):
        exec(f'__IF_RETURN__ = not not {" ".join(line.split(" ")[1:]).removesuffix(";")}', globals())
        if not __IF_RETURN__:
            __skip_until__ = "ELSE;"
    elif regex.match("WHILE .*;", line):
        globals()['__WHILE_STATEMENT__'] = " ".join(line.split(" ")[1:]).removesuffix(";")
        __in_while_loop__ = True
    elif line == "ELSE;":
        if __IF_RETURN__:
            __skip_until__ = "ENDIF;"
        else:
            __skip_until__ = ""
    elif __in_while_loop__ and line == "ENDWHILE;" and not ignore_while_loop:
        while eval(__WHILE_STATEMENT__):
            for l in __while_loop__:
                process(l, True)
        __in_while_loop__ = False
    elif line == __skip_until__:
        __skip_until__ = ""
    else:
        raise SyntaxError(line)

# check if a file is supplied
if len(sys.argv) < 2:
    while True:
        line = input(">> ")
        process(line)
else:
    # check format and execute each line
    __process_file__(sys.argv[1])
