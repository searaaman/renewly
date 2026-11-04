from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from .views import financial_year_start


class FinancialYearTests(TestCase):
    def test_financial_year_starts_on_1_april(self):
        self.assertEqual(financial_year_start(date(2026, 3, 31)), date(2025, 4, 1))
        self.assertEqual(financial_year_start(date(2026, 4, 1)), date(2026, 4, 1))

    @patch('django.utils.timezone.localdate', return_value=date(2026, 11, 5))
    def test_this_and_last_financial_year_views(self, _today):
        self.client.force_login(User.objects.create_user('staff'))

        current = self.client.get('/?period=fy').context
        self.assertEqual((current['start'], current['end']), (date(2026, 4, 1), date(2026, 11, 5)))
        self.assertEqual(current['fy_label'], 'FY 2026–27')
        self.assertEqual(len(current['revenue_labels']), 8)

        last = self.client.get('/?period=last_fy').context
        self.assertEqual((last['start'], last['end']), (date(2025, 4, 1), date(2026, 3, 31)))
        self.assertEqual(last['fy_label'], 'FY 2025–26')
        self.assertEqual(len(last['revenue_labels']), 12)
