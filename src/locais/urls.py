from django.urls import path
from . import views

app_name = 'locais'

urlpatterns = [
    path('', views.listar_obras, name='home'),
    path('criar/obra/', views.criar_obra, name='criar_obra'),
    path('editar/obra/<int:obra_id>', views.editar_obra, name='editar_obra'),
    path('deletar/obra/<int:obra_id>', views.deletar_obra, name='deletar_obra'),
    path('detalhes/obra/<int:id>', views.detalhar_obra, name='detalhe_obra'),
    path("consultar-debito-mensal/<int:id>/", views.consultar_debito_mensal, name="consultar_debito_mensal"),


    path('detalhes/escritorio/<int:id>', views.detalhar_escritorio, name='detalhe_escritorio'),
    path('criar/escritorio/', views.criar_escritorio, name='criar_escritorio'),
]