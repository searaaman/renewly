from django.urls import path

from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.subscription_list, name='list'),
    path('new/', views.subscription_form, name='new'),
    path('<int:pk>/edit/', views.subscription_form, name='edit'),
    path('<int:pk>/renew/', views.subscription_renew, name='renew'),
    path('<int:pk>/cancel/', views.subscription_cancel, name='cancel'),
]
