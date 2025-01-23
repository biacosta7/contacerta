from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Despesas
    path('detalhes/<str:tipo>/<int:id>/criar-despesa/', views.criar_despesa, name='criar_despesa'),
    path('detalhes/atualizar-status/<int:despesa_id>/', views.atualizar_status, name='atualizar_status'),

    # Cartões
    path('cartoes/', views.ver_cartoes, name='cartoes'),
    path('cartoes/criar/', views.criar_cartao, name='criar_cartao'),

    # Aditivos
    #path('aditivos/', views.ver_aditivos, name='aditivos'),
    path('aditivos/criar/', views.criar_aditivo, name='criar_aditivo'),

    # Bancos
    #path('banco/', views.ver_banco, name='banco'),
    path('banco/criar/', views.criar_banco, name='criar_banco'),

    path('funcionario/criar/', views.criar_funcionario, name='criar_funcionario'),
]
