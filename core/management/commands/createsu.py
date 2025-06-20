import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Cria superusuário automaticamente se variáveis de ambiente estiverem presentes'

    def handle(self, *args, **kwargs):
        if os.getenv('CREATE_SUPERUSER') != 'True':
            self.stdout.write('Variável CREATE_SUPERUSER não é True. Pulando criação do superusuário.')
            return

        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

        if not username or not email or not password:
            self.stderr.write('Variáveis do superusuário incompletas.')
            return

        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(f'Superusuário "{username}" criado com sucesso.')
        else:
            self.stdout.write(f'O superusuário "{username}" já existe.')
