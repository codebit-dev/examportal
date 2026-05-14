import subprocess
import tempfile
import os
import json
import re
from datetime import datetime

class CodeExecutor:
    """Professional compiler with function-based test case execution"""
    
    # Execution limits
    MAX_EXECUTION_TIME = 5  # seconds
    MAX_OUTPUT_SIZE = 10240  # 10KB
    
    @staticmethod
    def wrap_python_code(code, function_name, input_vars, output_var):
        """Wrap student code in a testable function"""
        wrapped = f"""
import sys
import json

# Read input from stdin
try:
    input_data_raw = sys.stdin.read().strip()
    input_data = json.loads(input_data_raw)
    if not isinstance(input_data, list):
        input_data = [input_data]
except:
    input_data = []

{code}

# Test function
try:
    result = {function_name}(*input_data)
    if isinstance(result, (list, dict)):
        print(json.dumps(result))
    else:
        print(result)
except Exception as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
        return wrapped
    
    @staticmethod
    def wrap_java_code(code, class_name, method_name, input_vars, output_var):
        """Wrap Java code for testing with main method"""
        # Check if student already has a main method
        has_main = 'public static void main' in code
        
        if has_main:
            # Student wrote their own main method, use as-is
            return code
        
        # Wrap student's solution class with a TestRunner
        wrapped = f"""
{code}

public class TestRunner {{
    public static void main(String[] args) {{
        try {{
            {class_name} solver = new {class_name}();
            // For now, just instantiate - actual test harness handles input
            System.out.println("Solution class loaded successfully");
        }} catch (Exception e) {{
            System.err.println("ERROR: " + e.getMessage());
            System.exit(1);
        }}
    }}
}}
"""
        return wrapped
    
    @staticmethod
    def execute_java_with_test(code, input_data, method_name="solution", class_name="Solution"):
        """Execute Java code with function-based testing"""
        try:
            # Parse input data
            if isinstance(input_data, list):
                args = input_data
            else:
                args = [input_data]
            
            # Generate test runner with actual test case
            test_code = CodeExecutor.generate_java_test_runner(code, class_name, method_name, args)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write only the TestRunner file (contains both classes)
                test_file = os.path.join(temp_dir, 'TestRunner.java')
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(test_code)
                
                # Compile ONLY TestRunner.java
                compile_result = subprocess.run(
                    ['javac', 'TestRunner.java'],
                    capture_output=True,
                    text=True,
                    timeout=CodeExecutor.MAX_EXECUTION_TIME,
                    cwd=temp_dir
                )
                
                if compile_result.returncode != 0:
                    return {
                        'output': None,
                        'error': compile_result.stderr.strip()[:CodeExecutor.MAX_OUTPUT_SIZE],
                        'exit_code': -1
                    }
                
                # Delete Solution.class to prevent Java from running it
                solution_class = os.path.join(temp_dir, 'Solution.class')
                if os.path.exists(solution_class):
                    os.remove(solution_class)
                
                # Run ONLY TestRunner class
                run_result = subprocess.run(
                    ['java', '-cp', temp_dir, 'TestRunner'],
                    capture_output=True,
                    text=True,
                    timeout=CodeExecutor.MAX_EXECUTION_TIME
                )
                
                output = run_result.stdout.strip()
                error = run_result.stderr.strip()
                
                if error and 'ERROR' in error:
                    return {
                        'output': None,
                        'error': error[:CodeExecutor.MAX_OUTPUT_SIZE],
                        'exit_code': -1
                    }
                
                return {
                    'output': output[:CodeExecutor.MAX_OUTPUT_SIZE],
                    'error': error[:CodeExecutor.MAX_OUTPUT_SIZE] if error else None,
                    'exit_code': run_result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {'output': None, 'error': 'Time Limit Exceeded', 'exit_code': -1}
        except Exception as e:
            return {'output': None, 'error': str(e), 'exit_code': -1}
    
    @staticmethod
    def generate_java_test_runner(code, class_name, method_name, args):
        """Generate a complete Java test runner with embedded solution"""
        # Determine argument types and generate appropriate code
        args_code = []
        for i, arg in enumerate(args):
            if isinstance(arg, int):
                args_code.append(str(arg))
            elif isinstance(arg, float):
                args_code.append(str(arg))
            elif isinstance(arg, str):
                args_code.append(f'"{arg}"')
            elif isinstance(arg, list):
                # Handle arrays
                if all(isinstance(x, int) for x in arg):
                    array_str = '{' + ', '.join(str(x) for x in arg) + '}'
                    args_code.append(f'new int[]{array_str}')
                elif all(isinstance(x, str) for x in arg):
                    array_str = '{' + ', '.join(f'"{x}"' for x in arg) + '}'
                    args_code.append(f'new String[]{array_str}')
                else:
                    args_code.append('null')
            else:
                args_code.append('null')
        
        args_str = ', '.join(args_code)
        
        # Extract just the method body from student's code
        import re
        # Find the method and extract it
        method_pattern = rf'public\s+\w+\s+{method_name}\s*\([^)]*\)\s*{{'
        method_match = re.search(method_pattern, code)
        
        if method_match:
            # Extract the class content (methods only)
            class_content = code[code.index('{', method_match.start()):]
            # Remove the class declaration wrapper
            student_methods = class_content
        else:
            student_methods = code
        
        # Create TestRunner with solution as an inner static class
        test_runner = f"""
