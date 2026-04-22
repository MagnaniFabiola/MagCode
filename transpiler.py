#!/usr/bin/env python3
"""
MagCode to C Transpiler
Converts a MagCode (.txt) program into a C source file.

How to run:
    python transpiler.py programs/helloworld.txt output.c
    gcc output.c -o output
    ./output
"""

import sys
import re

STRING_SIZE = 1024

# Words that are reserved in C — rename MagCode variables that clash
C_RESERVED = {
    'char', 'int', 'float', 'double', 'long', 'short', 'void',
    'if', 'else', 'while', 'for', 'do', 'switch', 'case', 'break',
    'continue', 'return', 'struct', 'union', 'enum', 'typedef',
    'static', 'extern', 'const', 'auto', 'register', 'sizeof',
    'unsigned', 'signed', 'goto', 'default'
}

def safe_name(name):
    """If a variable name is a C keyword, append _var to avoid conflicts."""
    if name in C_RESERVED:
        return name + '_var'
    return name


# ── First pass: figure out the type of every variable ────────────────

def first_pass(lines):
    """
    Scan all lines once to build two things:
      types    — dict mapping each variable name to 'int' or 'str'
      numified — set of variables that the program converts with numify
    """
    types = {}
    numified = set()

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split(None, 1)
        cmd  = parts[0]
        rest = parts[1].strip() if len(parts) > 1 else ''

        if cmd == 'listen':
            varname = rest[:rest.index(' ')]
            types[varname] = 'str'

        elif cmd == 'numify':
            varname = rest.strip()
            numified.add(varname)
            types[varname] = 'int'

        elif cmd == 'hold':
            varname, expr = rest.split('=', 1)
            varname = varname.strip()
            expr    = expr.strip()
            if varname not in types:
                if expr.startswith('"'):
                    types[varname] = 'str'
                elif re.match(r'^\d+$', expr):
                    types[varname] = 'int'
                elif 'flip(' in expr:
                    types[varname] = 'str'
                else:
                    tokens = re.split(r'[\s\+\-\*\/\%\(\)]+', expr)
                    if any(types.get(t) == 'str' for t in tokens):
                        types[varname] = 'str'
                    else:
                        types[varname] = 'int'

    return types, numified


# ── Translate a MagCode condition into a C boolean expression ─────────

def translate_condition(cond, types):
    cond = cond.strip()

    # String equality / inequality — must use strcmp in C
    for op in ['==', '!=']:
        if op in cond:
            left, right = cond.split(op, 1)
            left  = left.strip()
            right = right.strip()
            if types.get(left) == 'str' or types.get(right) == 'str':
                ls = safe_name(left)
                rs = safe_name(right)
                return f'strcmp({ls}, {rs}) == 0' if op == '==' else f'strcmp({ls}, {rs}) != 0'

    # length(x)  →  (int)strlen(safe_x)
    cond = re.sub(
        r'\blength\((\w+)\)',
        lambda m: f'(int)strlen({safe_name(m.group(1))})',
        cond
    )

    # Replace every identifier that is a known variable with its safe C name
    def replace_var(m):
        name = m.group(0)
        return safe_name(name) if name in types else name

    cond = re.sub(r'\b([a-zA-Z_]\w*)\b', replace_var, cond)
    return cond


# ── Translate one hold expression into C statement(s) ─────────────────

def translate_hold(varname, expr, types):
    safe_var  = safe_name(varname)
    var_type  = types.get(varname, 'int')
    expr      = expr.strip()

    if var_type == 'str':
        if expr == '""':
            return [f'{safe_var}[0] = \'\\0\';']

        if expr.startswith('"') and expr.endswith('"'):
            return [f'strcpy({safe_var}, {expr});']

        if expr.startswith('flip(') and expr.endswith(')'):
            inner = safe_name(expr[5:-1])
            return [f'flip({inner}, {safe_var});']

        if '+' in expr:
            parts = [p.strip() for p in expr.split('+')]
            stmts = []
            first      = parts[0]
            safe_first = safe_name(first)
            if safe_first != safe_var:
                stmts.append(f'strcpy({safe_var}, {safe_first});')
            for p in parts[1:]:
                safe_p = p if p.startswith('"') else safe_name(p)
                stmts.append(
                    f'strncat({safe_var}, {safe_p}, '
                    f'sizeof({safe_var}) - strlen({safe_var}) - 1);'
                )
            return stmts

        return [f'strcpy({safe_var}, {safe_name(expr)});']

    else:
        # Numeric expression — replace length() and variable names
        expr = re.sub(
            r'\blength\((\w+)\)',
            lambda m: f'(int)strlen({safe_name(m.group(1))})',
            expr
        )
        def replace_var(m):
            name = m.group(0)
            return safe_name(name) if name in types else name
        expr = re.sub(r'\b([a-zA-Z_]\w*)\b', replace_var, expr)
        return [f'{safe_var} = {expr};']


# ── Second pass: generate the body of main() ─────────────────────────

