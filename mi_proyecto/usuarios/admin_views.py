from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import AdminUserForm


def superuser_required(view_func):
    @wraps(view_func)
    @login_required(login_url='login')
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            return HttpResponseForbidden('Solo el administrador principal puede gestionar cuentas.')
        return view_func(request, *args, **kwargs)
    return wrapped


@never_cache
@superuser_required
def admin_users(request):
    query = request.GET.get('q', '').strip()
    role = request.GET.get('rol', '')
    status = request.GET.get('estado', '')
    users = User.objects.order_by('-date_joined', '-pk')
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
    if role == 'admin':
        users = users.filter(Q(is_superuser=True) | Q(is_staff=True))
    elif role == 'customer':
        users = users.filter(is_superuser=False, is_staff=False)
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)

    page_obj = Paginator(users, 25).get_page(request.GET.get('page'))
    context = {
        'users': page_obj.object_list,
        'page_obj': page_obj,
        'query': query,
        'role': role,
        'status': status,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'admin_users': User.objects.filter(Q(is_superuser=True) | Q(is_staff=True)).count(),
    }
    return render(request, 'usuarios/admin_users.html', context)


@never_cache
@superuser_required
def admin_user_create(request):
    form = AdminUserForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'La cuenta se creó correctamente.')
        return redirect('admin_users')
    return render(request, 'usuarios/admin_user_form.html', {'form': form, 'creating': True})


@never_cache
@superuser_required
def admin_user_edit(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    can_change_role = target.pk != request.user.pk
    form = AdminUserForm(
        request.POST or None,
        instance=target,
        allow_role_change=can_change_role,
    )
    if request.method == 'POST' and form.is_valid():
        selected_admin = form.cleaned_data['is_admin'] == 'admin'
        with transaction.atomic():
            if target.is_superuser and not selected_admin:
                remaining_admins = User.objects.select_for_update().filter(is_superuser=True).count()
                if remaining_admins <= 1:
                    form.add_error('is_admin', 'Debe quedar al menos un administrador principal.')
                else:
                    form.save()
            else:
                form.save()
        if not form.errors:
            messages.success(request, 'Los cambios de la cuenta quedaron guardados.')
            return redirect('admin_users')
    return render(request, 'usuarios/admin_user_form.html', {
        'form': form,
        'creating': False,
        'target': target,
        'can_change_role': can_change_role,
    })


@never_cache
@superuser_required
@require_POST
def admin_user_delete(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.pk == request.user.pk:
        messages.error(request, 'No puedes eliminar la cuenta con la que tienes iniciada sesión.')
        return redirect('admin_users')

    with transaction.atomic():
        if target.is_superuser:
            remaining_admins = User.objects.select_for_update().filter(is_superuser=True).count()
            if remaining_admins <= 1:
                messages.error(request, 'Debe quedar al menos un administrador principal.')
                return redirect('admin_users')
        try:
            target.delete()
            messages.success(request, 'La cuenta se eliminó correctamente.')
        except ProtectedError:
            messages.error(
                request,
                'Esta cuenta tiene pedidos asociados y no se puede borrar sin perder el historial. '
                'Puedes desactivarla desde Editar usuario.',
            )
    return redirect('admin_users')
