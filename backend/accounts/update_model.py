import sys
import re

with open('models.py', 'r') as f:
    content = f.read()

# Find where to insert new fields - look for the last field before Meta class
# First, let's find the Account class
account_start = content.find('class Account(')
if account_start == -1:
    print("❌ Could not find Account class")
    sys.exit(1)

# Find the Meta class within the Account class
account_section = content[account_start:]
meta_match = re.search(r'\n    class Meta:', account_section)

if not meta_match:
    print("❌ Could not find Meta class in Account class")
    sys.exit(1)

# Find the position just before the Meta class
insert_position = account_start + meta_match.start()

# Get the content before and after insertion point
before_meta = content[:insert_position]
after_meta = content[insert_position:]

# Define the new fields to add
new_fields = '''
    # Frontend registration fields
    phone = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    doc_type = models.CharField(_('document type'), max_length=50, blank=True, null=True)
    doc_number = models.CharField(_('document number'), max_length=100, blank=True, null=True)
    street = models.CharField(_('street address'), max_length=255, blank=True, null=True)
    city = models.CharField(_('city'), max_length=100, blank=True, null=True)
    state = models.CharField(_('state'), max_length=100, blank=True, null=True)
    zip_code = models.CharField(_('zip code'), max_length=20, blank=True, null=True)
    occupation = models.CharField(_('occupation'), max_length=100, blank=True, null=True)
    employer = models.CharField(_('employer'), max_length=100, blank=True, null=True)
    income_range = models.CharField(_('income range'), max_length=50, blank=True, null=True)
    
    # Account number for display
    account_number = models.CharField(_('account number'), max_length=20, unique=True, blank=True, null=True)
'''

# Insert the new fields
updated_content = before_meta + new_fields + after_meta

# Write back to file
with open('models.py', 'w') as f:
    f.write(updated_content)

print("✅ Successfully added missing fields to Account model")
print(f"Added fields: phone, doc_type, doc_number, street, city, state, zip_code,")
print(f"              occupation, employer, income_range, account_number")
