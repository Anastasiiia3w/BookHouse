from django.test import TestCase

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import SignUpForm
from .models import UserProfile


User = get_user_model()


class SignUpFormTests(TestCase):
    def test_valid_registration_form(self):
        form = SignUpForm(
            data={
                "username": "olena",
                "email": "olena@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            }
        )

        self.assertTrue(form.is_valid())

    def test_passwords_must_match(self):
        form = SignUpForm(
            data={
                "username": "olena",
                "email": "olena@example.com",
                "password1": "StrongPassword123!",
                "password2": "AnotherPassword123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_email_must_be_unique(self):
        User.objects.create_user(
            username="first-user",
            email="olena@example.com",
            password="StrongPassword123!",
        )

        form = SignUpForm(
            data={
                "username": "second-user",
                "email": "OLENA@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class AuthenticationViewTests(TestCase):
    def test_signup_creates_user_and_profile(self):
        response = self.client.post(
            reverse("users:signup"),
            {
                "username": "olena",
                "email": "olena@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
            follow=True,
        )

        user = User.objects.get(
            email="olena@example.com",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            UserProfile.objects.filter(user=user).exists()
        )
        self.assertTrue(
            response.context["user"].is_authenticated
        )

    def test_profile_requires_authentication(self):
        response = self.client.get(
            reverse("users:profile"),
        )

        expected_url = (
            f"{reverse('users:login')}"
            f"?next={reverse('users:profile')}"
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_profile_can_be_updated(self):
        user = User.objects.create_user(
            username="olena",
            email="olena@example.com",
            password="StrongPassword123!",
        )

        self.client.force_login(user)

        response = self.client.post(
            reverse("users:profile"),
            {
                "phone": "+380671234567",
                "city": "Київ",
            },
            follow=True,
        )

        user.profile.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.profile.city, "Київ")
        self.assertEqual(
            user.profile.phone,
            "+380671234567",
        )
        self.assertContains(
            response,
            "Профіль успішно оновлено.",
        )
