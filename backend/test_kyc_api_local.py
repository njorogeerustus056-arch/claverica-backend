import json
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from kyc.views import check_kyc_requirement

# Get the test user
User = get_user_model()
try:
    user = User.objects.get(email='test@example.com')
    print(f'Found user: {user.email}')
except User.DoesNotExist:
    print('Test user not found. Run the test user creation script first.')
    exit()

# Create a mock POST request
factory = RequestFactory()
data = {
    "service_type": "transfer",
    "amount": 2000
}
request = factory.post(
    '/kyc/check-requirement/',
    data=json.dumps(data),
    content_type='application/json'
)
request.user = user

# Call the view function
response = check_kyc_requirement(request)
print(f'Status Code: {response.status_code}')
print(f'Response Data: {json.loads(response.content)}')
