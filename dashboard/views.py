
from collections import Counter
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from clients.models import Client
from payments.models import Payment
from subscriptions.models import Subscription


@login_required
def dashboard(request):
    Status = Subscription.Status
    PaymentStatus = Subscription.PaymentStatus
    subscriptions = list(
        Subscription.objects.select_related('client', 'plan').prefetch_related('payments', 'renewals')
    )
    live = [s for s in subscriptions if s.status != Status.CANCELLED]
    in_force = [s for s in live if s.status in (Status.ACTIVE, Status.EXPIRING_SOON)]
    not_renewed = [s for s in live if not s.renewals.all()]
    overdue = [s for s in live if s.payment_status == PaymentStatus.OVERDUE]
    pending = [s for s in live if s.payment_status in (PaymentStatus.PENDING, PaymentStatus.PARTIAL)]

    today = timezone.localdate()
    months = []
    for i in range(11, -1, -1):
        year, month = divmod(today.year * 12 + today.month - 1 - i, 12)
        months.append(date(year, month + 1, 1))
    rows = (
        Payment.objects.filter(paid_on__gte=months[0])
        .annotate(month=TruncMonth('paid_on'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by()
    )
    revenue = {row['month']: row['total'] for row in rows}
    revenue_values = [float(revenue.get(m, 0)) for m in months]

    client_counts = Counter(Client.objects.values_list('status', flat=True))
    status_counts = Counter(s.status.value for s in subscriptions)

    return render(request, 'dashboard/index.html', {
        'client_total': sum(client_counts.values()),
        'client_counts': client_counts,
        'status_counts': status_counts,
        'licensed_users': sum(s.licensed_users for s in in_force),
        'active_users': sum(s.active_users for s in in_force),
        'total_value': sum(s.amount for s in live),
        'collected': Payment.objects.aggregate(total=Sum('amount'))['total'] or 0,
        'outstanding': sum(s.outstanding for s in live),
        'pending_amount': sum(s.outstanding for s in pending),
        'overdue_amount': sum(s.outstanding for s in overdue),
        'revenue_this_month': revenue_values[-1],
        'revenue_year': sum(revenue_values),
        'expiring': [s for s in not_renewed if s.status == Status.EXPIRING_SOON],
        'expired': [s for s in not_renewed if s.status == Status.EXPIRED],
        'upcoming': [s for s in not_renewed if s.status == Status.ACTIVE and s.days_left <= 90],
        'overdue': sorted(overdue, key=lambda s: s.due_date),
        'pending_payments': sorted(pending, key=lambda s: s.due_date),
        'revenue_labels': [m.strftime('%b %y') for m in months],
        'revenue_values': revenue_values,
        'status_labels': [label for _, label in Status.choices],
        'status_values': [status_counts[value] for value, _ in Status.choices],
    })