import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client
from payments.models import Payment
from subscriptions.models import Subscription


@login_required
def client_list(request):
    clients = Client.objects.all()
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    payment_status = request.GET.get('payment_status', '')
    if query:
        clients = clients.filter(
            Q(company_name__icontains=query)
            | Q(client_code__icontains=query)
            | Q(contact_person__icontains=query)
        )
    if status:
        clients = clients.filter(status=status)
    if payment_status:
        subscriptions = Subscription.objects.filter(cancelled_at__isnull=True).prefetch_related('payments')
        clients = clients.filter(pk__in={s.client_id for s in subscriptions if s.payment_status == payment_status})
    return render(request, 'clients/list.html', {
        'clients': clients,
        'query': query,
        'status': status,
        'statuses': Client.Status.choices,
        'payment_status': payment_status,
        'payment_statuses': Subscription.PaymentStatus.choices,
    })


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    subscriptions = client.subscriptions.select_related('plan', 'renewed_from__plan').prefetch_related('payments')
    payments = Payment.objects.filter(subscription__client=client).select_related('subscription__plan')
    return render(request, 'clients/detail.html', {
        'client': client,
        'subscriptions': subscriptions,
        'payments': payments,
    })


def csv_text(value):
    """Stops a spreadsheet treating text a user typed, such as =SUM(...), as a formula."""
    return f"'{value}" if str(value)[:1] in ('=', '+', '-', '@') else value


@login_required
def client_report(request, pk):
    client = get_object_or_404(Client, pk=pk)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{client.client_code}-report.csv"'
    response.write('﻿')  # lets Excel detect UTF-8
    writer = csv.writer(response)

    writer.writerow(['Client', csv_text(client.company_name)])
    writer.writerow(['Code', client.client_code])
    writer.writerow(['Status', client.get_status_display()])
    writer.writerow(['Contact', csv_text(client.contact_person), client.email, client.phone])
    writer.writerow([])

    writer.writerow([
        'Plan', 'Start', 'End', 'Duration', 'Renewal date', 'Licensed users', 'Active users', 'Available licenses',
        'Amount (INR)', 'Paid (INR)', 'Outstanding (INR)', 'Status', 'Payment status', 'Renewal of',
    ])
    for s in client.subscriptions.select_related('plan', 'renewed_from__plan').prefetch_related('payments'):
        cancelled = s.status == Subscription.Status.CANCELLED
        writer.writerow([
            csv_text(s.plan), s.start_date, s.end_date, s.duration, s.renewal_date,
            s.licensed_users, s.active_users, s.available_licenses,
            s.amount, s.amount_paid, s.outstanding, s.status.label,
            '' if cancelled else s.payment_status.label,
            f'{s.renewed_from.plan} ending {s.renewed_from.end_date}' if s.renewed_from_id else '',
        ])
    writer.writerow([])

    writer.writerow(['Payment date', 'Plan', 'Method', 'Reference', 'Amount (INR)'])
    payments = Payment.objects.filter(subscription__client=client).select_related('subscription__plan')
    for p in payments:
        writer.writerow([p.paid_on, csv_text(p.subscription.plan), p.get_method_display(), csv_text(p.txn_ref), p.amount])
    return response


@login_required
def client_form(request, pk=None):
    client = get_object_or_404(Client, pk=pk) if pk else None
    form = ClientForm(request.POST or None, instance=client)
    if request.method == 'POST' and form.is_valid():
        client = form.save()
        messages.success(request, f'{client.company_name} saved.')
        return redirect('clients:detail', pk=client.pk)
    return render(request, 'clients/form.html', {'form': form, 'client': client})