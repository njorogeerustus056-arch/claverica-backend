# Read and clean the file
with open('backend/accounts/views.py', 'r') as f:
    content = f.read()

# Remove everything from the broken UserProfileView onward
lines = content.split('\n')
new_lines = []
i = 0
in_broken_class = False
while i < len(lines):
    line = lines[i]
    
    # Look for the broken class
    if 'class UserProfileView' in line:
        print(f"Removing broken class starting at line {i+1}")
        in_broken_class = True
    
    if not in_broken_class:
        new_lines.append(line)
    else:
        # Skip until we find an empty line after class definition
        if line.strip() == '' and i > 0 and 'class' in lines[i-1]:
            in_broken_class = False
    
    i += 1

# Write cleaned file
with open('backend/accounts/views.py', 'w') as f:
    f.write('\n'.join(new_lines))
print("✅ Removed broken UserProfileView")
