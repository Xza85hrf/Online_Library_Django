import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_project.settings')
django.setup()

from accounts.models import CustomUser, UserProfile
from django.db import transaction

# Create test users with different roles
test_users = [
    {'email': 'admin@test.com', 'password': 'Test1234!', 'first_name': 'Admin', 'last_name': 'Test', 'role': 'admin'},
    {'email': 'librarian@test.com', 'password': 'Test1234!', 'first_name': 'Librarian', 'last_name': 'Test', 'role': 'librarian'},
    {'email': 'reader@test.com', 'password': 'Test1234!', 'first_name': 'Reader', 'last_name': 'Test', 'role': 'reader'}
]

created_users = []

with transaction.atomic():
    for user_data in test_users:
        # Check if user already exists
        if not CustomUser.objects.filter(email=user_data['email']).exists():
            # Create the user
            user = CustomUser.objects.create_user(
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_active=True
            )
            
            # Set the role in the user profile
            profile = user.profile
            profile.role = user_data['role']
            profile.save()
            
            created_users.append(user_data['email'])
            print(f'Created user: {user_data["email"]} with role: {user_data["role"]}')
        else:
            print(f'User {user_data["email"]} already exists')

print(f'Created {len(created_users)} test users')
