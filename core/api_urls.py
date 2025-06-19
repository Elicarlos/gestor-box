from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FuncionarioViewSet,
    BoxViewSet,
    AtividadeViewSet,
    login_funcionario,
    RelatorioAPIView,
    VerificarSessaoAtivaView,
    cadastrar_filial_view,
    cadastrar_box_view,
    cadastrar_atividade_view
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'funcionarios', FuncionarioViewSet, basename='funcionario')
router.register(r'boxes', BoxViewSet, basename='box')
router.register(r'atividades', AtividadeViewSet, basename='atividade')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', login_funcionario, name='api_login'),
    path('relatorios/', RelatorioAPIView.as_view(), name='api_relatorio'),
    path('verificar-sessao/', VerificarSessaoAtivaView.as_view(), name='verificar_sessao_ativa'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cadastrar-filial/', cadastrar_filial_view, name='cadastrar_filial'),
    path('cadastrar-box/', cadastrar_box_view, name='cadastrar_box'),
    path('cadastrar-atividade/', cadastrar_atividade_view, name='cadastrar_atividade'),
]
