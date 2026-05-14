#!/usr/bin/env python
"""Test the code executor with function-based test cases"""

from code_executor import CodeExecutor

print("=" * 60)
print("Testing Function-Based Code Execution")
print("=" * 60)

# Test 1: Simple function (multiply by 10)
print("\n✓ Test 1: Multiply by 10")
code1 = """
def solution(n):
    return n * 10
"""
test_cases1 = [
    {"args": [5], "output": "50"},
    {"args": [10], "output": "100"},
    {"args": [-3], "output": "-30"}
]
results1 = CodeExecutor.run_test_cases('python', code1, test_cases1)
for r in results1:
    status = "✓ PASS" if r['passed'] else "✗ FAIL"
    print(f"  Test {r['test_case_number']}: {status} | Expected: {r['expected_output']} | Got: {r['actual_output']}")

# Test 2: String reversal
print("\n✓ Test 2: String Reversal")
code2 = """
def solution(s):
    return s[::-1]
"""
test_cases2 = [
    {"args": ["hello"], "output": "olleh"},
    {"args": ["world"], "output": "dlrow"}
]
results2 = CodeExecutor.run_test_cases('python', code2, test_cases2)
for r in results2:
    status = "✓ PASS" if r['passed'] else "✗ FAIL"
    print(f"  Test {r['test_case_number']}: {status} | Expected: {r['expected_output']} | Got: {r['actual_output']}")

# Test 3: Array sum
print("\n✓ Test 3: Array Sum")
code3 = """
def solution(arr):
    return sum(arr)
"""
test_cases3 = [
    {"args": [[1, 2, 3]], "output": "6"},
    {"args": [[10, 20, 30]], "output": "60"}
]
results3 = CodeExecutor.run_test_cases('python', code3, test_cases3)
for r in results3:
    status = "✓ PASS" if r['passed'] else "✗ FAIL"
    print(f"  Test {r['test_case_number']}: {status} | Expected: {r['expected_output']} | Got: {r['actual_output']}")

# Test 4: STDIO mode (backward compatibility)
print("\n✓ Test 4: STDIO Mode (Backward Compatible)")
code4 = """
a = int(input())
b = int(input())
print(a + b)
"""
test_cases4 = [
    {"input": "5\n3", "output": "8"},
    {"input": "10\n20", "output": "30"}
]
results4 = CodeExecutor.run_test_cases('python', code4, test_cases4)
for r in results4:
    status = "✓ PASS" if r['passed'] else "✗ FAIL"
    print(f"  Test {r['test_case_number']}: {status} | Expected: {r['expected_output']} | Got: {r['actual_output']}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
