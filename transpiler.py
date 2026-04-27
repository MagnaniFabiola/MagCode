#!/usr/bin/env python3
"""
MagCode - C Transpiler
Reads a MagCode (.txt) program and converts it into a valid C source file.

MagCode keyword  -  C equivalent
─────────────────────────────────
shout            -  printf()
listen           -  printf() + fgets()
hold             -  assignment (= / strcpy / strncat)
numify           -  atoi()
vibe             -  if
nah              -  else
periodt          -  } (closing brace)
yap              -  while
length(x)        -  strlen(x)

How to use:
    python3 transpiler.py programs/helloworld.txt output.c
    gcc output.c -o output
    ./output
"""

import sys  # gives us access to command-line arguments (sys.argv) and sys.exit()
import re   # regular expressions — used to find and replace patterns in strings

# C keywords that cannot be used as variable names — if a MagCode variable
# uses one of these names, we rename it by adding _var (e.g. char → char_var)
C_RESERVED = {
    'char', 'int', 'float', 'double', 'long', 'short', 'void',
    'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'break',
    'continue', 'return', 'struct', 'union', 'enum', 'typedef',
    'static', 'extern', 'const', 'auto', 'register', 'sizeof',
    'unsigned', 'signed', 'goto', 'default'
}

def safe_name(name):
    # if the variable name is a C keyword, add _var to the end to avoid conflicts
    return name + '_var' if name in C_RESERVED else name


def translate_condition(cond, types):
    # translate a MagCode condition into a valid C boolean expression
    cond = cond.strip()
    # MagCode uses Python-style 'and'/'or' — replace with C's && and ||
    cond = re.sub(r'\band\b', '&&', cond)
    cond = re.sub(r'\bor\b',  '||', cond)

    # string equality/inequality — C can't use == on strings, must use strcmp
    for op in ['==', '!=']:
        if op in cond:
            left, right = cond.split(op, 1)
            left  = left.strip()
            right = right.strip()
            if types.get(left) == 'str' or types.get(right) == 'str':
                ls = safe_name(left)
                rs = safe_name(right)
                # strcmp returns 0 when equal, so wrap accordingly
                return f'strcmp({ls}, {rs}) == 0' if op == '==' else f'strcmp({ls}, {rs}) != 0'

    # replace length(x) with (int)strlen(safe_name(x))
    cond = re.sub(
        r'\blength\((\w+)\)',
        lambda m: f'(int)strlen({safe_name(m.group(1))})',
        cond
    )
    # rename every known variable to its safe C name
    cond = re.sub(
        r'\b([a-zA-Z_]\w*)\b',
        lambda m: safe_name(m.group(0)) if m.group(0) in types else m.group(0),
        cond
    )
    return cond


C_HEADER = """\
#include <stdio.h>    // printf, fgets
#include <string.h>   // string length, copy, compare
#include <stdlib.h>   // convert string to integer (atoi)

int main() {"""


def first_pass(lines):
    types    = {}   # will hold { 'varname': 'int' } or { 'varname': 'str' }
    numified = set()  # names of variables that go through numify (need a _buf in C)

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):  # skip blanks and comments
            continue

        parts = stripped.split(None, 1)   # split keyword from the rest
        cmd  = parts[0]
        rest = parts[1].strip() if len(parts) > 1 else ''

        if cmd == 'hold':                          # hold is the only assignment command
            varname, expr = rest.split('=', 1)     # split on '=' to get name and value
            varname = varname.strip()
            expr    = expr.strip()
            if varname not in types:               # only set type if we haven't seen it yet
                if expr.startswith('"'):           # value starts with quote → it's a string
                    types[varname] = 'str'
                else:                              # otherwise assume integer
                    types[varname] = 'int'

        elif cmd == 'listen':                      # listen always reads a string from the user
            varname = rest.split()[0]              # variable name is the first word after listen
            types[varname] = 'str'

        elif cmd == 'numify':                      # numify converts a variable to int
            varname = rest.strip()
            numified.add(varname)                  # remember it needs a _buf declared
            types[varname] = 'int'                 # after numify the variable becomes an int
            types['numify_failed'] = 'int'         # auto-declare the error flag variable

    return types, numified  # return both the type map and the numified set



