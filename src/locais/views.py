import locale
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from financeiro.models import Banco, Cartao, Funcionario
from locais.models import Obra, Escritorio, Despesa
from datetime import datetime
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation

def formatar_valor(valor):
    if valor is None:
        valor = 0  # Substitua por 0 ou outro valor desejado
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@login_required
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
            if data_final: 
                data_final = datetime.strptime(data_final, '%d/%m/%Y').date()
            else:
                data_final = None
        except ValueError:
            messages.error(request, 'Formato de data inválido. Use o formato dd/mm/yyyy.')
            return redirect('locais:home')
        
        # Limpar e converter o valor inicial para decimal
        valor_inicial = valor_inicial.replace('.', '').replace(',', '.')

        try:
            valor_inicial = Decimal(valor_inicial)
        except InvalidOperation:
            messages.error(request, 'Valor inicial inválido.')
            return redirect('locais:home')

        if Obra.objects.filter(nome=nome).exists():
            messages.error(request, 'Já existe uma obra com esse nome.')
            return redirect('locais:home')

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
        return redirect('locais:home')
    
    return render(request, 'locais/home.html') 

@login_required
def listar_obras(request):
    obras = Obra.objects.all()
    for obra in obras:
        obra.valor_inicial = formatar_valor(obra.valor_inicial)
    return render(request, 'locais/home.html', {'obras': obras})

@login_required
def editar_obra(request, obra_id):
    obra = get_object_or_404(Obra, id=obra_id)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        local = request.POST.get('local')
        data_inicio = request.POST.get('data_inicio')
        data_final = request.POST.get('data_final')
        valor_inicial = request.POST.get('valor_inicial')
        prazo_inicial = request.POST.get('prazo_inicial')

        print(nome, "\t", local,"\t", data_inicio,"\t", data_final,"\t", valor_inicial,"\t", prazo_inicial)

        # Converter as datas do formato dd/mm/yyyy para yyyy-mm-dd
        try:
            data_inicio = datetime.strptime(data_inicio, '%d/%m/%Y').date()
            prazo_inicial = datetime.strptime(prazo_inicial, '%d/%m/%Y').date()
            if data_final: 
                data_final = datetime.strptime(data_final, '%d/%m/%Y').date()
            else:
                data_final = None 
        except ValueError:
            messages.error(request, 'Formato de data inválido. Use o formato dd/mm/yyyy.')
            return redirect('locais:home')
        
        # Limpar e converter o valor inicial para decimal
        valor_inicial = valor_inicial.replace('.', '').replace(',', '.')

        try:
            valor_inicial = Decimal(valor_inicial)
        except InvalidOperation:
            print("erro valor inicial")
            messages.error(request, 'Valor inicial inválido.')
            return redirect('locais:home')

        obra.nome = nome
        obra.local = local
        obra.data_inicio = data_inicio
        obra.data_final = data_final
        obra.valor_inicial = valor_inicial
        obra.prazo_inicial = prazo_inicial

        obra.save()
        messages.success(request, 'Obra atualizada com sucesso.')
        return redirect('locais:home')

    # Renderizar o template com os dados da obra para edição
    return render(request, 'locais/home.html', {'obra': obra})

@login_required
def deletar_obra(request, obra_id):
    obra = get_object_or_404(Obra, id=obra_id)

    obra.delete()
    messages.success(request, 'Obra deletada com sucesso.')
    return redirect('locais:home')

@login_required
def detalhar_obra(request, id):
    obra = get_object_or_404(Obra, id=id)
    despesas = Despesa.objects.filter(id_local=id)
    
    # Formata os valores das despesas
    despesas_formatadas = []
    for despesa in despesas:
        despesa_dict = despesa.__dict__.copy()  # Converte o objeto em dicionário
        despesa_dict['valor'] = formatar_valor(despesa.valor)  # Formata o valor
        despesas_formatadas.append(despesa_dict)

        # Calcula os valores para a obra, mas não formata aqui
        obra.debito_mensal = obra.calcular_debito_mensal()
        obra.valor_total = obra.calcular_valor_total()
        obra.valor_receber = obra.calcular_valor_receber()
        obra.debito_geral = obra.calcular_debito_geral()
        obra.custo_total = obra.calcular_custo_total()
        obra.prazo_atual = obra.calcular_prazo_atual()

    return render(request, 'locais/detalhe_obra.html', {
        'obra': obra,
        'despesas': despesas_formatadas,
    })

    
@login_required
def criar_escritorio(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cnpj = request.POST.get('cnpj')
        ceo = request.POST.get('ceo')

        if Escritorio.objects.filter(nome=nome).exists():
            messages.error(request, 'Já existe um escritório com esse nome.')
            return redirect('locais:home')

        escritorio = Escritorio.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            cnpj=cnpj,
            ceo=ceo
        )
        escritorio.save()
        messages.success(request, 'Escritório cadastrado com sucesso.')
        return redirect('locais:home')

    return redirect('locais:home')


@login_required
def detalhar_escritorio(request, id=None):
    escritorio = Escritorio.objects.first()
    funcionarios = Funcionario.objects.all()
    bancos = Banco.objects.all()
    cartoes = Cartao.objects.all()

    if escritorio:
        escritorio_id = escritorio.id
        escritorio = get_object_or_404(Escritorio, id=id)
    else:
        # Trate o caso em que não há nenhum escritório
        escritorio_id = None
    
    return render(request, 'locais/detalhe_escritorio.html', {
        'escritorio': escritorio,
        'funcionarios': funcionarios,
        'bancos': bancos,
        'cartoes': cartoes,
    })