def generate_body(lines, types, numified):
    output = []
    indent = 1

    def add(stmt):
        output.append('    ' * indent + stmt)

    for line in lines:
        stripped = line.strip()

        if not stripped:
            output.append('')
            continue

        if stripped.startswith('#'):
            add('// ' + stripped[1:].strip())
            continue

        parts = stripped.split(None, 1)
        cmd  = parts[0]
        rest = parts[1].strip() if len(parts) > 1 else ''

        # ── shout ────────────────────────────────────────────────────
        if cmd == 'shout':
            expr = rest.strip()

            if expr.startswith('"') and expr.endswith('"'):
                add(f'printf("{expr[1:-1]}\\n");')

            elif expr.startswith('flip(') and expr.endswith(')'):
                inner = safe_name(expr[5:-1])
                add(f'flip({inner}, _tmp);')
                add(f'printf("%s\\n", _tmp);')

            elif expr.startswith('length(') and expr.endswith(')'):
                inner = safe_name(expr[7:-1])
                add(f'printf("%d\\n", (int)strlen({inner}));')

            elif types.get(expr) == 'int':
                add(f'printf("%d\\n", {safe_name(expr)});')

            else:
                add(f'printf("%s\\n", {safe_name(expr)});')

        # ── listen ───────────────────────────────────────────────────
        elif cmd == 'listen':
            space   = rest.index(' ')
            varname = rest[:space]
            prompt  = rest[space + 1:].strip()
            prompt_text = prompt[1:-1] if prompt.startswith('"') else prompt
            safe_var    = safe_name(varname)

            if varname in numified:
                buf = safe_var + '_buf'
                add(f'printf("{prompt_text}");')
                add(f'fgets({buf}, sizeof({buf}), stdin);')
                add(f'{buf}[strcspn({buf}, "\\n")] = 0;')
            else:
                add(f'printf("{prompt_text}");')
                add(f'fgets({safe_var}, sizeof({safe_var}), stdin);')
                add(f'{safe_var}[strcspn({safe_var}, "\\n")] = 0;')

        # ── numify ───────────────────────────────────────────────────
        elif cmd == 'numify':
            varname  = rest.strip()
            safe_var = safe_name(varname)
            buf      = safe_var + '_buf'
            add(f'{safe_var} = atoi({buf});')

        # ── hold ─────────────────────────────────────────────────────
        elif cmd == 'hold':
            varname, expr = rest.split('=', 1)
            for stmt in translate_hold(varname.strip(), expr, types):
                add(stmt)

        # ── vibe (if) ────────────────────────────────────────────────
        elif cmd == 'vibe':
            cond = translate_condition(rest, types)
            add(f'if ({cond}) {{')
            indent += 1

        # ── nah (else) ───────────────────────────────────────────────
        elif cmd == 'nah':
            indent -= 1
            add('} else {')
            indent += 1

        # ── periodt (closing brace) ──────────────────────────────────
        elif cmd == 'periodt':
            indent -= 1
            add('}')

        # ── yap (while) ──────────────────────────────────────────────
        elif cmd == 'yap':
            cond = translate_condition(rest, types)
            add(f'while ({cond}) {{')
            indent += 1

    return output


# ── Build variable declarations for the top of main() ────────────────

def declare_variables(types, numified):
    decls = []
    for var in sorted(types.keys()):
        safe_var = safe_name(var)
        if types[var] == 'str':
            decls.append(f'    char {safe_var}[{STRING_SIZE}] = "";')
        else:
            decls.append(f'    int {safe_var} = 0;')
        if var in numified:
            decls.append(f'    char {safe_var}_buf[{STRING_SIZE}] = "";')
    return decls


# ── The fixed C header that every output file starts with ────────────

C_HEADER = """\
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Reverses src into dst — used by the flip() built-in */
void flip(char *src, char *dst) {
    int len = (int)strlen(src);
    int i;
    for (i = 0; i < len; i++) {
        dst[i] = src[len - 1 - i];
    }
    dst[len] = '\\0';
}

int main() {
    char _tmp[1024] = "";   /* scratch buffer for flip() inside shout */\
"""


# ── Main transpile function ───────────────────────────────────────────

def transpile(src_file, out_file):
    try:
        with open(src_file) as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: '{src_file}' not found.")
        sys.exit(1)

    types, numified = first_pass(lines)
    decls           = declare_variables(types, numified)
    body            = generate_body(lines, types, numified)

    parts = [C_HEADER]
    if decls:
        parts.append('')
        parts += decls
    parts.append('')
    parts += body
    parts += ['', '    return 0;', '}', '']

    output = '\n'.join(parts)

    if out_file:
        with open(out_file, 'w') as f:
            f.write(output)
        print(f"Transpiled  →  {out_file}")
        print(f"Compile     →  gcc {out_file} -o output")
        print(f"Run         →  ./output")
    else:
        print(output)


# ── Entry point ───────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python transpiler.py <program.txt> [output.c]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) >= 3 else None
    transpile(sys.argv[1], out)
