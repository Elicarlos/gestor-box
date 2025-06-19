from django.test import TestCase

from django.contrib.auth import get_user_model
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
