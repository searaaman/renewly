from datetime import timedelta
from decimal import Decimal
from itertools import cycle

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from clients.models import Client
from payments.models import Payment
from subscriptions.models import Plan, Subscription

PLANS = {'Basic': 1500, 'Professional': 2400, 'Enterprise': 3600}

# Dates are days relative to today, so every status (expiring, overdue...) is correct on the day it is seeded.
# Each subscription: plan, licensed users, active users, start, end, due, [(payment day, amount)], extra fields.
# A client with two subscriptions has renewed: the second one links back to the first.
CLIENTS = [
    ('Malabar Traders', 'Arun Menon', 'Kozhikode', '32', 'active', [
        ('Professional', 50, 38, -200, 165, -190, [(-195, 60000), (-180, 30000), (-100, 30000)], {}),
    ]),
    ('Periyar Spices Exports', 'Latha Varghese', 'Kochi', '32', 'active', [
        ('Enterprise', 80, 72, -345, 19, -320, [(-330, 288000)], {}),
    ]),
    ('Anand Textiles', 'Vinod Anand', 'Thrissur', '32', 'active', [
        ('Professional', 30, 27, -340, 24, -310, [(-300, 40000)], {}),
    ]),
    ('Ananthapuri Hardware Mart', 'Suresh Nair', 'Thiruvananthapuram', '32', 'active', [
        ('Basic', 15, 11, -355, 9, -330, [(-335, 22500)], {}),
    ]),
    ('Coastal Marine Supplies', 'Joseph Fernandez', 'Kollam', '32', 'inactive', [
        ('Professional', 25, 25, -400, -35, -380, [(-390, 60000)], {}),
    ]),
    ('Nilgiri Foods', 'Priya Raman', 'Coimbatore', '33', 'active', [
        ('Enterprise', 60, 41, -420, -55, -400, [(-410, 216000)], {}),
        ('Enterprise', 60, 48, -54, 310, 30, [(-50, 108000), (-30, 54000)], {}),
    ]),
    ('Spice Route Retail', 'Rahul Shetty', 'Bengaluru', '29', 'active', [
        ('Professional', 40, 35, -290, 75, -270, [(-285, 48000), (-240, 48000)], {}),
    ]),
    ('Greenfield Agro Products', 'Kavya Gowda', 'Mysuru', '29', 'active', [
        ('Basic', 20, 14, -150, 214, -30, [(-148, 15000), (-60, 15000)], {}),
    ]),
    ('Chola Auto Parts', 'Senthil Kumar', 'Chennai', '33', 'active', [
        ('Enterprise', 100, 86, -90, 274, 40, [(-85, 180000)], {}),
    ]),
    ('Deccan Pharma Distributors', 'Farah Khan', 'Hyderabad', '36', 'active', [
        ('Professional', 45, 30, -20, 344, 10, [], {}),
    ]),
    ('Lakshmi Jewellers', 'Meera Krishnan', 'Palakkad', '32', 'active', [
        ('Basic', 10, 6, -30, 334, -10, [], {}),
    ]),
    ('Backwater Resorts', 'Thomas Kurian', 'Kottayam', '32', 'active', [
        ('Professional', 20, 0, 5, 369, 5, [], {'is_activated': False}),
    ]),
    ('Sahyadri Furniture', 'Nikhil Das', 'Kannur', '32', 'suspended', [
        ('Basic', 12, 9, -160, 204, -140, [(-155, 9000)], {'cancelled_days': -40}),
    ]),
    ('Western Ghats Logistics', 'Asha Mathew', 'Malappuram', '32', 'active', [
        ('Professional', 35, 33, -120, 244, -100, [(-118, 50000), (-2, 34000)], {}),
    ]),
    ('Cochin Paints', 'Rajesh Pillai', 'Ernakulam', '32', 'active', [
        ('Basic', 25, 19, -280, 85, -260, [(-270, 37500)], {}),
    ]),
]


class Command(BaseCommand):
    help = 'Load demo clients, subscriptions and payments once. Does nothing if they already exist.'

    @transaction.atomic
    def handle(self, *args, **options):
        if Client.objects.filter(company_name=CLIENTS[0][0]).exists():
            self.stdout.write('Demo data already loaded.')
            return

        today = timezone.localdate()
        day = lambda offset: today + timedelta(days=offset)
        methods = cycle(['neft', 'upi', 'neft', 'cheque', 'upi', 'card'])
        plans = {
            name: Plan.objects.get_or_create(name=name, defaults={'price_per_user': price})[0]
            for name, price in PLANS.items()
        }

        for n, (company, contact, city, state, status, subscriptions) in enumerate(CLIENTS, start=1):
            first_name = contact.split()[0].lower()
            domain = company.lower().replace(' ', '')
            client = Client(
                company_name=company,
                contact_person=contact,
                email=f'{first_name}@{domain}.example',
                phone=f'90000{n:05d}',
                city=city,
                gstin=f'{state}AABCR{n:04d}F1Z{n % 10}',
                status=status,
                onboarded_on=day(subscriptions[0][3]),
            )
            client.full_clean()
            client.save()

            previous = None
            for plan, licensed, active, start, end, due, payments, extra in subscriptions:
                cancelled = extra.get('cancelled_days')
                subscription = Subscription(
                    client=client,
                    plan=plans[plan],
                    start_date=day(start),
                    end_date=day(end),
                    licensed_users=licensed,
                    active_users=active,
                    amount=Decimal(licensed * PLANS[plan]),
                    due_date=day(due),
                    is_activated=extra.get('is_activated', True),
                    cancelled_at=day(cancelled) if cancelled else None,
                    renewed_from=previous,
                )
                subscription.full_clean()
                subscription.save()
                previous = subscription

                for paid_on, amount in payments:
                    payment = Payment(
                        subscription=subscription,
                        amount=Decimal(amount),
                        paid_on=day(paid_on),
                        method=next(methods),
                        txn_ref=f'TXN{n:02d}{abs(paid_on):04d}',
                    )
                    payment.full_clean()
                    payment.save()

        self.stdout.write(self.style.SUCCESS(f'Loaded {len(CLIENTS)} demo clients.'))
