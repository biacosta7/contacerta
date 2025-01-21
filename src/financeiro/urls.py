from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('/criar/despesa/', views.criar_despesa, name='criar_despesa'),
    path('cartoes/', views.ver_cartoes, name='cartoes'),
    path('cartoes/criar/', views.criar_cartao, name='criar_cartao'),
    path('banco/criar/', views.criar_banco, name='criar_banco'),

]
