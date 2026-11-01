"""Example student submissions for the mining lab."""

PRESET_EXAMPLES = {
    "range(n) off-by-one": {
        "title": "Factorial Function",
        "desc": "Write the factorial(n) function that computes the factorial n! of a natural number n. If input n is negative, return 0.",
        "code": """def factorial(n):
    if n < 0:
        return 0
    fact = 1
    for i in range(n):
        fact = fact * i
    return fact""",
        "notes": "Student believes range(n) produces values from 1 to n inclusive.",
        "expect_clean": False,
    },
    "Tuple mutation": {
        "title": "Append to Tuple",
        "desc": "Write a function that appends a dictionary to a tuple of elements.",
        "code": """def add_dict_to_tuple(test_tup, test_dict):
    list(test_tup)
    test_tup.append(test_dict)
    tuple(test_tup)
    return test_tup""",
        "notes": "Student believes tuples can be mutated in-place and list(tup) modifies tup.",
        "expect_clean": False,
    },
    "= vs ==": {
        "title": "Filter Long Words",
        "desc": "Write a function to return words longer than length n from a string.",
        "code": """def long_words(n, str):
    word_len = []
    txt = str.split(" ")
    for x in txt:
        if len(x) = n:
            word_len.append(x)
    return word_len""",
        "notes": "Student confuses assignment operator (=) with comparison operator (==).",
        "expect_clean": False,
    },
    "Clean recursion": {
        "title": "Factorial Recursive",
        "desc": "Write a factorial function that recursively computes factorial.",
        "code": """def factorial(n):
    if n <= 0:
        return 1
    return n * factorial(n - 1)""",
        "notes": "Correct implementation. The verification gate should return no misconception.",
        "expect_clean": True,
    },
    "Clean transpose": {
        "title": "Matrix Transpose",
        "desc": "Transpose an n x n square matrix in place.",
        "code": """def transpose(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    return matrix""",
        "notes": "Correct implementation with upper-triangle iteration.",
        "expect_clean": True,
    },
}
