import re

with open('backend/accounts/views.py', 'r') as f:
    lines = f.readlines()

# Find where UserProfileView should be
for i in range(355, 375):
    if 'def get(self, request):' in lines[i] and 'user = request.user' in lines[i+1]:
        print(f"Found broken UserProfileView at line {i+1}")
        # Insert class definition before the def
        lines.insert(i, 'class UserProfileView(APIView):\n')
        lines.insert(i+1, '    permission_classes = [IsAuthenticated]\n')
        lines.insert(i+2, '\n')
        break

with open('backend/accounts/views.py', 'w') as f:
    f.writelines(lines)

print("✅ Added missing UserProfileView class definition")
