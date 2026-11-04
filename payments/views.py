from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from subscriptions.models import Subscription

from .forms import PaymentForm
from .models import Payment


@login_required
def payment_list(request):
    subscriptions = (
        Subscription.objects.filter(cancelled_at__isnull=True)
        .select_related('client', 'plan')
        .prefetch_related('payments')
    )
    status = request.GET.get('status', '')
    if status:
        subscriptions = [s for s in subscriptions if s.payment_status == status]
    payments = Payment.objects.select_related('subscription__client', 'subscription__plan')
    return render(request, 'payments/list.html', {
        'subscriptions': subscriptions,
        'payments': payments,
        'status': status,
        'statuses': Subscription.PaymentStatus.choices,
    })


@login_required
def payment_form(request):
    form = PaymentForm(
        request.POST or None,
        initial={'subscription': request.GET.get('subscription')},
    )
    if request.method == 'POST' and form.is_valid():
    
        payment = form.save()
        messages.success(request, 'Payment recorded.')
        return redirect('clients:detail', pk=payment.subscription.client_id)
    return render(request, 'payments/form.html', {'form': form})