"""Concept-check question bank: 75 free-text Python questions across 18 topics.

Each question has: id, topic, question, correct_answer, context, misconception_hint.
"""

CHATBOT_QUESTIONS = [
    # ── Basics ──
    {"id": 1,  "topic": "Basics",
     "question": "What is the output of `print(type(3/2))` in Python 3? Explain why.",
     "correct_answer": "<class 'float'> — because `/` in Python 3 always performs true division and returns a float, even if both operands are integers.",
     "context": "In Python 3, the `/` operator always returns a float. `3/2 = 1.5` so `type(3/2)` is `float`.",
     "misconception_hint": "Confusing Python 3 true division with Python 2 integer division where 3/2 would give 1."},

    {"id": 2,  "topic": "Basics",
     "question": "What is the result of `10 % 3`? What does the `%` operator do?",
     "correct_answer": "1. The `%` (modulo) operator returns the remainder after integer division. 10 ÷ 3 = 3 remainder 1.",
     "context": "Modulo returns the remainder: 10 = 3×3 + 1, so 10 % 3 = 1.",
     "misconception_hint": "Confusing modulo with division or thinking % gives a percentage."},

    {"id": 3,  "topic": "Basics",
     "question": "Is `bool(0)` True or False in Python? Explain what 'falsy' means.",
     "correct_answer": "False. In Python, `0`, empty strings `''`, empty lists `[]`, `None`, and `0.0` are all 'falsy' — they evaluate to False in a boolean context.",
     "context": "Python has truthy/falsy values. 0 is falsy so bool(0) is False.",
     "misconception_hint": "Thinking only the literal False is falsy, not understanding Python's truthiness rules."},

    {"id": 4,  "topic": "Basics",
     "question": "What does `2 ** 3 ** 2` evaluate to? Why?",
     "correct_answer": "512. The `**` operator is right-associative, so `2 ** 3 ** 2` = `2 ** (3**2)` = `2 ** 9` = 512.",
     "context": "Right-associativity: evaluated right-to-left for **.",
     "misconception_hint": "Assuming left-to-right evaluation: 2**3=8, 8**2=64 (wrong)."},

    {"id": 5,  "topic": "Basics",
     "question": "What is the difference between `//` and `/` in Python 3?",
     "correct_answer": "`/` is true division (always returns float). `//` is floor division (returns int or float, but truncated toward negative infinity). E.g., `7/2=3.5`, `7//2=3`.",
     "context": "// is floor division (rounds down), / is true division.",
     "misconception_hint": "Thinking // just truncates decimal (it floors, which differs for negatives: -7//2=-4, not -3)."},

    # ── Strings ──
    {"id": 6,  "topic": "Strings",
     "question": "What does `'hello'[1]` return? Why doesn't it return 'h'?",
     "correct_answer": "'e'. Python uses 0-based indexing — index 0 is 'h', index 1 is 'e'.",
     "context": "0-based indexing: index 0='h', 1='e', 2='l', 3='l', 4='o'.",
     "misconception_hint": "Assuming 1-based indexing where index 1 means the first element."},

    {"id": 7,  "topic": "Strings",
     "question": "What does `'abc' * 3` produce in Python?",
     "correct_answer": "'abcabcabc'. The `*` operator on strings means repetition — it concatenates the string that many times.",
     "context": "String repetition: 'abc' * 3 = 'abcabcabc'.",
     "misconception_hint": "Thinking * is multiplication and will raise an error, or produce '3abc'."},

    {"id": 8,  "topic": "Strings",
     "question": "Are strings mutable in Python? What happens if you try `s = 'hello'; s[0] = 'H'`?",
     "correct_answer": "No, strings are immutable. `s[0] = 'H'` raises a TypeError. To get 'Hello', you must create a new string: `s = 'H' + s[1:]`.",
     "context": "Strings are immutable in Python — you cannot change characters in-place.",
     "misconception_hint": "Treating strings like lists and assuming in-place character assignment works."},

    {"id": 9,  "topic": "Strings",
     "question": "What does `'hello'.upper()` return? Does it modify the original string?",
     "correct_answer": "Returns 'HELLO'. It does NOT modify the original string — it returns a new string. The variable `'hello'` is unchanged because strings are immutable.",
     "context": "String methods return new strings, they don't modify in-place.",
     "misconception_hint": "Thinking string methods like .upper() modify the string in-place and the original is changed."},

    {"id": 10, "topic": "Strings",
     "question": "Explain what `s[-1]` does for `s = 'python'`.",
     "correct_answer": "Returns 'n' — the last character. Negative indices count from the end: -1 is last, -2 is second-to-last, etc.",
     "context": "Negative indexing: s[-1] is the last element.",
     "misconception_hint": "Not knowing negative indices exist or thinking s[-1] raises an error."},

    # ── Lists ──
    {"id": 11, "topic": "Lists",
     "question": "What does `[1,2,3].append(4)` return? What is the list after this call?",
     "correct_answer": "Returns `None`. The list is modified in-place to `[1,2,3,4]`. `.append()` is a mutating method that returns None, not the modified list.",
     "context": "List mutating methods return None. The list itself is changed in-place.",
     "misconception_hint": "Expecting .append() to return the new list like in some other languages."},

    {"id": 12, "topic": "Lists",
     "question": "What happens when you do `a = [1,2,3]; b = a; b.append(4); print(a)`?",
     "correct_answer": "Prints `[1,2,3,4]`. `b = a` does NOT copy the list — both `a` and `b` point to the same list object. Mutating `b` also changes `a`.",
     "context": "Assignment copies the reference, not the object. Both names point to the same list.",
     "misconception_hint": "Thinking b = a creates an independent copy of the list."},

    {"id": 13, "topic": "Lists",
     "question": "What does `[1,2,3,4][1:3]` return? Is the stop index included?",
     "correct_answer": "`[2,3]`. Slicing `[start:stop]` includes index `start` but EXCLUDES index `stop`. So `[1:3]` gives indices 1 and 2.",
     "context": "Slicing is [start:stop) — stop is exclusive.",
     "misconception_hint": "Thinking the stop index is inclusive and expecting [2,3,4]."},

    {"id": 14, "topic": "Lists",
     "question": "How do you create a proper copy of a list `a` so that modifying the copy doesn't affect `a`?",
     "correct_answer": "Use `a[:]`, `list(a)`, or `a.copy()`. All create a shallow copy. Using `b = a` just creates another reference to the same list.",
     "context": "Shallow copy methods: a[:], list(a), a.copy(). Not b=a.",
     "misconception_hint": "Using b = a thinking it copies the list, or not knowing about copy methods."},

    {"id": 15, "topic": "Lists",
     "question": "What is the difference between `.sort()` and `sorted()`?",
     "correct_answer": "`.sort()` sorts the list in-place and returns `None`. `sorted()` returns a new sorted list without modifying the original. Use `sorted()` when you need the original preserved.",
     "context": ".sort() in-place returns None. sorted() returns new list.",
     "misconception_hint": "Thinking .sort() returns the sorted list or that sorted() modifies the original."},

    # ── Tuples ──
    {"id": 16, "topic": "Tuples",
     "question": "How do you create a tuple with only ONE element?",
     "correct_answer": "`(1,)` — with a trailing comma. `(1)` is just the integer 1 in parentheses, not a tuple. The trailing comma is what makes it a tuple.",
     "context": "Single-element tuple requires trailing comma: (1,). Without comma, (1) is just parenthesized int.",
     "misconception_hint": "Thinking (1) creates a single-element tuple."},

    {"id": 17, "topic": "Tuples",
     "question": "Are tuples mutable? What happens if you try to change an element?",
     "correct_answer": "No, tuples are immutable. `t[0] = 10` on a tuple raises a `TypeError`. To 'change' a tuple, you must create a new one.",
     "context": "Tuples are immutable — element assignment raises TypeError.",
     "misconception_hint": "Treating tuples like lists and assuming in-place modification works."},

    {"id": 18, "topic": "Tuples",
     "question": "If a tuple contains a list, e.g. `t = (1, [2,3])`, can you modify the list inside?",
     "correct_answer": "Yes! `t[1].append(4)` works — the tuple itself is immutable (you can't replace `t[1]`), but the list object inside can be mutated. So `t` becomes `(1, [2,3,4])`.",
     "context": "Tuples are immutable in terms of what objects they hold, but mutable objects inside can still be changed.",
     "misconception_hint": "Thinking immutability extends to all nested objects inside the tuple."},

    # ── Sets ──
    {"id": 19, "topic": "Sets",
     "question": "What does `{1, 2, 2, 3}` evaluate to? What property of sets explains this?",
     "correct_answer": "`{1, 2, 3}`. Sets only store unique elements — duplicates are automatically removed.",
     "context": "Sets are unordered collections of unique elements.",
     "misconception_hint": "Not knowing sets eliminate duplicates, expecting {1,2,2,3}."},

    {"id": 20, "topic": "Sets",
     "question": "What is the difference between `|` and `&` for sets?",
     "correct_answer": "`|` is the union operator (all elements from both sets). `&` is the intersection operator (only elements in both sets). E.g., `{1,2} | {2,3} = {1,2,3}` and `{1,2} & {2,3} = {2}`.",
     "context": "| = union, & = intersection for sets.",
     "misconception_hint": "Confusing union (|) with intersection (&)."},

    # ── Dictionaries ──
    {"id": 21, "topic": "Dicts",
     "question": "What happens if you access a missing key with `d['missing_key']`? How can you avoid the error?",
     "correct_answer": "Raises a `KeyError`. To safely access a key, use `d.get('missing_key')` which returns `None` by default, or `d.get('missing_key', default_value)` to specify a default.",
     "context": "Missing key with [] raises KeyError. .get() returns None or a default safely.",
     "misconception_hint": "Expecting None or a default value instead of KeyError from direct key access."},

    {"id": 22, "topic": "Dicts",
     "question": "What does `{'a': 1, 'a': 2}['a']` return? Are duplicate keys allowed?",
     "correct_answer": "Returns `2`. Python allows duplicate keys in a dict literal — the last value silently overwrites previous ones. So `'a': 2` overwrites `'a': 1`.",
     "context": "Last key-value wins when there are duplicates in dict literal.",
     "misconception_hint": "Thinking duplicate keys raise an error or that both values are stored."},

    {"id": 23, "topic": "Dicts",
     "question": "What is the difference between `.keys()`, `.values()`, and `.items()`?",
     "correct_answer": "`.keys()` returns a view of all keys. `.values()` returns a view of all values. `.items()` returns a view of all `(key, value)` pairs as tuples. All return dict_view objects (not lists) that reflect changes to the dict.",
     "context": ".keys()=keys, .values()=values, .items()=(key,value) pairs.",
     "misconception_hint": "Confusing which method returns what, or thinking they return lists."},

    {"id": 24, "topic": "Dicts",
     "question": "How does dictionary ordering work in Python 3.7+?",
     "correct_answer": "Since Python 3.7, dictionaries maintain insertion order — keys are iterated in the order they were added. This is a language guarantee (not just CPython implementation detail).",
     "context": "Python 3.7+ dicts preserve insertion order.",
     "misconception_hint": "Thinking dicts are unordered (was true in Python 2 and Python 3 before 3.7)."},

    # ── Control Flow ──
    {"id": 25, "topic": "Control Flow",
     "question": "What does `range(5)` produce? Does it include 5?",
     "correct_answer": "Produces integers 0, 1, 2, 3, 4. It does NOT include 5 — `range(stop)` is exclusive of stop. To include 5, use `range(6)` or `range(1,6)` to get 1–5.",
     "context": "range(n) produces 0 to n-1. Stop is exclusive.",
     "misconception_hint": "Thinking range(n) starts from 1 or is inclusive of n."},

    {"id": 26, "topic": "Control Flow",
     "question": "What is the difference between `break` and `continue` in a loop?",
     "correct_answer": "`break` immediately exits the entire loop. `continue` skips the rest of the current iteration and jumps to the next iteration. Neither exits the function.",
     "context": "break exits loop, continue skips current iteration.",
     "misconception_hint": "Confusing break (exit loop) with continue (skip iteration)."},

    {"id": 27, "topic": "Control Flow",
     "question": "Explain what `else` on a `for` loop does in Python. Is it like `try/except` else?",
     "correct_answer": "A `for/else` block: the `else` runs if the loop completed normally without hitting `break`. It does NOT run if `break` was triggered. It's useful to detect if a search in a loop succeeded.",
     "context": "for/else: else runs when loop completes without break.",
     "misconception_hint": "Thinking for/else is like if/else (runs when loop body is empty or condition was False)."},

    {"id": 28, "topic": "Control Flow",
     "question": "What does the ternary expression `x if condition else y` do?",
     "correct_answer": "It returns `x` if `condition` is True, otherwise returns `y`. E.g., `'even' if n%2==0 else 'odd'` returns 'even' for even numbers. It's Python's one-line if-else.",
     "context": "Python ternary: value_if_true if condition else value_if_false.",
     "misconception_hint": "Not knowing Python's ternary syntax or confusing the order."},

    # ── Functions ──
    {"id": 29, "topic": "Functions",
     "question": "What does a Python function return if it has no explicit `return` statement?",
     "correct_answer": "`None`. All Python functions implicitly return `None` when execution reaches the end without a `return` statement.",
     "context": "No return statement → returns None.",
     "misconception_hint": "Thinking no return statement causes an error, or that the function returns 0 or False."},

    {"id": 30, "topic": "Functions",
     "question": "Why is using a mutable default argument like `def f(lst=[]):` dangerous?",
     "correct_answer": "The default list `[]` is created ONCE when the function is defined, not on each call. So if you mutate `lst` inside `f`, the changes persist across subsequent calls. This is a classic Python gotcha. Fix: use `def f(lst=None): if lst is None: lst = []`.",
     "context": "Mutable defaults are created once at definition time, shared across calls.",
     "misconception_hint": "Thinking default arguments are re-created fresh on every function call."},

    {"id": 31, "topic": "Functions",
     "question": "What is the difference between `*args` and `**kwargs`?",
     "correct_answer": "`*args` collects extra positional arguments into a tuple. `**kwargs` collects extra keyword arguments into a dict. E.g., `def f(*args, **kwargs)` can accept any combination of positional and keyword args.",
     "context": "*args = extra positional as tuple, **kwargs = extra keyword as dict.",
     "misconception_hint": "Confusing *args with **kwargs or thinking they're interchangeable."},

    {"id": 32, "topic": "Functions",
     "question": "What is a lambda function? What are its limitations compared to a regular function?",
     "correct_answer": "A lambda is an anonymous, single-expression function: `lambda x: x*2`. Limitations: can only contain a single expression (no statements, no assignments, no multiple lines). For complex logic, use `def`.",
     "context": "lambda = anonymous single-expression function. No statements allowed.",
     "misconception_hint": "Thinking lambdas can contain multiple statements or be multi-line."},

    {"id": 33, "topic": "Functions",
     "question": "Explain the concept of variable scope in Python (LEGB rule).",
     "correct_answer": "Python resolves variable names in this order: Local → Enclosing → Global → Built-in (LEGB). A variable in an inner function shadows outer ones. Use `global` to write to module-level vars, `nonlocal` to write to enclosing function vars.",
     "context": "LEGB: Local, Enclosing, Global, Built-in scope lookup order.",
     "misconception_hint": "Not understanding scope lookup or thinking inner functions can freely modify outer variables."},

    # ── OOP ──
    {"id": 34, "topic": "OOP",
     "question": "What is `self` in a Python class method? Is it a keyword?",
     "correct_answer": "`self` refers to the instance the method is called on. It's NOT a keyword — it's a convention. Python automatically passes the instance as the first argument. You could name it anything (like `this`), but `self` is the universal convention.",
     "context": "self is the instance, passed automatically as first arg. It's a convention, not keyword.",
     "misconception_hint": "Thinking self is a reserved Python keyword like in Java's `this`."},

    {"id": 35, "topic": "OOP",
     "question": "What is the difference between `__init__` and `__new__` in Python?",
     "correct_answer": "`__new__` creates the instance (allocates memory). `__init__` initializes the already-created instance with attributes. In practice, you almost always override `__init__` — `__new__` is only overridden for metaclasses or immutable types like int.",
     "context": "__new__ creates, __init__ initializes. Normally only override __init__.",
     "misconception_hint": "Thinking __init__ creates the object (it doesn't — __new__ does)."},

    {"id": 36, "topic": "OOP",
     "question": "What is the difference between `@staticmethod` and `@classmethod`?",
     "correct_answer": "`@staticmethod`: doesn't receive `self` or `cls` — just a regular function namespaced in the class. `@classmethod`: receives `cls` (the class itself) as first arg, useful for factory methods or accessing class-level state.",
     "context": "@staticmethod: no self/cls. @classmethod: receives cls as first arg.",
     "misconception_hint": "Confusing staticmethod (no class/instance access) with classmethod (receives cls)."},

    {"id": 37, "topic": "OOP",
     "question": "What is `__repr__` vs `__str__` in a class?",
     "correct_answer": "`__repr__` is the 'official' developer representation (shown in REPL, debuggers). `__str__` is the 'friendly' user-facing representation (used by `print()`). If only `__repr__` is defined, it's used for both. Guideline: `repr` should ideally be unambiguous/parseable.",
     "context": "__repr__ for developers/debugging, __str__ for users/print. repr used as fallback.",
     "misconception_hint": "Thinking __repr__ and __str__ are the same or interchangeable."},

    # ── Exceptions ──
    {"id": 38, "topic": "Exceptions",
     "question": "What is the difference between `try/except/else/finally`? When does `else` run?",
     "correct_answer": "`try`: code to attempt. `except`: runs if an exception occurs. `else`: runs ONLY if no exception occurred in `try`. `finally`: ALWAYS runs, exception or not. Use `finally` for cleanup (closing files etc.).",
     "context": "else: runs if no exception. finally: always runs.",
     "misconception_hint": "Confusing else (no exception) with finally (always runs)."},

    {"id": 39, "topic": "Exceptions",
     "question": "What is the difference between `raise` in Python vs `throw` in Java/JavaScript?",
     "correct_answer": "Python uses `raise` (not `throw`). `raise ValueError('msg')` raises an exception. You can also `raise` with no argument inside `except` to re-raise the current exception.",
     "context": "Python uses raise, not throw. raise alone inside except re-raises.",
     "misconception_hint": "Using throw (Java/JS syntax) instead of raise in Python."},

    {"id": 40, "topic": "Exceptions",
     "question": "What exception does Python raise for division by zero? What about `0/0` vs `0//0`?",
     "correct_answer": "Both `0/0` and `0//0` raise `ZeroDivisionError`. For floats, `0.0/0` also raises `ZeroDivisionError` (Python doesn't produce NaN like some languages).",
     "context": "ZeroDivisionError for any division by zero including integer and floor division.",
     "misconception_hint": "Expecting ArithmeticError (Java) or NaN (JavaScript) instead of ZeroDivisionError."},

    # ── Comprehensions ──
    {"id": 41, "topic": "Comprehensions",
     "question": "What does `[x**2 for x in range(4)]` produce? Trace through it.",
     "correct_answer": "[0, 1, 4, 9]. `range(4)` = 0,1,2,3. Squaring: 0²=0, 1²=1, 2²=4, 3²=9. Result: [0,1,4,9].",
     "context": "range(4) gives 0,1,2,3. List comprehension squares each.",
     "misconception_hint": "Off-by-one: thinking range(4) gives 1,2,3,4 and expecting [1,4,9,16]."},

    {"id": 42, "topic": "Comprehensions",
     "question": "What is a generator expression vs a list comprehension? When should you use each?",
     "correct_answer": "List comprehension `[x for x in ...]` creates a full list in memory. Generator expression `(x for x in ...)` is lazy — yields one value at a time, uses much less memory. Use generators for large data or when you only need to iterate once.",
     "context": "[] = eager list in memory. () = lazy generator on demand.",
     "misconception_hint": "Not knowing generator expressions exist or thinking (x for x) creates a tuple."},

    {"id": 43, "topic": "Comprehensions",
     "question": "Write a dict comprehension that maps numbers 1–5 to their squares.",
     "correct_answer": "`{n: n**2 for n in range(1, 6)}` → `{1: 1, 2: 4, 3: 9, 4: 16, 5: 25}`. Dict comprehensions use `{}` with `key: value` syntax.",
     "context": "{k:v for ...} syntax for dict comprehensions.",
     "misconception_hint": "Using [] for dict comprehension or wrong syntax for key:value."},

    # ── File I/O ──
    {"id": 44, "topic": "File I/O",
     "question": "What is the difference between file modes `'r'`, `'w'`, `'a'`, and `'x'`?",
     "correct_answer": "`'r'`: read (error if missing). `'w'`: write, creates or TRUNCATES. `'a'`: append (creates if missing). `'x'`: exclusive create (error if file exists). Add 'b' for binary: `'rb'`, `'wb'`.",
     "context": "r=read, w=write/truncate, a=append, x=exclusive create.",
     "misconception_hint": "Confusing modes — especially 'w' truncating vs 'a' appending."},

    {"id": 45, "topic": "File I/O",
     "question": "Why use `with open(...) as f:` instead of manually calling `f.close()`?",
     "correct_answer": "The `with` statement (context manager) automatically calls `f.close()` when the block exits — even if an exception occurs. Manual `f.close()` can be skipped if an exception happens before it. `with` is safer and more Pythonic.",
     "context": "with = context manager, guarantees close even on exception.",
     "misconception_hint": "Not knowing context managers or thinking manual close is equivalent."},

    # ── Modules ──
    {"id": 46, "topic": "Modules",
     "question": "What is the difference between `import math` and `from math import sqrt`?",
     "correct_answer": "`import math`: imports the module. Must use `math.sqrt(x)`. `from math import sqrt`: imports only `sqrt` into current namespace. Can use `sqrt(x)` directly. The latter can cause name collisions if you have a local `sqrt`.",
     "context": "import module: need module.func. from module import func: direct access.",
     "misconception_hint": "Not understanding namespace differences between import styles."},

    {"id": 47, "topic": "Modules",
     "question": "What does `if __name__ == '__main__':` do? Why is it useful?",
     "correct_answer": "When a Python file is run directly, `__name__` is `'__main__'`. When it's imported as a module, `__name__` is the module's filename. This guard ensures certain code (like running a demo) only executes when the file is run directly, not when imported.",
     "context": "__name__ == '__main__' only when script run directly, not when imported.",
     "misconception_hint": "Not understanding the import/run-directly distinction."},

    # ── Generators ──
    {"id": 48, "topic": "Generators",
     "question": "What does the `yield` keyword do? How does it differ from `return`?",
     "correct_answer": "`yield` makes a function a generator. When called, the function returns a generator object — it doesn't execute. Each `next()` call resumes until the next `yield`. Unlike `return`, the function's state (local variables) is preserved between calls.",
     "context": "yield pauses execution and saves state. return exits completely.",
     "misconception_hint": "Thinking yield is just like return but can be used multiple times."},

    {"id": 49, "topic": "Generators",
     "question": "What is the memory advantage of generators over lists? Give an example.",
     "correct_answer": "Generators produce values one at a time (lazy evaluation) so they don't store all values in memory. For example, `range(1_000_000_000)` takes ~48 bytes (a range object), while `list(range(1_000_000_000))` would take ~8GB of RAM.",
     "context": "Generators: lazy, O(1) memory. Lists: eager, O(n) memory.",
     "misconception_hint": "Not understanding lazy evaluation — thinking generator still stores all values."},

    # ── Decorators ──
    {"id": 50, "topic": "Decorators",
     "question": "What does a Python decorator do? Explain with a simple example.",
     "correct_answer": "A decorator wraps a function to extend or modify its behavior. `@my_decorator` before `def f():` is syntactic sugar for `f = my_decorator(f)`. Example: a timing decorator can measure how long any function takes without modifying its source.",
     "context": "@decorator is sugar for f = decorator(f). Wraps function behavior.",
     "misconception_hint": "Not knowing decorators are just higher-order functions using @syntax."},

    # ── Types ──
    {"id": 51, "topic": "Types",
     "question": "What does `isinstance(True, int)` return? Explain why.",
     "correct_answer": "`True`. In Python, `bool` is a subclass of `int`. `True == 1` and `False == 0`. So `True` is an instance of both `bool` and `int`. This means `True + True == 2` works.",
     "context": "bool is subclass of int. True=1, False=0.",
     "misconception_hint": "Not knowing bool inherits from int, expecting False."},

    {"id": 52, "topic": "Types",
     "question": "What is dynamic typing in Python? How does it differ from static typing in Java?",
     "correct_answer": "Python is dynamically typed — a variable's type is determined at runtime and can change. `x = 5` (int), then `x = 'hello'` (str) is valid. Java is statically typed — type is declared at compile time and can't change. Python type hints are optional annotations, not enforced at runtime.",
     "context": "Dynamic typing: type assigned at runtime. Type hints are not enforced.",
     "misconception_hint": "Thinking Python type hints enforce type checking like Java's static types."},

    # ── Built-ins ──
    {"id": 53, "topic": "Built-ins",
     "question": "What is the difference between `map()` and a list comprehension?",
     "correct_answer": "Both apply a function to each element. `map(func, iterable)` returns a lazy iterator (like a generator). A list comprehension `[func(x) for x in iterable]` returns an eager list. `map` is slightly faster for simple function calls; comprehensions are more readable and support filtering.",
     "context": "map() is lazy iterator. list comprehension is eager list.",
     "misconception_hint": "Thinking map() returns a list directly (it returns a map object in Python 3)."},

    {"id": 54, "topic": "Built-ins",
     "question": "What does `enumerate()` do? Give an example of why it's useful.",
     "correct_answer": "`enumerate(iterable)` returns `(index, value)` pairs. Instead of `for i in range(len(lst)): print(i, lst[i])`, you write `for i, val in enumerate(lst): print(i, val)`. Cleaner and more Pythonic.",
     "context": "enumerate gives (index, value) pairs. Avoids range(len()) pattern.",
     "misconception_hint": "Using range(len(x)) pattern instead of enumerate, or not knowing enumerate exists."},

    {"id": 55, "topic": "Built-ins",
     "question": "Explain what `zip()` does with an example.",
     "correct_answer": "`zip([1,2,3], ['a','b','c'])` produces `(1,'a'), (2,'b'), (3,'c')`. It pairs elements from multiple iterables. If lengths differ, it stops at the shortest. Used for parallel iteration.",
     "context": "zip pairs elements from multiple iterables into tuples.",
     "misconception_hint": "Thinking zip concatenates lists or that it handles unequal lengths by filling with None (that's zip_longest)."},

    {"id": 56, "topic": "Built-ins",
     "question": "What does `filter(lambda x: x > 2, [1,2,3,4])` return?",
     "correct_answer": "Returns a filter object (lazy iterator) yielding `3, 4`. `filter(func, iterable)` keeps elements where `func(element)` is True. Convert to list with `list(filter(...))` to get `[3, 4]`.",
     "context": "filter returns lazy iterator of elements where func is True.",
     "misconception_hint": "Thinking filter returns a list or keeps elements where func is False."},

    # ── Memory & References ──
    {"id": 57, "topic": "Memory",
     "question": "What is the difference between `is` and `==` in Python?",
     "correct_answer": "`==` checks value equality (do they have the same value?). `is` checks identity (do they point to the same object in memory?). `[1,2] == [1,2]` is True, but `[1,2] is [1,2]` is False — two different list objects. Never use `is` to compare values.",
     "context": "== checks value. is checks identity (same object in memory).",
     "misconception_hint": "Using 'is' to compare values like strings or numbers (works by accident for small ints due to caching)."},

    {"id": 58, "topic": "Memory",
     "question": "What is the difference between shallow copy and deep copy?",
     "correct_answer": "Shallow copy (`list.copy()`, `list[:]`) creates a new container but nested objects are still shared. Deep copy (`copy.deepcopy()`) recursively copies all nested objects too. For `[[1,2],[3,4]]`, shallow copy shares the inner lists; deep copy creates independent inner lists.",
     "context": "Shallow: new container, shared nested. Deep: fully independent recursive copy.",
     "misconception_hint": "Thinking shallow copy fully isolates the copy — it doesn't for nested mutable objects."},

    # ── Scope ──
    {"id": 59, "topic": "Scope",
     "question": "What is a closure in Python? Give a practical example.",
     "correct_answer": "A closure is a function that 'remembers' variables from its enclosing scope even after that scope has finished. Example: `def make_counter(): count=0; def counter(): nonlocal count; count+=1; return count; return counter` — the inner `counter` closes over `count`.",
     "context": "Closure: inner function captures variables from outer function's scope.",
     "misconception_hint": "Not understanding closures or thinking inner function can't access outer variables after outer returns."},

    {"id": 60, "topic": "Scope",
     "question": "When do you need `global` vs `nonlocal` in Python?",
     "correct_answer": "`global x`: inside a function, lets you write to the module-level variable `x`. `nonlocal x`: inside a nested function, lets you write to the enclosing function's variable `x`. Without these keywords, assigning to `x` creates a new local variable.",
     "context": "global: module-level write. nonlocal: enclosing function write.",
     "misconception_hint": "Not knowing nonlocal exists or thinking you can write to outer scope variables without keyword."},

    # ── Recursion ──
    {"id": 61, "topic": "Recursion",
     "question": "What is the base case in recursion and why is it essential?",
     "correct_answer": "The base case is a condition where the function returns a result directly without making a recursive call. Without it, recursion never terminates, eventually hitting Python's recursion limit and raising `RecursionError`.",
     "context": "Base case prevents infinite recursion and RecursionError.",
     "misconception_hint": "Writing recursive functions without a base case or misplacing the base case condition."},

    {"id": 62, "topic": "Recursion",
     "question": "What error does Python raise for infinite recursion and why?",
     "correct_answer": "`RecursionError: maximum recursion depth exceeded`. Python has a default stack depth limit (~1000 frames). Use `sys.setrecursionlimit()` to change it, but deep recursion can cause memory issues. Consider iteration or memoization for deeply recursive problems.",
     "context": "RecursionError with ~1000 default limit. sys.setrecursionlimit can change it.",
     "misconception_hint": "Expecting StackOverflowError (Java/C++) or that Python has unlimited stack depth."},

    # ── Operators ──
    {"id": 63, "topic": "Operators",
     "question": "Explain Python's `not`, `and`, and `or` operators with short-circuit evaluation.",
     "correct_answer": "`not x` inverts boolean. `x and y`: returns `x` if falsy, else `y` (short-circuits — if x is False, y is never evaluated). `x or y`: returns `x` if truthy, else `y`. E.g., `None or 'default'` = `'default'`, `5 and 'yes'` = `'yes'`.",
     "context": "Short-circuit: and returns first falsy or last. or returns first truthy or last.",
     "misconception_hint": "Thinking and/or always return True/False instead of one of the operands."},

    {"id": 64, "topic": "Operators",
     "question": "What does `x = x or []` do and why is it a common Python idiom?",
     "correct_answer": "If `x` is falsy (None, 0, empty), assigns `[]` to `x`. If `x` is truthy, keeps `x`. It's equivalent to `x if x else []`. Used as a safe default: `def f(lst=None): lst = lst or []`.",
     "context": "x or y returns x if truthy, else y. Used for safe defaults.",
     "misconception_hint": "Not understanding short-circuit evaluation making this pattern work."},

    # ── Advanced ──
    {"id": 65, "topic": "Advanced",
     "question": "What is the GIL (Global Interpreter Lock) in CPython? How does it affect threading?",
     "correct_answer": "The GIL is a mutex in CPython that allows only ONE thread to execute Python bytecode at a time. This means Python threads can't achieve true CPU parallelism for CPU-bound tasks. For I/O-bound tasks, threads still work well (GIL is released during I/O). Use `multiprocessing` for CPU parallelism.",
     "context": "GIL limits one thread at a time in CPython. Affects CPU-bound, not I/O-bound.",
     "misconception_hint": "Thinking Python threads give CPU parallelism like Java/C++ threads."},

    {"id": 66, "topic": "Advanced",
     "question": "What is `*` (star) unpacking in Python? Give examples.",
     "correct_answer": "`a, *b, c = [1,2,3,4,5]` → `a=1, b=[2,3,4], c=5`. In function calls: `func(*my_list)` unpacks list as positional args. In list literals: `[*list1, *list2]` merges lists. Very versatile Python 3 feature.",
     "context": "* unpacks iterables in assignment, function calls, and literals.",
     "misconception_hint": "Not knowing Python's extended unpacking (*) syntax."},

    {"id": 67, "topic": "Advanced",
     "question": "Explain Python's `__dunder__` (double underscore) methods. Why are they called magic methods?",
     "correct_answer": "Dunder (double-under) methods like `__len__`, `__add__`, `__iter__` define how objects respond to Python operators and built-in functions. E.g., `__len__` makes `len(obj)` work, `__add__` enables `+`. They're called magic because Python calls them implicitly.",
     "context": "Dunder methods define Python operator/built-in behavior. Called implicitly by Python.",
     "misconception_hint": "Thinking dunder methods must be called directly (e.g., obj.__len__()) rather than through built-ins."},

    # ── Python 3 ──
    {"id": 68, "topic": "Python 3",
     "question": "What does `input()` return in Python 3? How is it different from Python 2?",
     "correct_answer": "In Python 3, `input()` ALWAYS returns a string. To get an integer: `int(input())`. In Python 2, `input()` evaluated the input as Python code (dangerous!) and `raw_input()` returned a string.",
     "context": "Python 3 input() always returns str. Must cast for numeric types.",
     "misconception_hint": "Assuming input() can auto-detect type or return int (Python 2 behavior)."},

    {"id": 69, "topic": "Python 3",
     "question": "What are f-strings and what makes them better than `.format()` or `%` formatting?",
     "correct_answer": "f-strings (PEP 498, Python 3.6+): `f'Hello {name}!'`. Advantages: faster, more readable, support expressions directly `f'{2+2}'`, can access attributes `f'{obj.name}'`, and support format specs `f'{val:.2f}'`.",
     "context": "f-strings: fast, readable, support expressions. f'...' prefix.",
     "misconception_hint": "Not knowing f-string syntax or thinking you need quotes inside the braces."},

    {"id": 70, "topic": "Python 3",
     "question": "What are type hints in Python? Are they enforced at runtime?",
     "correct_answer": "Type hints (PEP 484): `def f(x: int) -> str: ...`. They are NOT enforced at runtime — Python still allows wrong types without error. They're for documentation and static analysis tools (mypy, pyright, IDEs). Runtime enforcement requires libraries like `pydantic`.",
     "context": "Type hints are documentation only, not enforced at runtime.",
     "misconception_hint": "Thinking Python type hints enforce types at runtime like Java/TypeScript."},

    # ── Iterators ──
    {"id": 71, "topic": "Iterators",
     "question": "What is the difference between an iterable and an iterator in Python?",
     "correct_answer": "An **iterable** has `__iter__()` (lists, strings, dicts). An **iterator** has both `__iter__()` and `__next__()`. `iter(x)` converts an iterable to an iterator. Iterators are one-pass — once exhausted, they're done. Lists can be iterated multiple times.",
     "context": "Iterable: has __iter__. Iterator: has __iter__ + __next__. One-pass.",
     "misconception_hint": "Thinking iterables and iterators are the same thing."},

    {"id": 72, "topic": "Iterators",
     "question": "What happens when you call `next()` on an exhausted iterator?",
     "correct_answer": "Raises `StopIteration`. This is how Python's for loops know to stop — internally they catch `StopIteration`. You can provide a default: `next(iterator, default_value)` to avoid the exception.",
     "context": "StopIteration raised when iterator is exhausted. next(it, default) avoids exception.",
     "misconception_hint": "Expecting None or looping back to start when iterator is exhausted."},

    # ── String Methods ──
    {"id": 73, "topic": "Strings",
     "question": "What is the difference between `split()` and `split(' ')`?",
     "correct_answer": "`split()` (no arg) splits on any whitespace (spaces, tabs, newlines) and removes empty strings. `split(' ')` splits ONLY on single spaces and can produce empty strings for consecutive spaces. E.g., `'a  b'.split()` = `['a','b']` but `'a  b'.split(' ')` = `['a','','b']`.",
     "context": "split() handles all whitespace + collapses. split(' ') only single space.",
     "misconception_hint": "Thinking split() and split(' ') are identical."},

    {"id": 74, "topic": "Strings",
     "question": "How does string `join()` work? Why is `''.join(list)` faster than concatenation with `+`?",
     "correct_answer": "`'sep'.join(iterable)` concatenates strings with `sep` between them. `'+'.join(['a','b','c'])` = `'a+b+c'`. It's faster than `a + b + c` because Python strings are immutable — each `+` creates a new string object. `join()` does it in one pass.",
     "context": "join() is O(n). Repeated + concatenation is O(n²) due to immutability.",
     "misconception_hint": "Not knowing join() or thinking + concatenation is equally efficient."},

    {"id": 75, "topic": "Strings",
     "question": "What is string interning in Python? Why does `'hello' is 'hello'` return True but `a is b` (for two separately created strings) might not?",
     "correct_answer": "Python automatically 'interns' (reuses the same object for) string literals that look like identifiers. So two `'hello'` literals may share the same object. But `a = ''.join(['hel','lo'])` creates a new object. This is an implementation detail — always use `==` to compare string values, never `is`.",
     "context": "String interning: Python reuses some string objects. Always use == for value comparison.",
     "misconception_hint": "Using 'is' to compare strings and being confused by inconsistent results due to interning."},
]
