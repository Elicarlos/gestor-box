from django.db import models
from django.contrib.auth.models import BaseUserManager, User
from django.utils import timezone


class FuncionarioManager(BaseUserManager):
    """Custom manager to create Funcionario along with its related User."""

    def create_user(self, matricula, nome, senha=None, **extra_fields):
        """Create and return a ``Funcionario`` with an associated ``User``."""
        if not matricula:
            raise ValueError('Funcionário precisa de código de barras')

        user = User.objects.create_user(
            username=matricula,
            password=senha,
            first_name=nome,
        )

        funcionario = self.model(user=user, matricula=matricula, **extra_fields)
        funcionario.save(using=self._db)
        return funcionario

class Funcionario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='funcionario')
    matricula = models.CharField(max_length=50, unique=True)
    filial = models.ForeignKey('Filial', on_delete=models.CASCADE, related_name='funcionarios', null=True, blank=True)
    objects = FuncionarioManager()
    def __str__(self):
        if self.user:
            return self.user.get_full_name() or self.user.username
        return f'Funcionario {getattr(self, "matricula", self.id)}'

class Filial(models.Model):
    nome = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    def __str__(self):
        return self.nome

class Box(models.Model):
    nome = models.CharField(max_length=50)
    localizacao = models.CharField(max_length=100)
    filial = models.ForeignKey('Filial', on_delete=models.CASCADE, related_name='boxes', null=True, blank=True)
    def __str__(self):
        return self.nome

class Atividade(models.Model):
    nome = models.CharField(max_length=100)
    duracao_estimada = models.PositiveIntegerField(help_text="Duração em minutos")
    filial = models.ForeignKey('Filial', on_delete=models.CASCADE, related_name='atividades', null=True, blank=True)
    def __str__(self):
        return self.nome

class SessaoServico(models.Model):
    box = models.ForeignKey(Box, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE)
    data_hora_inicio = models.DateTimeField(default=timezone.now)
    data_hora_fim = models.DateTimeField(null=True, blank=True)

class SessaoAtividade(models.Model):
    sessao_servico = models.ForeignKey(SessaoServico, on_delete=models.CASCADE, related_name='atividades')
    atividade = models.ForeignKey(Atividade, on_delete=models.CASCADE)
    ordem = models.PositiveIntegerField(null=True, blank=True)
