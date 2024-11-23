# Notes on _Crafting Interpreters_

These are the Lox programs to aim for:

- For, while, if/else, arithmetic, printing
- Multiple handwritten tests
- Function
- Reach: Luhn checksum
- Graph DFS, recursion
- Arrays

Resources on machine learning domain-specific languages from my advisor:

Halide, EDSLs (Embedded DSLs). Check out conferences rather than papers: ASPLOS,
NeurIPS, PLDI, OOPSLA, conferences on fuctional programming languages. ML
languages are named differently from just "ML languages": check out languages
for accelerators/NLP/vision, domains

The Triton language is worth checking out.

Read Bril, on embedded DSLs, by Adrian Sampson. Check out all the practical work
done with EDSLs.

The recommended text on programming languages is _Modern Compiler
Implementation_. From digging online, it seems the book's ML version is
canonical and the Java and C versions are ports.

## Chapter 4: Scanning

Each individually meaningfully "blob" of characters is a _lexeme_. For example,
in the line

```js
var language = "lox";
```

the lexemes are `var`, `language`, `=`, `"lox"` and `;`.

---

**Line information in tokens for error reporting**

Tokens need to store information about the position of the lexeme in the source
code to display to the user when there's a syntax error. The straightforward way
to do this is to store the line the token appears on (this is what the book
does), and maybe also the column and the token's length.

But a more involved way to do this is to store just the token's offset from the
beginning of the source file to the beginning of the lexeme, and the lexeme's
length. The scanner needs to know these anyway, so it incurs no overhead in
computing them. Then, when an error needs to be reported, the interpreter counts
the number of newlines preceding that stored location. This is linear-time
search (though you could store a list of the newline positions, and
binary-search over them, making having log-runtime but additional linear
memory). This _sounds_ slow, but you only rarely report errors. The
zero-computational-overhead in storing location could win out, amortized.

---

**What the scanner does, in Nystromic vividness**

> The core of the scanner is a loop. Starting at the first character of the
> source code, the scanner figures out what lexeme the character belongs to, and
> consumes it and any following characters that are part of that lexeme. When it
> reaches the end of that lexeme, it emits a token.
>
> Then it loops back and does it again, starting from the very next character in
> the source code. It keeps doing that, eating characters and occasionally, uh,
> excreting tokens, until it reaches the end of the input.

---

**Regex and lexical grammars**

Regexing during the scanning process seems to have surprising theoretical CS
depth:

> The rules that determine how a particular language groups characters into
> lexemes are called its **lexical grammar**. In Lox, as in most programming
> languages, the rules of that grammar are simple enough for the language to be
> classified a [**regular
> language**](https://en.wikipedia.org/wiki/Regular_language). That’s the same
> “regular” as in regular expressions.
>
> It pains me to gloss over the theory so much, especially when it’s as
> interesting as I think the [Chomsky
> hierarchy](https://en.wikipedia.org/wiki/Chomsky_hierarchy) and [finite-state
> machines](https://en.wikipedia.org/wiki/Finite-state_machine) are. But the
> honest truth is other books cover this better than I could. [_Compilers:
> Principles, Techniques, and
> Tools_](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools)
> (universally known as “the dragon book”) is the canonical reference.

You can use tools like
[Lex](http://dinosaur.compilertools.net/lex/) or [Flex](https://github.com/westes/flex)
to get a complete scanner out of a handful of defined regexes.

I need to chase down these rabbit holes at some point.

---

**Peeking lookahead**

An interesting design choice:

> I could have made `peek()` take a parameter for the number of characters ahead
> to look instead of defining two functions, but that would allow *arbitrarily*
> far lookahead. Providing these two functions makes it clearer to a reader of
> the code that our scanner looks ahead at most two characters.

---

**Newlines vs ;**

How Python handles newlines is interesting:

> [Python](https://docs.python.org/3.5/reference/lexical_analysis.html#implicit-line-joining) treats
> all newlines as significant unless an explicit backslash is used at the end of
> a line to continue it to the next line. However, newlines anywhere inside a
> pair of brackets (`()`, `[]`, or `{}`) are ignored. Idiomatic style strongly
> prefers the latter.

## Chapter 5: Representing Code

Quite funny:

> People have been trying to crystallize grammar all the way back to
> Pāṇini's *Ashtadhyayi*, which codified Sanskrit grammar a mere couple thousand
> years ago. Not much progress happened until John Backus and company needed a
> notation for specifying ALGOL 58 and came up with [**Backus-Naur
> form**](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form) (**BNF**).
