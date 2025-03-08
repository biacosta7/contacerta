from django.urls import path
from . import views

urlpatterns = [
    path('cadastro/', views.criar_user, name='criar_user'),
    path('editar-dados/<int:user_id>/', views.editar_user, name='editar_user'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),

]