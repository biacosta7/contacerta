from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Despesas
    path('detalhes/<str:tipo>/<int:id>/criar-despesa/', views.criar_despesa, name='criar_despesa'),

    # Cartões
    path('cartoes/', views.ver_cartoes, name='cartoes'),
    path('cartoes/criar/', views.criar_cartao, name='criar_cartao'),

    # Bancos
    #path('banco/', views.ver_banco, name='banco'),
    path('banco/criar/', views.criar_banco, name='criar_banco'),
]
