print("=== CHECKING manage.py ===")
with open('manage.py', 'r') as f:
    content = f.read()
    print(f"First 5 lines:\n{content[:500]}")
    
    # Check for common issues
    if 'execute_from_command_lin' in content:
        print("🚨 ERROR: 'execute_from_command_lin' is incomplete!")
        print("Should be: 'execute_from_command_line'")
