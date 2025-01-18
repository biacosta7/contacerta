from django.urls import path
from . import views

urlpatterns = [
    path('cadastro/', views.criar_user, name='criar_user'),
    path('login/', views.login, name='login'),
]