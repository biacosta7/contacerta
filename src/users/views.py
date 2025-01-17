from .models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as login_django, logout as logout_django
from django.db import IntegrityError

def criar_user(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        sobrenome = request.POST.get('sobrenome')
        email = request.POST.get('email')
        cargo = request.POST.get('cargo')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        form_data = {
            'nome': nome,
            'sobrenome': sobrenome,
            'email': email,
            'cargo': cargo,
        }

        valid_name = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ")
        if not set(nome).issubset(valid_name):
            messages.error(request, 'O nome não deve conter números ou caracteres especiais')
            return render(request, 'cadastro.html', form_data)

        if ' ' in password:
            messages.error(request, 'A senha não pode conter espaços.')
            return render(request, 'cadastro.html', form_data)

        if '@' not in email or email.count('@') != 1:
            messages.error(request, 'Por favor, insira um email válido')
            return render(request, 'cadastro.html', form_data)

        if password == confirm_password:
            try:
                user = User.objects.create_user(
                    nome=nome,
                    sobrenome=sobrenome,
                    email=email,
                    cargo=cargo,
                    password=password
                )
                user.save()
                return redirect('login')
            except IntegrityError:
                messages.error(request, 'Já existe um usuário com este email. Tente novamente.')
                return render(request, 'cadastro.html', form_data)
        else:
            return render(request, 'cadastro.html', {'error': 'As senhas não coincidem.'})
    else:
        return render(request, 'cadastro.html')