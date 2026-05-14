# Coding Question Test Case Guide

## Two Execution Modes

The exam portal supports two modes of code execution:

### 1. STDIO Mode (Standard Input/Output)
Students read from input and print to output.

**Example Question:** Write a program to add two numbers

**Student Solution:**
```python
a = int(input())
b = int(input())
print(a + b)
```

**Test Cases Format:**
```json
[
  {"input": "5\n3", "output": "8"},
  {"input": "10\n20", "output": "30"},
  {"input": "-5\n5", "output": "0"}
]
```

---

### 2. Function Mode (Recommended)
Students write a function that takes parameters and returns a value.

**Example Question:** Write a function to multiply a number by 10

**Student Solution:**
```python
def solution(n):
    return n * 10
```

**Test Cases Format:**
```json
[
  {"args": [5], "output": "50"},
  {"args": [10], "output": "100"},
  {"args": [-3], "output": "-30"}
]
```

---

## More Examples

### Example 1: String Reversal (Function Mode)

**Question:** Write a function that reverses a string

**Starter Code:**
```python
def solution(s):
    # Your code here
    pass
```

**Test Cases:**
```json
[
  {"args": ["hello"], "output": "olleh"},
  {"args": ["world"], "output": "dlrow"},
  {"args": [""], "output": ""}
]
```

---

### Example 2: Array Sum (Function Mode)

**Question:** Write a function that returns the sum of all elements in an array

**Starter Code:**
```python
def solution(arr):
    # Your code here
    pass
```

**Test Cases:**
```json
[
  {"args": [[1, 2, 3]], "output": "6"},
  {"args": [[10, 20, 30, 40]], "output": "100"},
  {"args": [[]], "output": "0"}
]
```

---

### Example 3: Check Prime (STDIO Mode)

**Question:** Write a program that checks if a number is prime. Print "Yes" or "No".

**Test Cases:**
```json
[
  {"input": "7", "output": "Yes"},
  {"input": "10", "output": "No"},
  {"input": "2", "output": "Yes"},
  {"input": "1", "output": "No"}
]
```

---

### Example 4: Fibonacci Series (Function Mode)

**Question:** Write a function that returns the nth Fibonacci number

**Starter Code:**
```python
def solution(n):
    # Your code here
    pass
```

**Test Cases:**
```json
[
  {"args": [0], "output": "0"},
  {"args": [1], "output": "1"},
  {"args": [5], "output": "5"},
  {"args": [10], "output": "55"}
]
```

---

### Example 5: Multiple Arguments (Function Mode)

**Question:** Write a function that finds the maximum of three numbers

**Starter Code:**
```python
def solution(a, b, c):
    # Your code here
    pass
```

**Test Cases:**
```json
[
  {"args": [1, 2, 3], "output": "3"},
  {"args": [10, 5, 8], "output": "10"},
  {"args": [-1, -5, -3], "output": "-1"}
]
```

---

## Tips for Teachers

### Function Mode (Recommended)
✅ **Pros:**
- More like professional coding platforms (LeetCode, HackerRank)
- Students focus on logic, not I/O handling
- Easier to test with specific inputs
- Better for algorithmic problems

**Use for:**
- Array/string manipulation
- Mathematical computations
- Data structure problems
- Algorithm implementation

### STDIO Mode
✅ **Pros:**
- Good for beginners learning I/O
- Simpler for basic programs
- Works with any language without function signatures

**Use for:**
- Simple input/output programs
- Pattern printing
- Basic control flow exercises

---

## Common Patterns

### List/Array Input
```json
{"args": [[1, 2, 3, 4, 5]], "output": "15"}
```

### String Input
```json
{"args": ["hello world"], "output": "5"}
```

### Multiple Inputs
```json
{"args": [5, 3], "output": "15"}
```

### Boolean Output
```json
{"args": [7], "output": "True"}
```

### JSON Output
```json
{"args": [[3, 1, 2]], "output": "[1, 2, 3]"}
```

---

## Best Practices

1. **Always provide starter code** for function mode
2. **Test edge cases**: empty inputs, negative numbers, zeros
3. **Use clear variable names** in test cases
4. **Include 3-5 test cases** per question
5. **Make first test case simple** (it's visible to students)
6. **Add complex test cases** as hidden tests

---

## Troubleshooting

### Test Case Fails But Code Looks Correct
- Check output format (string vs number)
- Ensure no extra whitespace or newlines
- Verify function name is `solution` (default)

### Function Not Detected
- Make sure function is defined: `def solution(...):`
- Function must be at the top level (not inside another function)
- Check for syntax errors in student code

### Output Mismatch
- Output is compared as strings
- `25` and `25.0` are different
- Use `str()` or `int()` to normalize if needed
