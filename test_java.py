#!/usr/bin/env python
"""Test Java code execution"""

from code_executor import CodeExecutor

print("=" * 60)
print("Testing Java Code Execution")
print("=" * 60)

# Test 1: Simple Java function (multiply by 10)
print("\n✓ Test 1: Java - Multiply by 10")
java_code1 = """
public class Solution {
    public int solution(int n) {
        return n * 10;
    }
}
"""
test_cases1 = [
    {"args": [5], "output": "50"},
    {"args": [10], "output": "100"},
    {"args": [-3], "output": "-30"}
]
results1 = CodeExecutor.run_test_cases('java', java_code1, test_cases1)
for r in results1:
    status = "✓ PASS" if r['passed'] else "✗ FAIL"
    print(f"  Test {r['test_case_number']}: {status} | Expected: {r['expected_output']} | Got: {r['actual_output']}")
    if r['error']:
        print(f"    Error: {r['error']}")

# Test 2: String reversal
print("\n✓ Test 2: Java - String Reversal")
java_code2 = """
public class Solution {
    public String solution(String s) {
        StringBuilder sb = new StringBuilder(s);
        return sb.reverse().toString();
    }
}
"""
test_cases2 = [
    {"args": ["hello"], "output": "olleh"},
    {"args": ["world"], "output": "dlrow"}
]
results2 = CodeExecutor.run_test_cases('java', java_code2, test_cases2)
for r in results2:
    status = "✓ PASS" if r['passed'] else "✗ FAIL"
    print(f"  Test {r['test_case_number']}: {status} | Expected: {r['expected_output']} | Got: {r['actual_output']}")
    if r['error']:
        print(f"    Error: {r['error']}")

print("\n" + "=" * 60)
print("Java tests completed!")
print("=" * 60)
