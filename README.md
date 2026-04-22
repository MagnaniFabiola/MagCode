# MagCode

MagCode is a programming language I built from scratch in Python. It has 8 keywords, 2 built-in functions, and a transpiler that converts MagCode programs into C code.

You need Python 3 to run it. No extra libraries needed.

```bash
python3 magcode.py programs/helloworld.txt
```

---

## Keywords

| Keyword | What it does | Example |
|---|---|---|
| `shout` | prints to screen | `shout "hello"` |
| `listen` | reads user input | `listen name "Your name? "` |
| `hold` | stores a variable | `hold x = 5` |
| `numify` | converts a string to an integer | `numify x` |
| `vibe` | if statement | `vibe x > 0` |
| `nah` | else | `nah` |
| `periodt` | closes a vibe or yap block | `periodt` |
| `yap` | while loop | `yap i < 5` |

## Built-ins

| Function | What it does |
|---|---|
| `flip(x)` | reverses a string — `flip("hello")` gives `"olleh"` |
| `length(x)` | returns the length — `length("hi")` gives `2` |

Math operators: `+` `-` `*` `/` `%`  
Comparison: `==` `!=` `<` `>` `<=` `>=`  
Comments: any line starting with `#`

---

## Examples

**Print something**
```
shout "Hello, World!"
```

**Store and use a variable**
```
hold name = "Fabiola"
shout name
```

**Get input from the user**
```
listen name "What is your name? "
shout name
```

**If / else**
```
listen n "Enter a number: "
numify n
vibe n > 0
  shout "positive"
nah
  shout "not positive"
periodt
```

**While loop**
```
hold i = 0
yap i < 5
  shout i
  hold i = i + 1
periodt
```

**Reverse a string**
```
listen word "Enter a word: "
shout flip(word)
```

---

## Programs

| File | What it does |
|---|---|
| `programs/helloworld.txt` | Hello World |
| `programs/cat.txt` | reads input and prints it back |
| `programs/is_even.txt` | checks if a number is even or odd |
| `programs/multiply.txt` | multiplies two single-digit numbers |
| `programs/reverse_string.txt` | reverses a string |
| `programs/is_palindrome.txt` | checks if a string is a palindrome |
| `programs/repeater.txt` | repeats a character N times |

---

## Transpiler

`transpiler.py` takes a MagCode file and outputs valid C code that you can compile with `gcc`.

```bash
python3 transpiler.py programs/helloworld.txt output.c
gcc output.c -o output
./output
```

It works in two passes. The first pass figures out the type of every variable (string or int) since C needs that before anything is declared. The second pass goes line by line and converts each keyword into the equivalent C code — `shout` becomes `printf`, `listen` becomes `fgets`, `vibe` becomes `if`, `yap` becomes `while`, and so on.

A few things it handles automatically:
- string comparisons with `==` get converted to `strcmp()` since C can't compare strings with `==` directly
- variables named after C reserved words like `char` get renamed to `char_var`
- the `flip()` built-in gets compiled as a real C function at the top of the output file
