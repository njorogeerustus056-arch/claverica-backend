# Create find_error.py
import os

def find_error():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'Error handling compliance notification' in content:
                            print(f"Found in: {filepath}")
                            # Show the line
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if 'Error handling compliance notification' in line:
                                    print(f"Line {i+1}: {line}")
                                    # Show context
                                    start = max(0, i-5)
                                    end = min(len(lines), i+6)
                                    print("Context:")
                                    for j in range(start, end):
                                        print(f"{j+1}: {lines[j]}")
                                    print("-" * 50)
                except Exception as e:
                    pass

if __name__ == '__main__':
    find_error()