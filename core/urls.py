from django.urls import path, include
from .views import terminal_view, relatorio_view, alterar_senha_view, cadastrar_funcionario_view, logout_funcionario

urlpatterns = [
    path('', terminal_view, name='home'),  # Rota para a raiz
    path('terminal/', terminal_view, name='terminal'),
    path('relatorios/', relatorio_view, name='relatorio'),
    path('alterar-senha/', alterar_senha_view, name='alterar_senha'),
    path('cadastrar-funcionario/', cadastrar_funcionario_view, name='cadastrar_funcionario'),
    path('logout/', logout_funcionario, name='logout_funcionario'),
    path('api/', include('core.api_urls')),
]
