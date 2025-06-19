import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from .models import Funcionario


class FuncionarioManagerTests(TestCase):
    def test_create_user_creates_related_user(self):
        funcionario = Funcionario.objects.create_user(
            matricula="123", nome="Teste", senha="pwd12345"
        )

        self.assertEqual(funcionario.matricula, "123")
        self.assertEqual(funcionario.user.username, "123")
        self.assertEqual(funcionario.user.first_name, "Teste")
        self.assertTrue(funcionario.user.check_password("pwd12345"))


class LoginAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.funcionario = Funcionario.objects.create_user(
            matricula="321", nome="Login", senha="loginpwd"
        )

    def test_login_returns_jwt_token(self):
        response = self.client.post(
            "/api/login/",
            {"matricula": "321", "senha": "loginpwd"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        # validate that the token can be decoded
        AccessToken(data["access"])