def declare_variables(types, numified):
    decls = []
    for var in sorted(types.keys()):   # sorted so the output is alphabetical and consistent
        sv = safe_name(var)            # get the C-safe version of the name
        if types[var] == 'str':
            decls.append(f'    char {sv}[1024] = "";')    # strings are char arrays in C
        else:
            decls.append(f'    int {sv} = 0;')             # integers start at 0
        if var in numified:
            decls.append(f'    char {sv}_buf[1024] = "";') # buffer to hold raw input before atoi
    return decls


def transpile(src_file, out_file):
    try:
        with open(src_file) as f:
            lines = f.readlines()  # read every line into a list of strings
    except FileNotFoundError:
        print(f"Error: '{src_file}' not found.")  # friendly message if the file doesn't exist
        sys.exit(1)                                # stop the program with error code 1

    types, numified = first_pass(lines)          # scan all lines to learn every variable's type
    decls = declare_variables(types, numified)    # build the C declaration lines from that info

    # Build the output as a list of strings, then join them at the end
    parts = []
    parts.append(C_HEADER)        # start with the fixed C header
    if decls:
        parts.append('')           # blank line between header and declarations
        parts += decls             # add all variable declarations e.g. int x = 0;
    parts.append('')               # blank line before the body

    indent = 1  # start at 1 because we are already inside main() { }

    def add(stmt):
        # helper that adds a line with the correct number of spaces in front
        parts.append('    ' * indent + stmt)  # 4 spaces per indent level

    for line in lines:
        stripped = line.strip()    # remove leading/trailing whitespace and the \n at the end

        if not stripped:           # blank line → skip it
            continue
        if stripped.startswith('#'):  # MagCode comment → skip it
            continue

        parts_line = stripped.split(None, 1)  # split on first space: ['shout', '"Hello!"']
        cmd  = parts_line[0]                  # the keyword e.g. 'shout'
        rest = parts_line[1] if len(parts_line) > 1 else ''  # everything after the keyword

        if cmd == 'shout':                         # shout → printf
            expr = rest.strip()                    # what we want to print
            if expr.startswith('"') and expr.endswith('"'):   # it's a string literal like "Hello!"
                text = expr[1:-1]                  # strip the outer quotes: Hello!
                add(f'printf("{text}\\n");')     # printf("Hello!\n");
            elif types.get(expr) == 'int':         # integer variable
                add(f'printf("%d\\n", {safe_name(expr)});')
            else:                                  # string variable
                add(f'printf("%s\\n", {safe_name(expr)});')

        elif cmd == 'hold':                        # hold → C assignment
            varname, expr = rest.split('=', 1)     # split on '=' to get name and value
            varname = varname.strip()
            expr    = expr.strip()
            sv      = safe_name(varname)           # C-safe version of the variable name
            if types.get(varname) == 'int':        # integer assignment
                # also replace length(x) with strlen(x) inside numeric expressions
                expr = re.sub(
                    r'\blength\((\w+)\)',
                    lambda m: f'(int)strlen({safe_name(m.group(1))})',
                    expr
                )
                # rename known variables to safe C names in the expression
                expr = re.sub(
                    r'\b([a-zA-Z_]\w*)\b',
                    lambda m: safe_name(m.group(0)) if m.group(0) in types else m.group(0),
                    expr
                )
                add(f'{sv} = {expr};')             # e.g. x = 5;

            elif types.get(varname) == 'str':      # string assignment
                if expr == '""':                   # assigning empty string
                    add(f'{sv}[0] = \'\\0\';')    # set first char to null terminator
                elif expr.startswith('"'):         # assigning a string literal e.g. "hello"
                    add(f'strcpy({sv}, {expr});')  # strcpy copies the string in
                elif '+' in expr:                  # string concatenation e.g. result + char
                    pieces = [p.strip() for p in expr.split('+')]  # split into parts
                    first  = safe_name(pieces[0])  # safe name for the first piece
                    if first != sv:                # only strcpy if source != destination
                        add(f'strcpy({sv}, {first});')
                    for p in pieces[1:]:           # append each remaining piece
                        if p.startswith('"'):
                            src = p               # string literal — use as-is
                        elif '[' in p:            # e.g. word[i] — single character access
                            # in C, word[i] is a char not a string, so wrap it in a 2-char array
                            add(f'{{ char _ch[2]; _ch[0] = {p}; _ch[1] = \'\\0\'; strncat({sv}, _ch, sizeof({sv}) - strlen({sv}) - 1); }}')
                            continue
                        else:
                            src = safe_name(p)    # another string variable
                        add(f'strncat({sv}, {src}, sizeof({sv}) - strlen({sv}) - 1);')
                else:                              # copying from another string variable
                    add(f'strcpy({sv}, {safe_name(expr)});')

        elif cmd == 'listen':                      # listen → printf prompt + fgets input
            space   = rest.index(' ')              # find where the variable name ends
            varname = rest[:space]                 # everything before that space is the name
            sv      = safe_name(varname)           # C-safe version
            prompt  = rest[space + 1:].strip()     # everything after is the prompt string
            prompt_text = prompt[1:-1]             # strip the quotes from the prompt
            if varname in numified:                # if this var will be numified, read into _buf
                buf = sv + '_buf'
                add(f'printf("{prompt_text}");')           # show the prompt
                add(f'fgets({buf}, sizeof({buf}), stdin);') # read into buffer
                add(f'{buf}[strcspn({buf}, "\\n")] = 0;')  # strip the newline
            else:                                  # regular string — read directly into the var
                add(f'printf("{prompt_text}");')
                add(f'fgets({sv}, sizeof({sv}), stdin);')
                add(f'{sv}[strcspn({sv}, "\\n")] = 0;')

        elif cmd == 'numify':                      # numify → atoi converts the buffer string to int
            varname = rest.strip()
            sv      = safe_name(varname)
            buf     = sv + '_buf'
            add(f'{sv} = atoi({buf});')            # atoi("42") → 42
            # set numify_failed: 1 if input wasn't a valid number, 0 if it was
            add(f'numify_failed = ({sv} == 0 && {buf}[0] != \'0\') ? 1 : 0;')

        elif cmd == 'vibe':                        # vibe → if statement
            cond = translate_condition(rest, types)  # translate condition to valid C
            add(f'if ({cond}) {{')                 # e.g. if (n % 2 == 0) {
            indent += 1                            # increase indent — we're now inside the if block

        elif cmd == 'nah':                         # nah → else
            indent -= 1                            # close the if block first
            add('} else {')                        # write the else
            indent += 1                            # increase indent for the else body

        elif cmd == 'periodt':                     # periodt → closing brace
            indent -= 1                            # decrease indent before writing the brace
            add('}')                               # close the block

        elif cmd == 'yap':                         # yap → while loop
            cond = translate_condition(rest, types)  # translate condition to valid C
            add(f'while ({cond}) {{')              # e.g. while (i < 10) {
            indent += 1                            # increase indent — we're inside the loop

    parts.append('    return 0;')  # close main() with return 0
    parts.append('}')              # closing brace of main()
    parts.append('')               # trailing newline at end of file

    output = '\n'.join(parts)      # join every piece with a newline between them

    if out_file:                               # if the user gave us an output filename
        with open(out_file, 'w') as f:
            f.write(output)                    # write the C code to that file
        print(f"Transpiled  →  {out_file}")
        print(f"Compile     →  gcc {out_file} -o output")
        print(f"Run         →  ./output")
    else:
        print(output)                          # no output file → just print to terminal


if __name__ == '__main__':
    if len(sys.argv) < 2:  # need at least the source file
        print("Usage: python transpiler.py <program.txt> [output.c]")
        sys.exit(1)

    out = sys.argv[2] if len(sys.argv) >= 3 else None  # output file is optional
    transpile(sys.argv[1], out)  # kick off with the filename the user provided
