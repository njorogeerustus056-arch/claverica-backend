import re

# Read the file
with open('backend/accounts/views.py', 'r') as f:
    content = f.read()

# Find the problematic UserProfileView
if 'class UserProfileView' in content:
    # Remove the broken one
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        if 'class UserProfileView' in lines[i] and i+1 < len(lines):
            # Skip this broken class
            print(f"Removing broken class at line {i+1}: {lines[i]}")
            i += 10  # Skip ahead
        else:
            new_lines.append(lines[i])
            i += 1
    
    content = '\n'.join(new_lines)

# Add correct UserProfileView at the end
correct_view = '''

# ============================================================================
# USER PROFILE VIEW
# ============================================================================
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class UserProfileView(APIView):
    """User profile endpoint for React frontend"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined,
        })
'''

# Add it to the end of file
content += correct_view

# Write back
with open('backend/accounts/views.py', 'w') as f:
    f.write(content)

print("✅ Fixed UserProfileView syntax error")
