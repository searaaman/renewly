from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import SubscriptionForm
from .models import Subscription


@login_required
def subscription_list(request):
    subscriptions = Subscription.objects.select_related('client', 'plan')
    if request.GET.get('sort') == 'latest':
        subscriptions = subscriptions.order_by('-end_date')
    status = request.GET.get('status', '')
    if status:
        # ponytail: status is computed in Python, fine for ZcaleUp's ~15 clients; move into the query if this grows to thousands
        subscriptions = [s for s in subscriptions if s.status == status]
    return render(request, 'subscriptions/list.html', {
        'subscriptions': subscriptions,
        'status': status,
        'statuses': Subscription.Status.choices,
        'sort': request.GET.get('sort', ''),
    })


@login_required
def subscription_form(request, pk=None):
    subscription = get_object_or_404(Subscription, pk=pk) if pk else None
    form = SubscriptionForm(
        request.POST or None,
        instance=subscription,
        initial={'client': request.GET.get('client')},
    )
    if request.method == 'POST' and form.is_valid():
        subscription = form.save()
        messages.success(request, 'Subscription saved.')
        return redirect('clients:detail', pk=subscription.client_id)
    return render(request, 'subscriptions/form.html', {'form': form, 'subscription': subscription})


@login_required
@require_POST
def subscription_renew(request, pk):
    old = get_object_or_404(Subscription, pk=pk)
    start = old.end_date + timedelta(days=1)
    new = Subscription.objects.create(
        client=old.client,
        plan=old.plan,
        start_date=start,
        end_date=start + (old.end_date - old.start_date),
        licensed_users=old.licensed_users,
        active_users=old.active_users,
        amount=old.amount,
        due_date=start,
        renewed_from=old,
    )
    messages.success(request, 'Renewal created. Review the dates and amount.')
    return redirect('subscriptions:edit', pk=new.pk)


@login_required
@require_POST
def subscription_cancel(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)
    subscription.cancelled_at = timezone.localdate()
    subscription.save(update_fields=['cancelled_at'])
    messages.success(request, 'Subscription cancelled.')
    return redirect('clients:detail', pk=subscription.client_id)