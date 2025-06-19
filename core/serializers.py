from rest_framework import serializers
from core.models import Funcionario, Box, Atividade, SessaoServico, SessaoAtividade, Filial

class FilialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filial
        fields = ['id', 'nome', 'cidade', 'uf']

class FuncionarioSerializer(serializers.ModelSerializer):
    filial = FilialSerializer(read_only=True)
    filial_id = serializers.PrimaryKeyRelatedField(queryset=Filial.objects.all(), source='filial', write_only=True)
    nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Funcionario
        fields = ['id', 'nome', 'matricula', 'filial', 'filial_id']

    def get_nome(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None

class BoxSerializer(serializers.ModelSerializer):
    filial = FilialSerializer(read_only=True)
    filial_id = serializers.PrimaryKeyRelatedField(queryset=Filial.objects.all(), source='filial', write_only=True)
    class Meta:
        model = Box
        fields = ['id', 'nome', 'localizacao', 'filial', 'filial_id']

class AtividadeSerializer(serializers.ModelSerializer):
    filial = FilialSerializer(read_only=True)
    filial_id = serializers.PrimaryKeyRelatedField(queryset=Filial.objects.all(), source='filial', write_only=True)
    class Meta:
        model = Atividade
        fields = ['id', 'nome', 'duracao_estimada', 'filial', 'filial_id']

class SessaoAtividadeSerializer(serializers.ModelSerializer):
    atividade = AtividadeSerializer()
    class Meta:
        model = SessaoAtividade
        fields = ['id', 'atividade', 'ordem']

class SessaoServicoSerializer(serializers.ModelSerializer):
    funcionario = FuncionarioSerializer(read_only=True)
    box = BoxSerializer(read_only=True)
    atividades = SessaoAtividadeSerializer(many=True, read_only=True)
    duracao_real = serializers.SerializerMethodField()
    soma_estimada_min = serializers.SerializerMethodField()

    class Meta:
        model = SessaoServico
        fields = [
            'id', 'box', 'funcionario', 'data_hora_inicio', 'data_hora_fim', 
            'atividades', 'duracao_real', 'soma_estimada_min'
        ]

    def get_duracao_real(self, obj):
        if obj.data_hora_fim and obj.data_hora_inicio:
            delta = obj.data_hora_fim - obj.data_hora_inicio
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f'{hours:02}:{minutes:02}:{seconds:02}'
        return None

    def get_soma_estimada_min(self, obj):
        return sum(item.atividade.duracao_estimada for item in obj.atividades.all() if item.atividade)

