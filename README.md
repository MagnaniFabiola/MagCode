# MagCode 

A custom programming language created by **Magnani**.  

## How to Run

```bash
python magcode.py programs/helloworld.txt
```

**Requirement:** Python 3.x — check with `python --version`

---

## MagCode Keywords (8 total)

| Keyword    | What it does                              | Example |
|------------|-------------------------------------------|---------|
| `shout`    | Print something to the screen             | `shout "Hello!"` |
| `listen`   | Get input from the user                   | `listen name "Your name? "` |
| `hold`     | Store a value in a variable               | `hold x = 5` |
| `numify`   | Convert a variable to a real number       | `numify x` |
| `vibe`     | If statement                              | `vibe x > 0` |
| `nah`      | Else (the other option)                   | `nah` |
| `periodt`  | End a `vibe` or `yap` block               | `periodt` |
| `yap`      | While loop (keeps going until false)      | `yap i < 5` |

### Built-in Functions

| Function     | What it does                  | Example                       |
|--------------|-------------------------------|-------------------------------|
| `flip(x)`    | Reverses a string             | `flip("hello")` → `"olleh"`   |
| `length(x)`  | Returns the length of a string | `length("hi")` → `2`         |

### Operators

| Type       | Operators |
|------------|-----------|
| Math       | `+`  `-`  `*`  `/`  `%` |
| Compare    | `==`  `!=`  `<`  `>`  `<=`  `>=` |

### Comments

Any line starting with `#` is ignored.

---

## Syntax Guide

### Print something
```
shout "Hello, World!"
```

### Store a variable
```
hold name = "Fabiola"
shout name
```

### Get user input
```
listen name "What is your name? "
shout name
```

### If / Else
```
listen n "Enter a number: "
numify n
vibe n > 0
  shout "Positive bestie"
nah
  shout "Not positive no cap"
periodt
```

### While Loop
```
hold i = 0
yap i < 5
  shout i
  hold i = i + 1
periodt
```

### Reverse a string
```
listen word "Enter a word: "
shout flip(word)
```

---

## Example Programs

| File | Description |
|------|-------------|
| `programs/helloworld.txt`     | Prints "Hello, World!" |
| `programs/cat.txt`            | Listens and shouts back what you typed |
| `programs/multiply.txt`       | Multiplies two single-digit numbers |
| `programs/repeater.txt`       | Repeats a character N times |
| `programs/reverse_string.txt` | Reverses a user-entered string |
| `programs/is_palindrome.txt`  | Checks if a string is a palindrome |
| `programs/is_even.txt`        | Checks if a number is even or odd |

---

## MagCode to C Transpiler

`transpiler.py` converts any MagCode program into a valid C source file.  
The generated C code can then be compiled with `gcc` into a native executable.

### How to transpile

```bash
python3 transpiler.py programs/helloworld.txt output.c
gcc output.c -o output
./output
```

### Transpiling all example programs

```bash
# Hello World
python3 transpiler.py programs/helloworld.txt helloworld.c
gcc helloworld.c -o helloworld && ./helloworld

# Cat
python3 transpiler.py programs/cat.txt cat.c
gcc cat.c -o cat && ./cat

# Multiply
python3 transpiler.py programs/multiply.txt multiply.c
gcc multiply.c -o multiply && ./multiply

# Repeater
python3 transpiler.py programs/repeater.txt repeater.c
gcc repeater.c -o repeater && ./repeater

# Reverse String
python3 transpiler.py programs/reverse_string.txt reverse_string.c
gcc reverse_string.c -o reverse_string && ./reverse_string

# Is Palindrome
python3 transpiler.py programs/is_palindrome.txt is_palindrome.c
gcc is_palindrome.c -o is_palindrome && ./is_palindrome

# Is Even
python3 transpiler.py programs/is_even.txt is_even.c
gcc is_even.c -o is_even && ./is_even
```

### How the transpiler works

The transpiler runs in two passes over the MagCode source file:

1. **First pass** (`first_pass`) — scans every line to determine the type (`int` or `str`) of each variable and which variables are converted with `numify`.
2. **Second pass** (`generate_body`) — translates each MagCode keyword into the equivalent C code.

### MagCode → C translation reference

| MagCode | Generated C |
|---|---|
| `shout "Hello"` | `printf("Hello\n");` |
| `shout var` (string) | `printf("%s\n", var);` |
| `shout var` (int) | `printf("%d\n", var);` |
| `listen var "prompt"` | `printf("prompt"); fgets(var, ...); ...` |
| `numify var` | `var = atoi(var_buf);` |
| `hold x = ""` | `x[0] = '\0';` |
| `hold x = a + b` (strings) | `strncat(x, b, ...);` |
| `hold x = a * b` (ints) | `x = a * b;` |
| `hold rev = flip(word)` | `flip(word, rev);` |
| `vibe` / `nah` / `periodt` | `if (...) {` / `} else {` / `}` |
| `yap` / `periodt` | `while (...) {` / `}` |

### Notes

- MagCode variables that clash with C reserved words (e.g. `char`) are automatically renamed (e.g. `char_var`).
- String variables are declared as `char name[1024]`.
- Numified variables use a `_buf` helper for reading input: `fgets` → `atoi`.
- The `flip()` built-in is compiled as a helper C function included at the top of every output file.
- Requires `gcc` to compile the generated C file.
