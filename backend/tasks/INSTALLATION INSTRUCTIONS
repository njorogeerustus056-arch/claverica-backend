1. Add to INSTALLED_APPS in settings.py
pythonINSTALLED_APPS = [
    # ... other apps ...
    'tasks',
]
2. Add to urls.py
pythonurlpatterns = [
    # ... other paths ...
    path('api/tasks/', include('tasks.urls')),
]
3. Run Migrations
bashpython manage.py makemigrations tasks
python manage.py migrate tasks
4. Create Sample Data (Optional)
bashpython manage.py shell
Then in the shell:
pythonfrom tasks.models import Task, TaskCategory
from decimal import Decimal

# Create categories
TaskCategory.objects.create(name="Product Reviews", icon="⭐", color="blue")
TaskCategory.objects.create(name="Surveys", icon="📊", color="green")

# Create sample tasks
Task.objects.create(
    title="Product Review Task #1",
    description="Complete marketplace review",
    task_type="review",
    reward_amount=Decimal("575.00"),
    estimated_time=10,
    status="active"
)

Task.objects.create(
    title="Product Review Task #2",
    description="Quality assessment",
    task_type="review",
    reward_amount=Decimal("575.00"),
    estimated_time=10,
    status="active"
)

Task.objects.create(
    title="Product Review Task #3",
    description="User experience feedback",
    task_type="review",
    reward_amount=Decimal("575.00"),
    estimated_time=10,
    status="active"
)

Task.objects.create(
    title="Product Review Task #4",
    description="Final review submission",
    task_type="review",
    reward_amount=Decimal("575.00"),
    estimated_time=10,
    status="active"
)
5. Create Superuser (if not exists)
bashpython manage.py createsuperuser

📊 API ENDPOINTS
Tasks

GET /api/tasks/tasks/ - List all active tasks
GET /api/tasks/tasks/{id}/ - Get task details
GET /api/tasks/tasks/available/ - Get available tasks for user
GET /api/tasks/tasks/stats/ - Get task statistics

User Tasks

GET /api/tasks/user-tasks/ - List user's tasks
POST /api/tasks/user-tasks/ - Start a new task
POST /api/tasks/user-tasks/{id}/submit/ - Submit completed task
POST /api/tasks/user-tasks/{id}/complete/ - Mark as completed
GET /api/tasks/user-tasks/completed/ - Get completed tasks
GET /api/tasks/user-tasks/pending/ - Get pending tasks
GET /api/tasks/user-tasks/stats/ - Get user task statistics

Reward Balance

GET /api/tasks/balance/my_balance/ - Get current balance
GET /api/tasks/balance/summary/ - Get balance summary

Withdrawals

GET /api/tasks/withdrawals/ - List withdrawals
POST /api/tasks/withdrawals/ - Request withdrawal
POST /api/tasks/withdrawals/{id}/cancel/ - Cancel withdrawal

Categories

GET /api/tasks/categories/ - List task categories
