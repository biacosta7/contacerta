from locais.models import Escritorio
from .models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as login_django, logout as logout_django
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout


def criar_user(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        sobrenome = request.POST.get('sobrenome')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        nome = nome.strip()
        sobrenome = sobrenome.strip()
        email = email.strip()
        password = password.strip()
        confirm_password = confirm_password.strip()

        form_data = {
            'nome': nome,
            'sobrenome': sobrenome,
            'email': email,
        }

        valid_name = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚáéíóúÃÕãõÇç")
        if not set(nome).issubset(valid_name):
            messages.error(request, 'O nome não deve conter números ou caracteres especiais')
            return render(request, 'users/cadastro.html', form_data)

        if ' ' in password:
            messages.error(request, 'A senha não pode conter espaços.')
            return render(request, 'users/cadastro.html', form_data)

        if '@' not in email or email.count('@') != 1:
            messages.error(request, 'Por favor, insira um email válido')
            return render(request, 'users/cadastro.html', form_data)

        if password == confirm_password:
            try:
                user = User(
                    nome=nome,
                    sobrenome=sobrenome,
                    email=email,
                )
                user.set_password(password)  # Criptografa a senha
                user.save()
                messages.success(request, 'Usuário criado com sucesso!')

                # Autentica o usuário recém-criado
                user = authenticate(request, email=email, password=password)  # Verifique se o username é 'email'
                if user is not None:
                    login(request, user)  # Faz login automaticamente
                    return redirect('locais:hub', user_id=user.id)  # Redireciona para a página desejada

            except IntegrityError:
                messages.error(request, 'Já existe um usuário com este email. Tente novamente.')
                return render(request, 'users/cadastro.html', form_data)
        else:
            return render(request, 'users/cadastro.html', {'error': 'As senhas não coincidem.'})
    else:
        return render(request, 'users/cadastro.html')
    
def login_user(request):
    if request.user.is_authenticated:
        escritorios = Escritorio.objects.filter(membros=request.user)
        if escritorios.exists():
            return redirect('locais:home', escritorio_id=escritorios.first().id)
        return redirect('locais:hub', request.user.id)

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        email = email.strip()
        password = password.strip()

        user = authenticate(email=email, password=password)

        if user:
            login_django(request, user)
            messages.success(request, 'Autenticado com sucesso.')

            # Verifica a qual escritório o usuário pertence
            escritorios = Escritorio.objects.filter(membros=user)

            if escritorios.exists():
                # Se houver mais de um escritório, direcionar para um específico ou permitir escolha
                escritorio = escritorios.first()  # Pegando o primeiro por padrão
                return redirect('locais:home', escritorio_id=escritorio.id)
            else:
                messages.warning(request, 'Você não está associado a nenhum escritório.')
                return redirect('locais:hub', user_id=user.id) 

        else:
            messages.error(request, 'Email ou senha inválidos. Tente novamente.')
            return render(request, 'users/login.html')
    
    return render(request, 'users/login.html')

    
def logout_user(request):
    logout(request)
    return redirect('login')

@login_required
def editar_user(request, user_id):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        sobrenome = request.POST.get('sobrenome', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        valid_name = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚáéíóúÃÕãõÇç")
        if not set(nome).issubset(valid_name):
            messages.error(request, 'O nome não deve conter números ou caracteres especiais')
            return redirect('locais:hub', user_id=user_id)

        if ' ' in password:
            messages.error(request, 'A senha não pode conter espaços.')
            return redirect('locais:hub', user_id=user_id)

        if '@' not in email or email.count('@') != 1:
            messages.error(request, 'Por favor, insira um email válido')
            return redirect('locais:hub', user_id=user_id)

        if password != confirm_password:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('locais:hub', user_id=user_id)
        
        try:
            user = User.objects.get(id=user_id)
            user.nome = nome
            user.sobrenome = sobrenome
            user.email = email
            user.set_password(password)
            user.save()

            messages.success(request, 'Dados atualizados com sucesso!')
            
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)                
                escritorios = Escritorio.objects.filter(membros=user)
                if escritorios.exists():
                    escritorio = escritorios.first()
                    return redirect('locais:home', escritorio_id=escritorio.id)
                else:
                    messages.warning(request, 'Você não está associado a nenhum escritório.')
                    return redirect('locais:hub', user_id=user.id)
        
        except User.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')
        except IntegrityError:
            messages.error(request, 'Já existe um usuário com este email. Tente novamente.')
        
        return redirect('locais:hub', user_id=user_id)
    
    try:
        user = User.objects.get(id=user_id)
        return redirect('locais:hub', user_id=user.id)
    except User.DoesNotExist:
        messages.error(request, 'Usuário não encontrado.')
        return redirect('locais:hub')
