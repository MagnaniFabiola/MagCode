#!/usr/bin/env python3
"""
MagCode Interpreter
A programming language created by Magnani.

Keywords : shout, listen, hold, numify, vibe, nah, periodt, yap
Built-in : flip(x)  ->  reverses a string

"""

import sys


# ── Built-in functions available in MagCode programs ─────────────────
def flip(x):
    x = str(x)
    result = ""
    i = len(x) - 1
    while i >= 0:
        result = result + x[i]
        i = i - 1
    return result

def length(x):
    return len(str(x))


# ── Evaluate an expression and return its value ──────────────────────
def evaluate(expr, variables):
    expr = expr.strip()

    # Plain string literal  e.g.  "Hello!"
    if expr.startswith('"') and expr.endswith('"'):
        return expr[1:-1]

    # Build the environment that eval() can use
    env = dict(variables)
    env['flip']   = flip
    env['length'] = length

    try:
        return eval(expr, {"__builtins__": {}}, env)
    except Exception:
        return expr   # return as-is if we can't evaluate it


# ── Find the 'nah' that belongs to a 'vibe' block ────────────────────
def find_nah(lines, start):
    depth = 0
    for i in range(start + 1, len(lines)):
        line = lines[i].strip()
        if not line or line.startswith('#'):
            continue
        cmd = line.split()[0]
        if cmd in ('vibe', 'yap'):
            depth += 1
        elif cmd == 'periodt':
            if depth == 0:
                return None   # hit periodt before nah
            depth -= 1
        elif cmd == 'nah' and depth == 0:
            return i
    return None


# ── Find the matching 'periodt' that closes a block ──────────────────
def find_periodt(lines, start):
    depth = 0
    for i in range(start + 1, len(lines)):
        line = lines[i].strip()
        if not line or line.startswith('#'):
            continue
        cmd = line.split()[0]
        if cmd in ('vibe', 'yap'):
            depth += 1
        elif cmd == 'periodt':
            if depth == 0:
                return i
            depth -= 1
    return len(lines) - 1


# ── Run lines from index 'start' up to (not including) 'stop' ────────
def execute(lines, variables, start, stop):
    i = start
    while i < stop:
        line = lines[i].strip()

        # Skip blank lines and comments
        if not line or line.startswith('#'):
            i += 1
            continue

        parts = line.split(None, 1)           # split on first space only
        cmd   = parts[0]
        rest  = parts[1].strip() if len(parts) > 1 else ''

        # shout <expr>  →  print something
        if cmd == 'shout':
            print(evaluate(rest, variables))

        # listen <varname> <prompt>  →  get user input
        elif cmd == 'listen':
            space   = rest.index(' ')
            varname = rest[:space]
            prompt  = evaluate(rest[space + 1:].strip(), variables)
            variables[varname] = input(prompt)

        # hold <varname> = <expr>  →  store a value
        elif cmd == 'hold':
            varname, expr = rest.split('=', 1)
            variables[varname.strip()] = evaluate(expr.strip(), variables)

        # numify <varname>  →  convert variable to a real number
        #elif cmd == 'numify':
          #  variables[rest] = int(str(variables[rest]).strip())
        elif cmd == 'numify':
            try:
                variables[rest] = int(str(variables[rest]).strip())
                variables['numify_failed'] = 0
            except:
                variables[rest] = 0
                variables['numify_failed'] = 1

        # vibe <condition>  →  if statement
        elif cmd == 'vibe':
            nah_i     = find_nah(lines, i)
            periodt_i = find_periodt(lines, i)

            if evaluate(rest, variables):
                execute(lines, variables, i + 1, nah_i if nah_i is not None else periodt_i)
            elif nah_i is not None:
                execute(lines, variables, nah_i + 1, periodt_i)

            i = periodt_i + 1
            continue

        # yap <condition>  →  while loop (keeps yapping until false)
        elif cmd == 'yap':
            periodt_i = find_periodt(lines, i)

            while evaluate(rest, variables):
                execute(lines, variables, i + 1, periodt_i)

            i = periodt_i + 1
            continue

        # nah / periodt are handled above, skip if hit alone
        elif cmd in ('nah', 'periodt'):
            pass

        else:
            print(f"MagCode Error: Unknown command '{cmd}' on line {i + 1}")

        i += 1


# ── Entry point ───────────────────────────────────────────────────────
def run(filename):
    try:
        with open(filename) as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"MagCode Error: File '{filename}' not found")
        sys.exit(1)

    variables = {}
    execute(lines, variables, 0, len(lines))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python magcode.py <program.txt>")
        sys.exit(1)
    run(sys.argv[1])
