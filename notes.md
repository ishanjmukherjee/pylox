# Notes on _Crafting Interpreters_

These are the Lox programs to aim for:

- For, while, if/else, arithmetic, printing
- Multiple handwritten tests
- Function
- Reach: Luhn checksum
- Graph DFS, recursion
- Arrays

Resources on machine learning domain-specific languages from my advisor:

- Halide, EDSLs (Embedded DSLs). Check out conferences rather than papers:
ASPLOS, NeurIPS, PLDI, OOPSLA, conferences on fuctional programming languages.
ML languages are named differently from just "ML languages": check out languages
for accelerators/NLP/vision, domains
- The Triton language is worth checking out.
- Read Bril, on embedded DSLs, by Adrian Sampson. Check out all the practical
work done with EDSLs.
- The recommended text on programming languages is _Modern Compiler
Implementation_.
  - From digging online, it seems the book's ML version is canonical and the
Java and C versions are ports.

## Chapter 4: Scanning

### Lexemes

Each individually meaningfully "blob" of characters is a _lexeme_. For example,
in the line

```js
var language = "lox";
```

the lexemes are `var`, `language`, `=`, `"lox"` and `;`.

---

### Line information in tokens for error reporting

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

### What the scanner does, in Nystromic vividness

> The core of the scanner is a loop. Starting at the first character of the
> source code, the scanner figures out what lexeme the character belongs to, and
> consumes it and any following characters that are part of that lexeme. When it
> reaches the end of that lexeme, it emits a token.
>
> Then it loops back and does it again, starting from the very next character in
> the source code. It keeps doing that, eating characters and occasionally, uh,
> excreting tokens, until it reaches the end of the input.

---

### Regex and lexical grammars

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

### Peeking lookahead

An interesting design choice:

> I could have made `peek()` take a parameter for the number of characters ahead
> to look instead of defining two functions, but that would allow _arbitrarily_
> far lookahead. Providing these two functions makes it clearer to a reader of
> the code that our scanner looks ahead at most two characters.

---

### Newlines vs `;`

How Python handles newlines is interesting:

> [Python](https://docs.python.org/3.5/reference/lexical_analysis.html#implicit-line-joining) treats
> all newlines as significant unless an explicit backslash is used at the end of
> a line to continue it to the next line. However, newlines anywhere inside a
> pair of brackets (`()`, `[]`, or `{}`) are ignored. Idiomatic style strongly
> prefers the latter.

## Chapter 5: Representing Code

### The evolution of syntactical grammars

Quite funny:

> People have been trying to crystallize grammar all the way back to
> Pāṇini's _Ashtadhyayi_, which codified Sanskrit grammar a mere couple thousand
> years ago. Not much progress happened until John Backus and company needed a
> notation for specifying ALGOL 58 and came up with [**Backus-Naur
> form**](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form) (**BNF**).

### The Visitor pattern

Here's a simple demonstration of the Visitor pattern using the example of a zoo
and different animals. Imagine a bunch of `Animal` subclasses:

```python
class Lion(Animal):
    def roar(self):
        return "ROAR!"

    def feed(self):
        return "Feeding the lion some meat"

    def make_sound(self):
        return self.roar()

    # Later, if we need to add health check...
    def health_check(self):
        return "Checking lion's teeth and claws"

    # And if we need to add playtime...
    def play_time(self):
        return "Playing with lion using big ball"

class Elephant(Animal):
    def trumpet(self):
        return "PAWOO!"

    def feed(self):
        return "Feeding the elephant some leaves"

    def make_sound(self):
        return self.trumpet()

    def health_check(self):
        return "Checking elephant's trunk and tusks"

    def play_time(self):
        return "Playing with elephant using water spray"

class Monkey(Animal):
    def screech(self):
        return "OOH OOH AH AH!"

    def feed(self):
        return "Feeding the monkey some bananas"

    def make_sound(self):
        return self.screech()

    def health_check(self):
        return "Checking monkey's agility and reflexes"

    def play_time(self):
        return "Playing with monkey using rope swings"
```

Usage would look like:

```python
# Create animals
lion = Lion()
elephant = Elephant()
monkey = Monkey()

# Do operations
print(lion.feed())          # "Feeding the lion some meat"
print(elephant.feed())      # "Feeding the elephant some leaves"
print(monkey.make_sound())  # "OOH OOH AH AH!"
```

The problems with this approach:

- Every time you want to add a new operation (like health_check or play_time),
  you have to modify _every_ animal class. With 3 animals it's manageable, but
  with 20 animals it becomes a maintenance nightmare.
- Related behaviors are scattered across different classes. All feeding logic is
  split between `Lion`, `Elephant`, and `Monkey` classes instead of being
  centralized in one place.
  - If you have a bug in the feeding logic, you have to fix it in multiple
    places.
- The animal classes become bloated with many methods that aren't core to what
  an animal is. An animal naturally makes sounds, but feeding and health checks
  are really zookeeper operations being forced into the animal class.

Compare this to the Visitor pattern where adding a new operation just means
creating a new visitor class:

```python
# Base classes
class Animal:
    def accept(self, visitor):
        visitor.visit(self)

class AnimalVisitor:
    def visit(self, animal):
        # This will be overridden by specific visitors
        pass

# Some concrete animals
class Lion(Animal):
    def roar(self):
        return "ROAR!"

class Elephant(Animal):
    def trumpet(self):
        return "PAWOO!"

class Monkey(Animal):
    def screech(self):
        return "OOH OOH AH AH!"

# Some concrete visitors
class PlayTimeVisitor(AnimalVisitor):
    def visit(self, animal):
        if isinstance(animal, Lion):
            return "Playing with lion using big ball"
        elif isinstance(animal, Elephant):
            return "Playing with elephant using water spray"
        elif isinstance(animal, Monkey):
            return "Playing with monkey using rope swings"

class FeedingVisitor(AnimalVisitor):
    def visit(self, animal):
        if isinstance(animal, Lion):
            return "Feeding the lion some meat"
        elif isinstance(animal, Elephant):
            return "Feeding the elephant some leaves"
        elif isinstance(animal, Monkey):
            return "Feeding the monkey some bananas"

class SoundVisitor(AnimalVisitor):
    def visit(self, animal):
        if isinstance(animal, Lion):
            return animal.roar()
        elif isinstance(animal, Elephant):
            return animal.trumpet()
        elif isinstance(animal, Monkey):
            return animal.screech()
```

Usage would look like:

```python
lion = Lion()
elephant = Elephant()
monkey = Monkey()

feeding_visitor = FeedingVisitor()
print(feeding_visitor.visit(lion))  # "Feeding the lion some meat"
```

The Visitor pattern is great when:

- you expect to add _operations_, not new _classes_ (here, animals), and
- the operations aren't fundamental to the class itself (feeding, health checks,
  and playtime aren't fundamental to what an animal is; addition/concatentation
  and multiplication aren't fundamental to what a token is).

This makes the Visitor pattern a natural fit for interpreter design.
