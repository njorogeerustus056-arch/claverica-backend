# Fields expected from frontend signup form
frontend_fields = {
    'required': ['email', 'first_name', 'last_name', 'password', 'confirm_password'],
    'identity': ['doc_type', 'doc_number', 'street', 'city', 'state', 'zip_code', 'phone'],
    'optional': ['occupation', 'employer', 'income_range']
}

print("=== FRONTEND EXPECTED FIELDS ===")
print("\\nRequired for registration:")
for field in frontend_fields['required']:
    print(f"  - {field}")

print("\\nIdentity verification:")
for field in frontend_fields['identity']:
    print(f"  - {field}")

print("\\nOptional employment:")
for field in frontend_fields['optional']:
    print(f"  - {field}")

print("\\n=== CHECKING ACTUAL MODEL ===")

import sys
import os

try:
    sys.path.insert(0, '.')
    sys.path.insert(0, '..')
    
    # Try to import the model directly
    from models import Account
    
    print(f"Model: {Account.__name__}")
    print(f"App label: {Account._meta.app_label}")
    
    print("\\nModel fields:")
    for field in Account._meta.fields:
        print(f"  - {field.name}: {field.get_internal_type()}")
        
    # Check which frontend fields exist
    print("\\n=== FIELD MATCHING ===")
    
    all_frontend_fields = []
    for category in frontend_fields.values():
        all_frontend_fields.extend(category)
    
    print("Missing fields (in frontend but not in model):")
    missing = []
    for field in all_frontend_fields:
        try:
            Account._meta.get_field(field)
        except:
            missing.append(field)
    
    for field in missing:
        print(f"  ❌ {field}")
    
    if not missing:
        print("  ✅ All frontend fields are in the model!")
        
except ImportError as e:
    print(f"Cannot import Account model: {e}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
