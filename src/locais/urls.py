from django.urls import path
from . import views
from users import views as users_view

app_name = 'locais'

urlpatterns = [
    path('', users_view.login_user, name='login_user'),

    path('home/<int:escritorio_id>/', views.listar_obras, name='home'),
    path('criar/obra/<int:escritorio_id>/', views.criar_obra, name='criar_obra'),
    path('editar/obra/<int:obra_id>', views.editar_obra, name='editar_obra'),
    path('deletar/obra/<int:obra_id>', views.deletar_obra, name='deletar_obra'),
    path('detalhes/obra/<int:id>', views.detalhar_obra, name='detalhe_obra'),
    path("consultar-debito-mensal/<str:tipo>/<int:id>/", views.consultar_debito_mensal, name="consultar_debito_mensal"),

    path('hub/<int:user_id>/', views.acesso_hub, name='hub'),
    path('detalhes/escritorio/<int:escritorio_id>/', views.detalhar_escritorio, name='detalhe_escritorio'),
    path('criar/escritorio/<int:user_id>/', views.criar_escritorio, name='criar_escritorio'),
    path('enviar-acesso/escritorio/<int:escritorio_id>/', views.enviar_acesso_escritorio, name='enviar_acesso_escritorio'),
    
    path('responder-acesso/escritorio/<int:acesso_id>/<int:escritorio_id>/', views.responder_acesso_escritorio, name='responder_acesso_escritorio'),


]