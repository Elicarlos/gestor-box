from django.contrib import admin
from django.urls import path, include
from core.views import (
    cadastrar_funcionario_view,
    cadastrar_filial_view,
    cadastrar_box_view,
    cadastrar_atividade_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.api_urls')),
    path('', include('core.urls')),  # Inclui as URLs principais do core
    path('cadastrar-funcionario/', cadastrar_funcionario_view, name='cadastrar_funcionario'),
    path('cadastrar-filial/', cadastrar_filial_view, name='cadastrar_filial'),
    path('cadastrar-box/', cadastrar_box_view, name='cadastrar_box'),
    path('cadastrar-atividade/', cadastrar_atividade_view, name='cadastrar_atividade'),
]
