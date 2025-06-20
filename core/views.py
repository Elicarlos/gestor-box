from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db import models

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

import paho.mqtt.publish as publish

from core.models import Funcionario, Box, Atividade, SessaoServico, SessaoAtividade, Filial
from .serializers import (
    FuncionarioSerializer, BoxSerializer, AtividadeSerializer,
    SessaoServicoSerializer, SessaoAtividadeSerializer
)
from .forms import FuncionarioForm, FilialForm, BoxForm, AtividadeForm
from .decorators import permission_required, admin_or_manager_required


# -------------------- VIEWS DE TEMPLATES --------------------

@login_required
def alterar_senha_view(request):
    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual')
        nova_senha = request.POST.get('nova_senha')
        nova_senha2 = request.POST.get('nova_senha2')

        # Validações
        if not request.user.check_password(senha_atual):
            messages.error(request, 'Senha atual incorreta.')
        elif nova_senha != nova_senha2:
            messages.error(request, 'As novas senhas não coincidem.')
        elif not nova_senha:
            messages.error(request, 'Nova senha não pode ser vazia.')
        elif len(nova_senha) < 8:
            messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
        elif not any(c.isalpha() for c in nova_senha):
            messages.error(request, 'A nova senha deve conter pelo menos uma letra.')
        elif not any(c.isdigit() for c in nova_senha):
            messages.error(request, 'A nova senha deve conter pelo menos um número.')
        elif nova_senha == senha_atual:
            messages.error(request, 'A nova senha não pode ser igual à senha atual.')
        else:
            try:
                # Validar a força da senha
                from django.contrib.auth.password_validation import validate_password
                validate_password(nova_senha, request.user)
                
                # Se passou em todas as validações, altera a senha
                request.user.set_password(nova_senha)
                request.user.save()
                messages.success(request, 'Senha alterada com sucesso! Faça login novamente.')
                logout(request)
                return redirect('login')
            except Exception as e:
                messages.error(request, str(e))
    return render(request, 'alterar_senha.html')

@staff_member_required
def cadastrar_funcionario_view(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário cadastrado com sucesso.')
            return redirect('admin:index')
    else:
        form = FuncionarioForm()
    return render(request, 'cadastrar_funcionario.html', {'form': form})

@admin_or_manager_required
@permission_required('core.add_filial')
def cadastrar_filial_view(request):
    if request.method == 'POST':
        form = FilialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Filial cadastrada com sucesso.')
            return redirect('admin:index')
    else:
        form = FilialForm()
    return render(request, 'cadastrar_filial.html', {'form': form})

@admin_or_manager_required
@permission_required('core.add_box')
def cadastrar_box_view(request):
    if request.method == 'POST':
        form = BoxForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Box cadastrado com sucesso.')
            return redirect('admin:index')
    else:
        form = BoxForm()
    return render(request, 'cadastrar_box.html', {'form': form})

@admin_or_manager_required
@permission_required('core.add_atividade')
def cadastrar_atividade_view(request):
    if request.method == 'POST':
        form = AtividadeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atividade cadastrada com sucesso.')
            return redirect('admin:index')
    else:
        form = AtividadeForm()
    return render(request, 'cadastrar_atividade.html', {'form': form})

def terminal_view(request):
    """
    View para o terminal de box.
    Renderiza a página inicial do terminal onde o usuário pode selecionar um box
    e fazer login com sua matrícula.
    """
    return render(request, 'terminal.html')

@staff_member_required
def relatorio_view(request):
    return render(request, 'relatorio.html')


# -------------------- APIs REST --------------------

class FuncionarioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        matricula = self.request.query_params.get('matricula')
        if matricula:
            return self.queryset.filter(matricula=matricula)
        return self.queryset.none()

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_funcionario(request):
    matricula = request.data.get('matricula')
    senha = request.data.get('senha') 
    try:
        func = Funcionario.objects.get(matricula=matricula)
        user = func.user
    except Funcionario.DoesNotExist:
        return Response({'detail': 'Matrícula não encontrada.'}, status=status.HTTP_401_UNAUTHORIZED)

    # Check if the user is active
    if not user.is_active:
        return Response({'detail': 'Usuário inativo.'}, status=status.HTTP_401_UNAUTHORIZED)

    # Re-enable password check
    authenticated_user = authenticate(request, username=user.username, password=senha)
    if authenticated_user is not None:
        # Autentica a sessão Django também
        login(request, authenticated_user)
    else:
        return Response({'detail': 'Credenciais inválidas'}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'id': func.id,
            'nome_completo': user.get_full_name() or user.username,
            'matricula': func.matricula,
            'box_nome': func.filial.nome if func.filial else 'N/A',
        }
    })

