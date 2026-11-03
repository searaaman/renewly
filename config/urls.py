from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import  include,path

from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('clients/', include('clients.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', dashboard_views.dashboard, name='dashboard'),
]