import java.util.*;

public class TestRunner {{
    // Student's solution embedded as inner class
    static class Solution {{
{student_methods}
    }}
    
    public static void main(String[] args) {{
        try {{
            Solution solver = new Solution();
            Object result = solver.{method_name}({args_str});
            
            if (result == null) {{
                System.out.println("null");
            }} else if (result.getClass().isArray()) {{
                if (result instanceof int[]) {{
                    System.out.println(Arrays.toString((int[]) result));
                }} else if (result instanceof double[]) {{
                    System.out.println(Arrays.toString((double[]) result));
                }} else if (result instanceof String[]) {{
                    System.out.println(Arrays.toString((String[]) result));
                }} else {{
                    System.out.println(Arrays.toString((Object[]) result));
                }}
            }} else {{
                System.out.println(result);
            }}
        }} catch (Exception e) {{
            System.err.println("ERROR: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }}
    }}
}}
"""
        return test_runner
    
    @staticmethod
    def execute_python_with_input(code, input_data, function_name="solution", input_vars=["input_data"], output_var="result"):
        """Execute Python code with function-based testing"""
        try:
            # Wrap the code
            wrapped_code = CodeExecutor.wrap_python_code(code, function_name, input_vars, output_var)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(wrapped_code)
                f.flush()
                temp_file = f.name
            
            try:
                # Pass input as JSON
                input_json = json.dumps(input_data) if isinstance(input_data, (dict, list)) else str(input_data)
                
                result = subprocess.run(
                    ['python', temp_file],
                    input=input_json,
                    capture_output=True,
                    text=True,
                    timeout=CodeExecutor.MAX_EXECUTION_TIME,
                    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                )
                
                output = result.stdout.strip()
                error = result.stderr.strip()
                
                if error and 'ERROR:' in error:
                    return {
                        'output': None,
                        'error': error,
                        'exit_code': -1
                    }
                
                return {
                    'output': output[:CodeExecutor.MAX_OUTPUT_SIZE],
                    'error': error[:CodeExecutor.MAX_OUTPUT_SIZE] if error else None,
                    'exit_code': result.returncode
                }
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return {'output': None, 'error': 'Time Limit Exceeded', 'exit_code': -1}
        except Exception as e:
            return {'output': None, 'error': str(e), 'exit_code': -1}
    
    @staticmethod
    def execute_python_stdio(code, input_data):
        """Execute Python code using standard input/output (legacy mode)"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                f.flush()
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    ['python', temp_file],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=CodeExecutor.MAX_EXECUTION_TIME
                )
                
                output = result.stdout.strip()
                error = result.stderr.strip()
                
                return {
                    'output': output[:CodeExecutor.MAX_OUTPUT_SIZE],
                    'error': error[:CodeExecutor.MAX_OUTPUT_SIZE] if error else None,
                    'exit_code': result.returncode
                }
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return {'output': None, 'error': 'Time Limit Exceeded', 'exit_code': -1}
        except Exception as e:
            return {'output': None, 'error': str(e), 'exit_code': -1}
    
    @staticmethod
    def execute_java(code, input_data):
        """Execute Java code with given input"""
        try:
            # Extract class name from code
            class_name = 'Main'
            for line in code.split('\n'):
                if 'public class' in line:
                    class_name = line.split('public class')[1].split()[0].split('{')[0].strip()
                    break
            
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, f'{class_name}.java')
                with open(file_path, 'w') as f:
                    f.write(code)
                
                # Compile
                compile_result = subprocess.run(
                    ['javac', file_path],
                    capture_output=True,
                    text=True,
                    timeout=CodeExecutor.MAX_EXECUTION_TIME
                )
                
                if compile_result.returncode != 0:
                    return {
                        'output': None,
                        'error': compile_result.stderr.strip()[:CodeExecutor.MAX_OUTPUT_SIZE],
                        'exit_code': -1
                    }
                
                # Run
                run_result = subprocess.run(
                    ['java', '-cp', temp_dir, class_name],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=CodeExecutor.MAX_EXECUTION_TIME
                )
                
