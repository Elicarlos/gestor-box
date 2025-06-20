import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Cria um superusuário se variáveis de ambiente estiverem definidas'

    def handle(self, *args, **kwargs):
        username = os.getenv('DJANGO_SU_USERNAME')
        email = os.getenv('DJANGO_SU_EMAIL')
        password = os.getenv('DJANGO_SU_PASSWORD')

        if username and email and password:
            User = get_user_model()
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f'Superusuário "{username}" criado com sucesso.'))
            else:
                self.stdout.write(self.style.WARNING(f'Superusuário "{username}" já existe.'))
        else:
            self.stdout.write(self.style.NOTICE('Variáveis de ambiente não definidas. Nenhum superusuário criado.'))
