from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    username = None 
    email = models.EmailField(unique=True)

    nome = models.CharField(max_length=150, blank=False)
    sobrenome = models.CharField(max_length=150, blank=False)

    USERNAME_FIELD = 'email'  # email como o campo principal de autenticação
    REQUIRED_FIELDS = ['nome', 'sobrenome', 'cargo'] 

    def __str__(self):
        return self.email
