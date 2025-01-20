from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('criar/despesa/', views.criar_despesa, name='criar_despesa'),
]
