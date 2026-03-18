# HOOP — Human Object Oriented Programming

HOOP is an object-oriented programming language designed and implemented from scratch in Python. Its syntax is built around English words instead of traditional mathematical symbols, making code more explicit and readable. The project includes a full four-phase interpreter and a desktop IDE built with Tkinter.

---

## Why HOOP?

Most languages use symbols like `+`, `-`, `==` that feel abstract, especially for people just getting into programming. HOOP replaces those symbols with words: `plus`, `minus`, `equals`. The result is code that reads almost like natural English, making the logical structure more transparent.

```
data price set 150;
data discount set 30;
data total set price minus discount;

when total greater 100 {
    display "Discounted price applied";
}
```

---

## Interpreter Architecture

The interpreter follows a classic four-phase sequential pipeline. Each phase consumes the output of the previous one and has a single, well-defined responsibility.

```
Source code (.hoop)
        ↓
┌──────────────────────┐
│  1. Lexical Analysis │  lexer.py → Token list
└──────────────────────┘
        ↓
┌───────────────────────────┐
│  2. Syntactic Analysis    │  parser_oficial.py → AST
└───────────────────────────┘
        ↓
┌──────────────────────────┐
│  3. Semantic Analysis    │  semantic.py → symbol table + validation
└──────────────────────────┘
        ↓
┌─────────────────┐
│  4. Execution   │  interpreter.py → program output
└─────────────────┘
```

---

## Phase 1 — Lexical Analysis (`lexer.py`)

The `AnalizadorLexico` class walks through the source code character by character and produces a list of `Token` objects. Each token carries its type, its value, and its exact position in the file (line and column), which is what makes error messages in later phases actually useful.

The lexer distinguishes five main categories of words: language keywords (`mold`, `when`, `cycle`...), data types (`whole`, `fract`, `text`...), word operators (`set`, `plus`, `equals`...), built-in functions (`display`, `length`, `input`...), and boolean literals (`true`, `false`). Anything that doesn't fall into one of those categories becomes an `IDENTIFIER`.

A few implementation details worth noting:

- Numbers are processed by peeking at the character after a dot — if it's a digit, the token is read as a `fract`; otherwise the dot is treated as a separate delimiter token.
- Strings support escape sequences (`\n`, `\t`, `\\`) and report an error if the closing quote is never found.
- Comments start with `#` or `//` and consume the rest of the line.
- Single-character literals with single quotes (`'A'`) are tokenized as `CHARACTER`.

---

## Phase 2 — Syntactic Analysis (`parser_oficial.py`)

`ParserOficial` implements a recursive descent parser. Each grammar rule is a Python function that calls other functions recursively, mirroring the structure of the language.

Operator precedence is baked into the call hierarchy:

```
parse_expresion
  └── parse_operacion_logica           (and, or)
        └── parse_operacion_comparacion   (equals, greater, less...)
              └── parse_operacion_aritmetica    (plus, minus)
                    └── parse_operacion_multiplicativa  (times, divide, mod)
                          └── parse_operacion_unaria    (not, unary minus)
                                └── parse_primary       (literals, identifiers, calls)
```

This ensures that `5 plus 3 times 2` evaluates as `5 + (3 * 2)` rather than `(5 + 3) * 2`.

The output is an Abstract Syntax Tree (AST) made up of the node types defined in `ast_nodes.py`. There's a node for every language construct: `DeclaracionNode`, `FuncionNode`, `ClaseNode`, `IfStatementNode`, `CycleStatementNode`, `ForgeNode`, and so on.

One intentional design constraint: the parser enforces a **maximum nesting depth of 3 levels** for control structures. Trying to add a fourth level of nested `when` or `cycle` raises an error before the parser continues. This is tracked via a `nesting_depth` counter that increments when entering a block and decrements when leaving it.

---

## Phase 3 — Semantic Analysis (`semantic.py`)

The `SemanticAnalyzer` walks the AST using the visitor pattern and validates that the program makes logical sense. The core data structure is the symbol table, implemented as a chain of nested `Scope` objects.

Each scope holds a reference to its parent, which allows variables from outer contexts to be visible inside inner ones but not the other way around. Symbol lookups walk up the chain until they find the name or reach the global scope.

Key validations performed:

- Variables and functions must be declared before use
- Constants (`fixed`) cannot be reassigned
- `answer` (return) is only valid inside functions
- `self` is only valid inside class methods
- `halt` and `skip` are only valid inside loops
- Function call argument count is checked against the declaration
- Arithmetic type mismatches emit warnings (not hard errors, since HOOP is dynamically typed at runtime)

On initialization, `_define_builtins` registers all built-in functions into the global scope with their expected return types and whether they're variadic. This is what allows calls to `display`, `length`, `input`, etc. to pass semantic validation without being flagged as undefined.

---

## Phase 4 — Execution (`interpreter.py`)

`HoopInterpreter` is also an AST visitor. Execution is direct: each node knows how to execute itself when visited.

Program state lives in a chain of `ExecutionContext` objects, analogous to the semantic scopes but storing actual runtime values instead of metadata. When a function is called, a new context is created as a child of the **global** context (not the current one), which prevents accidental variable capture from the caller's scope. When the function returns, the context is discarded.

Functions return values using Python's exception mechanism: when the interpreter hits a `ReturnNode` (the `answer` statement), it raises a `ReturnException` that bubbles up the call stack until the function-call handler catches it and extracts the value. The same pattern is used for `LoopBreak` (`halt`) and `LoopContinue` (`skip`).

