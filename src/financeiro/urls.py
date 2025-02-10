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
    path('cartoes/', views.fatura_mensal_cartoes, name='cartoes'),

    path('cartoes/criar/', views.criar_cartao, name='criar_cartao'),
    path('cartoes/editar/<int:cartao_id>/', views.editar_cartao, name='editar_cartao'),
    path('cartoes/deletar/<int:cartao_id>/', views.deletar_cartao, name='deletar_cartao'),

    path('cartoes/editar-fatura/', views.editar_fatura, name='editar_fatura'),

    path('cartoes/pagar-fatura/<int:cartao_id>/', views.pagar_cartao, name='pagar_cartao'),

    # Aditivos
    path('aditivos/criar/<int:id>', views.criar_aditivo, name='criar_aditivo'),
    path('aditivos/editar/<int:aditivo_id>/', views.editar_aditivo, name='editar_aditivo'),
    path('aditivos/deletar/<int:aditivo_id>/', views.deletar_aditivo, name='deletar_aditivo'),

    # Adiantamentos
    path('adiantamentos/criar/<int:id>', views.criar_adiantamento, name='criar_adiantamento'),
    path('adiantamentos/editar/<int:adiantamento_id>/', views.editar_adiantamento, name='editar_adiantamento'),
    path('adiantamentos/deletar/<int:adiantamento_id>/', views.deletar_adiantamento, name='deletar_adiantamento'),

    # BMs
    path('bms/criar/<int:id>', views.criar_bm, name='criar_bm'),
    path('bms/editar/<int:bm_id>/', views.editar_bm, name='editar_bm'),
    path('bms/deletar/<int:bm_id>/', views.deletar_bm, name='deletar_bm'),

    path('debito-mensal/<int:id>/<str:ano>/<str:mes>/', views.get_debito_mensal, name='get_debito_mensal'),

    # Bancos
    #path('banco/', views.ver_banco, name='banco'),
    path('banco/criar/', views.criar_banco, name='criar_banco'),

    path('funcionario/criar/', views.criar_funcionario, name='criar_funcionario'),
]