class AtividadeViewSet(viewsets.ModelViewSet):
    queryset = Atividade.objects.all()
    serializer_class = AtividadeSerializer
    permission_classes = [permissions.IsAuthenticated]

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

class RelatorioAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request, *args, **kwargs):
        from datetime import datetime, time
        start_str = request.query_params.get('inicio')
        end_str = request.query_params.get('fim')
        if not start_str or not end_str:
            return Response({'detail': 'Datas de início e fim são obrigatórias.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'detail': 'Formato de data inválido. Use AAAA-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        # Converte para aware
        from django.utils import timezone
        start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
        end_dt   = timezone.make_aware(datetime.combine(end_date,   time.max))

        qs = SessaoServico.objects.filter(data_hora_inicio__gte=start_dt, data_hora_inicio__lte=end_dt).order_by('-data_hora_inicio')
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = SessaoServicoSerializer(page or qs, many=True)
        return paginator.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)

class VerificarSessaoAtivaView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, *args, **kwargs):
        try:
            # Ensure func is always available if authenticated
            func = request.user.funcionario
            
            response_data = {
                'sessao_id': None,
                'box_id': None,
                'box_name': None,
                'data_hora_inicio': None,
                'atividades': [],
                'user': {
                    'id': func.id,
                    'nome_completo': func.user.get_full_name() or func.user.username,
                    'matricula': func.matricula,
                }
            }

            sessao = SessaoServico.objects.filter(funcionario=func, data_hora_fim__isnull=True).order_by('-data_hora_inicio').first()
            
            if sessao:
                atividades = SessaoAtividade.objects.filter(sessao_servico=sessao)
                response_data['active_session'] = {
                    'id': sessao.id,
                    'box_id': sessao.box.id,
                    'box_nome': sessao.box.nome,
                    'data_hora_inicio': sessao.data_hora_inicio,
                    'atividades': SessaoAtividadeSerializer(atividades, many=True).data,
                    'sessao_id': sessao.id, # Redundant but kept for safety
                }
            else:
                response_data['active_session'] = None
            
            return Response(response_data)
            
        except Funcionario.DoesNotExist:
            return Response({'detail': 'Perfil de funcionário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e: # Catch generic exceptions to log them
            print(f"Erro ao verificar sessão ativa: {e}") # Log the specific error
            return Response({'detail': 'Erro interno ao verificar sessão ativa.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BoxViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Box.objects.all()
    serializer_class = BoxSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='atividades-disponiveis', permission_classes=[permissions.IsAuthenticated], authentication_classes=[JWTAuthentication])
    def atividades_disponiveis(self, request):
        func = request.user.funcionario
        # Seleciona a sessão ativa mais recente (caso existam múltiplas abertas por engano)
        sess = SessaoServico.objects.filter(funcionario=func, data_hora_fim__isnull=True).order_by('-data_hora_inicio').first()
        if not sess:
            qs = Atividade.objects.all()
        else:
            used = SessaoAtividade.objects.filter(sessao_servico=sess).values_list('atividade_id', flat=True)
            qs = Atividade.objects.exclude(id__in=used)
        return Response(AtividadeSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='sessao-servico/iniciar', permission_classes=[permissions.IsAuthenticated], authentication_classes=[JWTAuthentication])
    def iniciar_sessao(self, request, pk=None):
        box = self.get_object()
        func = request.user.funcionario
        if SessaoServico.objects.filter(funcionario=func, data_hora_fim__isnull=True).exists():
            return Response({'detail': 'Sessão já em andamento.'}, status=status.HTTP_409_CONFLICT)
        ids = request.data.get('atividades', [])
        if not ids:
            return Response({'detail': 'Informe atividades.'}, status=status.HTTP_400_BAD_REQUEST)
        sess = SessaoServico.objects.create(box=box, funcionario=func)
        for i, atv_id in enumerate(ids, start=1):
            SessaoAtividade.objects.create(sessao_servico=sess, atividade_id=atv_id, ordem=i)
        # publish.single(f"boxes/{box.id}/light", 'red', hostname='localhost')
        return Response(SessaoServicoSerializer(sess).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='sessao-servico/finalizar', permission_classes=[permissions.IsAuthenticated], authentication_classes=[JWTAuthentication])
    def finalizar_sessao(self, request, pk=None):
        box = self.get_object()
        func = request.user.funcionario
        sess_id = request.data.get('sessao_id')
        if not sess_id:
            return Response({'detail': 'sessao_id obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        sess = get_object_or_404(SessaoServico, id=sess_id, box=box, funcionario=func)
        if sess.data_hora_fim:
            return Response({'detail': 'Sessão já finalizada.'}, status=status.HTTP_400_BAD_REQUEST)
        sess.data_hora_fim = timezone.now()
        sess.save()
        # publish.single(f"boxes/{box.id}/light", 'green', hostname='localhost')
        return Response({'status': 'finalizado'})

    @action(detail=True, methods=['post'], url_path='sessao-servico/adicionar-atividades', permission_classes=[permissions.IsAuthenticated], authentication_classes=[JWTAuthentication])
    def adicionar_atividades(self, request, pk=None):
        box = self.get_object()
        func = request.user.funcionario
        sess = SessaoServico.objects.filter(
            funcionario=func,
            box=box,
            data_hora_fim__isnull=True
        ).first()
        if not sess:
            return Response({'detail': 'Nenhuma sessão ativa neste box.'}, status=status.HTTP_404_NOT_FOUND)
        ids = request.data.get('atividades', [])
        if not ids:
            return Response({'detail': 'Informe atividades.'}, status=status.HTTP_400_BAD_REQUEST)
        from django.db.models import Max
        existing = set(SessaoAtividade.objects.filter(sessao_servico=sess).values_list('atividade_id', flat=True))
        ordem = SessaoAtividade.objects.filter(sessao_servico=sess).aggregate(Max('ordem'))['ordem__max'] or 0
        added = []
        for atv_id in ids:
            if atv_id not in existing:
                ordem += 1
                SessaoAtividade.objects.create(sessao_servico=sess, atividade_id=atv_id, ordem=ordem)
                added.append(atv_id)
        if not added:
            return Response({'detail': 'Nenhuma atividade nova adicionada.'})
        return Response({'detail': f'Atividades adicionadas: {added}'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def relatorio_sessoes(request):
    inicio = request.GET.get('inicio')
    fim = request.GET.get('fim')
    qs = SessaoServico.objects.filter(data_hora_inicio__date__gte=inicio, data_hora_inicio__date__lte=fim)
    data = []
    for sess in qs:
        atvs = sess.atividades.all()
        soma = sum(sa.atividade.duracao_estimada for sa in atvs)
        real = None
        if sess.data_hora_fim:
            real = int((sess.data_hora_fim - sess.data_hora_inicio).total_seconds() // 60)
        data.append({
            'id': sess.id,
            'funcionario': sess.funcionario.user.get_full_name() or sess.funcionario.matricula,
            'box': sess.box.nome,
            'data_hora_inicio': sess.data_hora_inicio,
            'data_hora_fim': sess.data_hora_fim,
            'duracao_real': real,
            'soma_duracoes_atividades': soma,
            'atividades': [
                {'nome': sa.atividade.nome, 'duracao_estimada': sa.atividade.duracao_estimada, 'ordem': sa.ordem}
                for sa in atvs
            ]
        })
    return Response(data)

def logout_funcionario(request):
    logout(request)
    return redirect('/terminal/')
