from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client


@login_required
def client_list(request):
    clients = Client.objects.all()
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    if query:
        clients = clients.filter(
            Q(company_name__icontains=query)
            | Q(client_code__icontains=query)
            | Q(contact_person__icontains=query)
        )
    if status:
        clients = clients.filter(status=status)
    return render(request, 'clients/list.html', {
        'clients': clients,
        'query': query,
        'status': status,
        'statuses': Client.Status.choices,
    })


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    subscriptions = client.subscriptions.select_related('plan')
    return render(request, 'clients/detail.html', {'client': client, 'subscriptions': subscriptions})

@login_required
def client_form(request, pk=None):
    client = get_object_or_404(Client, pk=pk) if pk else None
    form = ClientForm(request.POST or None, instance=client)
    if request.method == 'POST' and form.is_valid():
        client = form.save()
        messages.success(request, f'{client.company_name} saved.')
        return redirect('clients:detail', pk=client.pk)
    return render(request, 'clients/form.html', {'form': form, 'client': client})