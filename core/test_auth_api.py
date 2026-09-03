from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import UserProfile
from departments.models import Department


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.department = Department.objects.create(name="Technology", code="TECH")
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="admin-user",
            email="admin-user@budgetflow.com",
            first_name="Admin",
            last_name="User",
            password="test-pass",
        )
        self.user.profile.role = UserProfile.Role.ADMIN
        self.user.profile.department = self.department
        self.user.profile.save(update_fields=["role", "department", "updated_at"])

    def login(self):
        return self.client.post(
            reverse("auth-login"),
            {"username": "admin-user", "password": "test-pass"},
            format="json",
        )

    def test_login_success_returns_tokens_and_user_info(self):
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        user = response.data["data"]["user"]
        self.assertEqual(user["username"], "admin-user")
        self.assertEqual(user["email"], "admin-user@budgetflow.com")
        self.assertEqual(user["full_name"], "Admin User")
        self.assertEqual(user["role"], UserProfile.Role.ADMIN)
        self.assertEqual(user["department"]["id"], self.department.id)

    def test_login_failure_returns_400(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "admin-user", "password": "wrong-pass"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_refresh_token_returns_access_token(self):
        login_response = self.login()
        refresh = login_response.data["data"]["refresh"]

        response = self.client.post(reverse("auth-refresh"), {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_me_returns_authenticated_user_info(self):
        login_response = self.login()
        access = login_response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.get(reverse("auth-me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["username"], "admin-user")
        self.assertEqual(response.data["data"]["role"], UserProfile.Role.ADMIN)

    def test_logout_blacklists_refresh_token(self):
        login_response = self.login()
        access = login_response.data["data"]["access"]
        refresh = login_response.data["data"]["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.post(reverse("auth-logout"), {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_unauthorized_request_is_blocked(self):
        response = self.client.get(reverse("department-list"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authorized_crud_request_is_allowed_for_admin(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("department-list"),
            {"name": "Finance", "code": "FIN"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

    def test_role_permission_blocks_employee_from_budget_endpoint(self):
        user_model = get_user_model()
        employee = user_model.objects.create_user(username="employee", password="test-pass")
        employee.profile.role = UserProfile.Role.EMPLOYEE
        employee.profile.save(update_fields=["role", "updated_at"])
        self.client.force_authenticate(user=employee)

        response = self.client.get(reverse("budget-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
