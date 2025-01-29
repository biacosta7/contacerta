from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Despesas
    path('detalhes/<str:tipo>/<int:id>/criar-despesa/', views.criar_despesa, name='criar_despesa'),
    path('detalhes/atualizar-status/<int:despesa_id>/', views.atualizar_status, name='atualizar_status'),
    path('editar/despesa/<int:despesa_id>/', views.editar_despesa, name='editar_despesa'),
    path('deletar/despesa/<int:despesa_id>/', views.deletar_despesa, name='deletar_despesa'),

    # Cartões
    path('cartoes/', views.ver_cartoes, name='cartoes'),
    path('cartoes/criar/', views.criar_cartao, name='criar_cartao'),
    path('cartoes/editar/', views.editar_cartao, name='editar_cartao'),
    path('cartoes/deletar/', views.deletar_cartao, name='deletar_cartao'),

    # Aditivos
    #path('aditivos/', views.ver_aditivos, name='aditivos'),
    path('aditivos/criar/<int:id>', views.criar_aditivo, name='criar_aditivo'),

    # Bancos
    #path('banco/', views.ver_banco, name='banco'),
    path('banco/criar/', views.criar_banco, name='criar_banco'),

    path('funcionario/criar/', views.criar_funcionario, name='criar_funcionario'),
]
