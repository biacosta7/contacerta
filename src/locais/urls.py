from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_obras, name='home'),
    path('criar/obra/', views.criar_obra, name='criar_obra'),
    path('criar/escritorio/', views.criar_escritorio, name='criar_escritorio'),
]