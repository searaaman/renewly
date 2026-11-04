from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clients.models import Client

from .models import Plan, Subscription


def make_subscription(client, plan, days_left, **fields):
    today = timezone.localdate()
    end = today + timedelta(days=days_left)
    defaults = {
        'start_date': end - timedelta(days=365),
        'end_date': end,
        'licensed_users': 50,
        'active_users': 38,
        'amount': 120000,
        'due_date': today + timedelta(days=30),
    }
    return Subscription.objects.create(client=client, plan=plan, **{**defaults, **fields})


class SubscriptionDetailsTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user('staff'))
        self.company = Client.objects.create(
            company_name='Test Co', contact_person='Asha', email='a@test.example',
            phone='9000000001', city='Kochi', onboarded_on=date(2026, 1, 1),
        )
        self.plan = Plan.objects.create(name='Basic', price_per_user=1500)
        self.bigger_plan = Plan.objects.create(name='Enterprise', price_per_user=3600)

    def test_duration_and_renewal_date(self):
        cases = [(365, '1 year'), (730, '2 years'), (182, '6 months'), (30, '1 month'), (14, '14 days'), (1, '1 day')]
        for days, label in cases:
            start = date(2026, 1, 1)
            subscription = Subscription(start_date=start, end_date=start + timedelta(days=days))
            self.assertEqual(subscription.duration, label)
        self.assertEqual(Subscription(end_date=date(2026, 12, 31)).renewal_date, date(2027, 1, 1))

    def test_renewals_page_lists_only_subscriptions_to_follow_up(self):
        expired = make_subscription(self.company, self.plan, -5)
        expiring = make_subscription(self.company, self.plan, 30)
        upcoming = make_subscription(self.company, self.plan, 90)
        far_off = make_subscription(self.company, self.plan, 91)
        cancelled = make_subscription(self.company, self.plan, 10, cancelled_at=timezone.localdate())
        pending = make_subscription(self.company, self.plan, 10, is_activated=False)
        already_renewed = make_subscription(self.company, self.plan, 5)
        renewal = make_subscription(self.company, self.plan, 370, renewed_from=already_renewed)

        listed = list(self.client.get(reverse('subscriptions:renewals')).context['subscriptions'])

        self.assertEqual(listed, [expired, expiring, upcoming])
        for excluded in (far_off, cancelled, pending, already_renewed, renewal):
            self.assertNotIn(excluded, listed)

    def test_renewal_shows_what_changed(self):
        old = make_subscription(self.company, self.plan, -5)
        make_subscription(
            self.company, self.bigger_plan, 360,
            licensed_users=60, amount=216000, renewed_from=old,
        )
        page = self.client.get(reverse('subscriptions:list')).content.decode()
        self.assertIn('Plan: Basic → Enterprise', page)
        self.assertIn('Licenses: 50 → 60', page)
        self.assertIn('Amount: ₹1,20,000 → ₹2,16,000', page)

    def test_unchanged_renewal_shows_no_changes(self):
        old = make_subscription(self.company, self.plan, -5)
        make_subscription(self.company, self.plan, 360, renewed_from=old)
        page = self.client.get(reverse('subscriptions:list')).content.decode()
        self.assertNotIn('Plan: ', page)
        self.assertNotIn('Licenses: ', page)
        self.assertNotIn('Amount: ', page)
