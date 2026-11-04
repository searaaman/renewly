from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from payments.models import Payment
from subscriptions.models import Plan, Subscription

from .models import Client


class ClientReportTests(TestCase):
    def setUp(self):
        self.company = Client.objects.create(
            company_name='=Malabar', contact_person='Arun', email='a@test.example',
            phone='9000000001', city='Kochi', onboarded_on=date(2026, 1, 1),
        )
        today = timezone.localdate()
        subscription = Subscription.objects.create(
            client=self.company, plan=Plan.objects.create(name='Basic', price_per_user=1500),
            start_date=today - timedelta(days=100), end_date=today + timedelta(days=265),
            licensed_users=10, active_users=8, amount=15000, due_date=today + timedelta(days=10),
        )
        Payment.objects.create(subscription=subscription, amount=5000, paid_on=today, method='neft', txn_ref='TXN-1')
        self.url = reverse('clients:report', args=[self.company.pk])

    def test_requires_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_report_contains_subscriptions_and_payments(self):
        self.client.force_login(User.objects.create_user('staff'))
        response = self.client.get(self.url)
        body = response.content.decode()

        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn(f'{self.company.client_code}-report.csv', response['Content-Disposition'])
        self.assertIn('1 year', body)
        self.assertIn('10000.00', body)
        self.assertIn('Partially Paid', body)
        self.assertIn('TXN-1', body)

    def test_text_cannot_run_as_a_spreadsheet_formula(self):
        self.client.force_login(User.objects.create_user('staff'))
        self.assertIn("'=Malabar", self.client.get(self.url).content.decode())
