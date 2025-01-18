from django.shortcuts import redirect, render
from django.contrib import messages
from locais.models import Obra, Escritorio
from datetime import datetime

def criar_obra(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        local = request.POST.get('local')
        data_inicio = request.POST.get('data_inicio')
        data_final = request.POST.get('data_final')
        valor_inicial = request.POST.get('valor_inicial')
        prazo_inicial = request.POST.get('prazo_inicial')

        # Converter as datas do formato dd/mm/yyyy para yyyy-mm-dd
        try:
            data_inicio = datetime.strptime(data_inicio, '%d/%m/%Y').date()
            prazo_inicial = datetime.strptime(prazo_inicial, '%d/%m/%Y').date()
            if data_final:  # Verifica se a data final não está vazia
                data_final = datetime.strptime(data_final, '%d/%m/%Y').date()
            else:
                data_final = None  # Caso a data_final esteja vazia
        except ValueError:
            messages.error(request, 'Formato de data inválido. Use o formato dd/mm/yyyy.')
            return redirect('home')

        if Obra.objects.filter(nome=nome).exists():
            messages.error(request, 'Já existe uma obra com esse nome.')
            return redirect('home')

        obra = Obra.objects.create(
            nome=nome,
            local=local,
            data_inicio=data_inicio,
            data_final=data_final,
            valor_inicial=valor_inicial,
            prazo_inicial=prazo_inicial
        )
        obra.save()
        messages.success(request, 'Obra cadastrada com sucesso.')
        return redirect('home')
    
    return render(request, 'home.html') 

def criar_escritorio(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cnpj = request.POST.get('cnpj')
        ceo = request.POST.get('ceo')

        if Escritorio.objects.filter(nome=nome).exists():
            messages.error(request, 'Já existe um escritório com esse nome.')
            return redirect('home')

        escritorio = Escritorio.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            cnpj=cnpj,
            ceo=ceo
        )
        escritorio.save()
        messages.success(request, 'Escritório cadastrado com sucesso.')
        return redirect('home')

    return redirect('home')

def listar_obras(request):
    obras = Obra.objects.all()
    return render(request, 'home.html', {'obras': obras})