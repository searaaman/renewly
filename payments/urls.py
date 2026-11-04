from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.payment_list, name='list'),
    path('new/', views.payment_form, name='new'),
]
