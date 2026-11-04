from django.urls import path

from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.client_list, name='list'),
    path('new/', views.client_form, name='new'),
    path('<int:pk>/', views.client_detail, name='detail'),
    path('<int:pk>/edit/', views.client_form, name='edit'),
    path('<int:pk>/report.csv', views.client_report, name='report'),
]