                return {
                    'output': run_result.stdout.strip()[:CodeExecutor.MAX_OUTPUT_SIZE],
                    'error': run_result.stderr.strip()[:CodeExecutor.MAX_OUTPUT_SIZE] if run_result.stderr else None,
                    'exit_code': run_result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {'output': None, 'error': 'Time Limit Exceeded', 'exit_code': -1}
        except Exception as e:
            return {'output': None, 'error': str(e), 'exit_code': -1}
    
    @staticmethod
    def execute_cpp(code, input_data):
        """Execute C++ code with given input"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                cpp_file = os.path.join(temp_dir, 'solution.cpp')
                exe_file = os.path.join(temp_dir, 'solution.exe')
                
                with open(cpp_file, 'w') as f:
                    f.write(code)
                
                # Compile
                compile_result = subprocess.run(
                    ['g++', '-o', exe_file, cpp_file, '-std=c++17'],
                    capture_output=True,
                    text=True,
                    timeout=CodeExecutor.MAX_EXECUTION_TIME
                )
                
                if compile_result.returncode != 0:
                    return {
                        'output': None,
                        'error': compile_result.stderr.strip()[:CodeExecutor.MAX_OUTPUT_SIZE],
                        'exit_code': -1
                    }
                
                # Run
                run_result = subprocess.run(
                    [exe_file],
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=CodeExecutor.MAX_EXECUTION_TIME
                )
                
                return {
                    'output': run_result.stdout.strip()[:CodeExecutor.MAX_OUTPUT_SIZE],
                    'error': run_result.stderr.strip()[:CodeExecutor.MAX_OUTPUT_SIZE] if run_result.stderr else None,
                    'exit_code': run_result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {'output': None, 'error': 'Time Limit Exceeded', 'exit_code': -1}
        except Exception as e:
            return {'output': None, 'error': str(e), 'exit_code': -1}
    
    @staticmethod
    def detect_execution_mode(code, language):
        """Detect if code uses function-based or stdio-based execution"""
        if language.lower() == 'python':
            # Check if code defines a function
            if re.search(r'def\s+\w+\s*\(', code):
                return 'function'
        return 'stdio'
    
    @staticmethod
    def execute_code(language, code, input_data, test_case=None):
        """Execute code based on language and test case format"""
        language = language.lower()
        
        # Detect execution mode
        mode = CodeExecutor.detect_execution_mode(code, language)
        
        if language in ['python', 'python3']:
            if mode == 'function' and test_case:
                # Function-based execution
                input_vars = test_case.get('input_vars', ['input_data'])
                output_var = test_case.get('output_var', 'result')
                function_name = test_case.get('function_name', 'solution')
                return CodeExecutor.execute_python_with_input(
                    code, input_data, function_name, input_vars, output_var
                )
            else:
                # STDIO-based execution
                input_str = str(input_data) if not isinstance(input_data, str) else input_data
                return CodeExecutor.execute_python_stdio(code, input_str)
        elif language in ['java']:
            if mode == 'function' and test_case:
                # Function-based execution for Java
                method_name = test_case.get('function_name', 'solution')
                class_name = 'Solution'
                # Extract class name if student defined it
                import re
                class_match = re.search(r'public\s+class\s+(\w+)', code)
                if class_match:
                    class_name = class_match.group(1)
                return CodeExecutor.execute_java_with_test(code, input_data, method_name, class_name)
            else:
                # STDIO-based execution
                return CodeExecutor.execute_java(code, str(input_data))
        elif language in ['cpp', 'c++', 'c']:
            return CodeExecutor.execute_cpp(code, str(input_data))
        else:
            return {'output': None, 'error': f'Language {language} not supported', 'exit_code': -1}
    
    @staticmethod
    def run_test_cases(language, code, test_cases):
        """Run code against multiple test cases"""
        results = []
        
        for i, test_case in enumerate(test_cases):
            # Support both old format (input/output) and new format (function-based)
            if 'input' in test_case:
                # STDIO mode: input is raw string
                input_data = test_case['input']
            elif 'args' in test_case:
                # Function mode: args is a list/dict of arguments
                input_data = test_case['args']
            else:
                input_data = test_case.get('input', '')
            
            expected_output = test_case.get('output', '').strip()
            
            execution_result = CodeExecutor.execute_code(language, code, input_data, test_case)
            
            # Compare output
            actual_output = execution_result.get('output', '')
            if actual_output is None:
                passed = False
            else:
                # Flexible comparison
                actual_output = actual_output.strip()
                passed = actual_output == expected_output
            
            results.append({
                'test_case_number': i + 1,
                'input': str(input_data),
                'expected_output': expected_output,
                'actual_output': actual_output,
                'passed': passed,
                'error': execution_result.get('error'),
                'exit_code': execution_result.get('exit_code')
            })
        
        return results