Objects are represented by the `HoopObject` class, which is essentially a named attribute dictionary. When `forge Clase(args)` is executed, the interpreter creates an instance, initializes its attributes using the default values declared in the class body, then looks up and runs the constructor method. `self` is implemented as a `current_instance` variable on the interpreter that gets set before executing any method and restored after.

---

## The HOOP Language

### Data types

| HOOP     | Equivalent  | Example                |
|----------|-------------|------------------------|
| `whole`  | int         | `data x set 42;`       |
| `fract`  | float       | `data pi set 3.14;`    |
| `text`   | string      | `data s set "hello";`  |
| `logic`  | bool        | `data ok set true;`    |
| `char`   | character   | `data c set 'A';`      |
| `grid`   | matrix      | (composite type)       |
| `chain`  | linked list | (composite type)       |

### Operators

All operators are words, not symbols:

```
plus   minus   times   divide   mod
equals   notequals   greater   less   greatereq   lesseq
and   or   not
set   (assignment)
```

### Control flow

```
# Conditional
when score greater 90 {
    display "Excellent";
} otherwise {
    display "Keep trying";
}

# Ranged loop
cycle i from 1 to 10 {
    display i;
}

# While loop
repeat counter less 5 {
    counter set counter plus 1;
}

# Select / case
select option {
    case 1 { display "First option"; }
    case 2 { display "Second option"; }
    default { display "Other option"; }
}
```

### Functions and classes

```
action calculateArea(fract base, fract height) {
    data area set base times height divide 2;
    answer area;
}

mold Rectangle {
    fract width;
    fract height;

    action construct(fract w, fract h) {
        self.width set w;
        self.height set h;
    }

    action area() {
        answer self.width times self.height;
    }
}

data rect set forge Rectangle(10.0, 5.0);
display rect.area();
```

### Error handling

```
attempt {
    data result set 10 divide 0;
} rescue error {
    display "Error caught";
} ensure {
    display "This always runs";
}
```

### Built-in functions

`display`, `input`, `length`, `size`, `type`, `convert`, `abs`, `sqrt`, `pow`, `max`, `min`, `random`, `read`, `write`, `open`, `close`

---

## IDE (HOOP IDLE)

The graphical interface is built with Tkinter and follows a layout similar to VS Code: a file explorer sidebar on the left, an editor in the center, and a terminal panel at the bottom.

**Syntax highlighting** — implemented in `syntax_highlighter.py` using regex patterns applied in real time as the user types. Each token category gets a distinct color based on the One Dark Pro palette: keywords in purple, types in red, word operators in cyan, built-ins in teal, numbers in blue, and comments/strings in green. Brackets are colored by nesting level.

**Tabbed terminal** — the PROBLEMS tab shows errors and warnings from each compilation phase with their file locations. The OUTPUT tab shows the program's runtime output.

**Compile vs Run flow** — the Compile button runs only phases 1, 2 and 3 and reports any errors without executing the program. The Run button runs all four phases and streams output to the terminal.

**File management** — the sidebar supports creating `.hoop` files and folders, opening projects from disk, and drag-and-drop reordering of files within the explorer tree.

**Code snippets** — the Options menu includes pre-written examples and tests covering all language features, which load directly into the editor with a single click.

---

## Project Structure

```
HOOP/
├── run_gui.py                  # Entry point
├── src/
│   ├── core/
│   │   ├── lexer.py            # Phase 1: AnalizadorLexico
│   │   ├── parser_oficial.py   # Phase 2: ParserOficial (recursive descent)
│   │   ├── semantic.py         # Phase 3: SemanticAnalyzer + symbol table
│   │   ├── interpreter.py      # Phase 4: HoopInterpreter + ExecutionContext
│   │   ├── ast_nodes.py        # All AST node definitions
│   │   └── constants/
│   │       ├── keywords.py     # Reserved words, types, operators
│   │       └── code_snippets.py # Snippets for the Options menu
│   └── interface/
│       ├── main_gui.py              # Main window
│       ├── colors/colors.py         # Color palette
│       └── components/
│           ├── content_area.py      # Editor + compiler integration
│           ├── sidebar.py           # File explorer
│           ├── header.py            # Top bar + menus
│           ├── terminal.py          # Tabbed terminal panel
│           ├── syntax_highlighter.py # Real-time syntax highlighting
│           ├── line_numbers.py      # Line number gutter
│           └── welcome_screen.py    # Welcome screen
```

---

## Installation and Usage

```bash
# Clone the repository
git clone <repo-url>
cd HOOP

# Install dependencies
pip install pillow

# Launch the IDE
python run_gui.py
```

To run a HOOP file without the IDE, the core modules can be used directly:

```python
from src.core.lexer import AnalizadorLexico
from src.core.parser_oficial import parse_tokens
from src.core.semantic import analyze_hoop_semantics
from src.core.interpreter import interpret_hoop

with open("program.hoop") as f:
    code = f.read()

lexer = AnalizadorLexico(code)
tokens = lexer.analizar()

ast, syntax_errors = parse_tokens(tokens)
valid, semantic_errors, warnings = analyze_hoop_semantics(ast)
success, runtime_error, output = interpret_hoop(ast)

for line in output:
    print(line)
```

---

## Known Limitations

- Class inheritance is not implemented — each `mold` is standalone
- Control structure nesting is capped at 3 levels by design
- The `grid` and `chain` types are declared but their composite behavior is not fully implemented in the interpreter
- No module system or imports between `.hoop` files

---

