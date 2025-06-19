from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

def permission_required(perm):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Você precisa estar logado para acessar esta página.')
                return redirect('login')
            
            if request.user.is_superuser or request.user.has_perm(perm):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Você não tem permissão para acessar esta página.')
                return redirect('admin:index')
        return _wrapped_view
    return decorator

def admin_or_manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar logado para acessar esta página.')
            return redirect('login')
        
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Acesso restrito a administradores e gerentes.')
            return redirect('admin:index')
    return _wrapped_view 