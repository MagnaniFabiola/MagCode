# MagCode

MagCode is a programming language I built from scratch in Python. It has 8 keywords, 1 built-in function, and a transpiler that converts MagCode programs into C code.

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
hold result = ""
hold i = length(word) - 1
yap i >= 0
  hold result = result + word[i]
  hold i = i - 1
periodt
shout result
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

I built a transpiler (`transpiler.py`) that takes any MagCode `.txt` file and converts it into a C file you can compile with `gcc`. I wrote it by hand in Python — no external tools like Lex or ANTLR.

To run it:

```bash
python3 transpiler.py programs/helloworld.txt output.c
gcc output.c -o output
./output
```

If you skip the output file it just prints the C code to the terminal so you can preview it:

```bash
python3 transpiler.py programs/helloworld.txt
```

---

### How I built it — two passes

The big challenge was that C needs every variable declared with its type (`int` or `char[]`) at the top of `main()` before any code runs. MagCode doesn't have type declarations so I had to figure that out myself.

**Pass 1 — figure out variable types**

I scan through all the lines first just to collect types, before generating any C. The rules I used:

- `listen x` -> `x` is a string (input is always text)
- `numify x` -> `x` becomes an `int`
- `hold x = "..."`  ->`x` is a string (starts with a quote)
- `hold x = 5` -> `x` is an `int`

**Pass 2 — translate each line**

I loop through every line and use `if/elif` to match the keyword and output the right C code.

---

### What each keyword turns into

| MagCode | C output | Notes |
|---|---|---|
| `shout "Hello!"` | `printf("Hello!\n");` | string literal |
| `shout x` | `printf("%s\n", x);` or `printf("%d\n", x);` | depends on type of `x` |
| `listen x "prompt"` | `printf("prompt"); fgets(x, sizeof(x), stdin);` | reads into a `char[]` |
| `hold x = 5` | `x = 5;` | integer assignment |
| `hold x = "hi"` | `strcpy(x, "hi");` | can't use `=` on strings in C |
| `hold x = a + b` | `strncat(x, b, sizeof(x) - strlen(x) - 1);` | safe concatenation |
| `numify x` | `x = atoi(x_buf);` | converts input buffer to int |
| `vibe x > 0` | `if (x > 0) {` | if block |
| `nah` | `} else {` | else |
| `periodt` | `}` | closes the block |
| `yap i < 5` | `while (i < 5) {` | while loop |
| `length(x)` | `(int)strlen(x)` | string length |

---

### Things I had to handle specially

**String comparison** — you can't use `==` on strings in C, you have to use `strcmp`. So `vibe word == rev` becomes:
```c
if (strcmp(word, rev) == 0) {
```

**C keyword conflicts** — one of my example programs uses a variable called `char`, which is a reserved word in C. I handle this by renaming it to `char_var` automatically:
```c
char char_var[1024] = "";
```

**`numify` needs a buffer** — C can't read input directly into an `int`. I declare a temporary `char[]` buffer, read into that with `fgets`, then convert with `atoi`:
```c
char n_buf[1024] = "";
int  n = 0;
fgets(n_buf, sizeof(n_buf), stdin);
n = atoi(n_buf);
numify_failed = (n == 0 && n_buf[0] != '0') ? 1 : 0;
```

**`and` / `or`** — MagCode uses Python-style operators so I replace them before generating C:
- `and` → `&&`
- `or` → `||`

**Character indexing** — `word[i]` gives you a single `char` in C, not a string. When it shows up in a concatenation like `hold rev = rev + word[i]`, I wrap it in a 2-char array so `strncat` works:
```c
{ char _ch[2]; _ch[0] = word[i]; _ch[1] = '\0'; strncat(rev, _ch, sizeof(rev) - strlen(rev) - 1); }
```

---

### Every generated file starts with

```c
#include <stdio.h>    // printf, fgets
#include <string.h>   // strlen, strcpy, strcmp, strncat
#include <stdlib.h>   // atoi
```
