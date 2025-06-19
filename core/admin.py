from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Funcionario, Filial, Box, Atividade, SessaoServico, SessaoAtividade

class FuncionarioInline(admin.StackedInline):
    model = Funcionario
    can_delete = False
    verbose_name_plural = 'Funcionário'

class CustomUserAdmin(UserAdmin):
    inlines = (FuncionarioInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_filial')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'funcionario__filial')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'funcionario__matricula')

    def get_filial(self, obj):
        if hasattr(obj, 'funcionario') and obj.funcionario.filial:
            return obj.funcionario.filial.nome
        return '-'
    get_filial.short_description = 'Filial'

@admin.register(Filial)
class FilialAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'uf')
    search_fields = ('nome', 'cidade')
    list_filter = ('uf',)

@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ('nome', 'localizacao', 'filial')
    search_fields = ('nome', 'localizacao')
    list_filter = ('filial',)

@admin.register(Atividade)
class AtividadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'duracao_estimada', 'filial')
    search_fields = ('nome',)
    list_filter = ('filial',)

@admin.register(SessaoServico)
class SessaoServicoAdmin(admin.ModelAdmin):
    list_display = ('box', 'funcionario', 'data_hora_inicio', 'data_hora_fim')
    list_filter = ('box__filial', 'funcionario__filial', 'data_hora_inicio')
    search_fields = ('box__nome', 'funcionario__user__username')
    date_hierarchy = 'data_hora_inicio'

@admin.register(SessaoAtividade)
class SessaoAtividadeAdmin(admin.ModelAdmin):
    list_display = ('sessao_servico', 'atividade', 'ordem')
    list_filter = ('atividade__filial',)
    search_fields = ('atividade__nome',)

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
