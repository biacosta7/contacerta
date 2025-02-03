import locale
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from financeiro.models import Banco, Cartao, Funcionario, MaoDeObra
from locais.models import Obra, Escritorio, Despesa
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from django.db.models import Q

def formatar_valor(valor):
    if valor is None:
        valor = 0  # Substitua por 0 ou outro valor desejado
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_range_meses():
    meses_abreviados = ["", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

    hoje = date.today()
    meses = []

    # Adicionar os últimos 5 meses
    for n in range(5, 0, -1):
        data = hoje - relativedelta(months=n)
        meses.append((data.year, data.month))
    
    # Adicionar o mês atual
    meses.append((hoje.year, hoje.month))

    # Adicionar os próximos 5 meses
    for n in range(1, 6):
        data = hoje + relativedelta(months=n)
        meses.append((data.year, data.month))

    # Criar a lista formatada
    resultado = [f'{ano}/{meses_abreviados[mes]}' for ano, mes in meses]

    return resultado

def filtrar_despesas(request, despesas_filtro):
    ano_mes = request.GET.getlist('ano_mes')
    data = request.GET.get('data_filtro')
    funcionario = request.GET.getlist('funcionario_filtro')
    modalidade = request.GET.getlist('modalidade')
    categoria = request.GET.getlist('categoria')

    meses_map = {
        "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4,
        "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8,
        "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
    }

    if ano_mes:
        filtros = Q()

        for item in ano_mes:
            ano, mes_abrev = item.split('/')  # '2024/FEV' -> '2024', 'FEV'
            mes = meses_map.get(mes_abrev.upper())  # Converte 'FEV' para 2
            
            if mes:  # Apenas adiciona se o mês for válido
                filtros |= Q(data__year=int(ano), data__month=mes)
        if filtros:
            despesas_filtro = despesas_filtro.filter(filtros)
    
    if data:
        data = datetime.strptime(data, '%d/%m/%Y').date()
        despesas_filtro = despesas_filtro.filter(data=data)

    if funcionario:
        mao_de_obra_filtro = MaoDeObra.objects.filter(funcionario_id__in=funcionario)
        if mao_de_obra_filtro.exists():
            despesas_filtro = despesas_filtro.filter(id__in=mao_de_obra_filtro.values_list('despesa_id', flat=True))

    if modalidade:
        despesas_filtro = despesas_filtro.filter(modalidade__in=modalidade) if modalidade else despesas_filtro

    if categoria:
        categoria_filtro = MaoDeObra.objects.filter(categoria__in=categoria)
        if categoria_filtro.exists():
            despesas_filtro = despesas_filtro.filter(id__in=categoria_filtro.values_list('despesa_id', flat=True))

    return despesas_filtro



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

    orcamento_usado = obra.valor_total - obra.custo_total if obra.valor_total else 0
    
    porcentagem_orcamento_usado = (orcamento_usado / obra.valor_total) * 100 if obra.valor_total else 0

    porcentagem_orcamento_usado = f"{porcentagem_orcamento_usado:.2f}"

    orcamento_usado = formatar_valor(orcamento_usado)

    meses = calcular_range_meses()

    despesas_filtro = filtrar_despesas(request, despesas)

    return render(request, 'locais/detalhe_obra.html', {
        'obra': obra,
        'despesas': despesas_formatadas,
        'despesas_filtro': despesas_filtro,
        'meses': meses,
        'porcentagem_orcamento_usado': porcentagem_orcamento_usado,
        'orcamento_usado': orcamento_usado
    })


@login_required
def consultar_debito_mensal(request, id):
    obra = get_object_or_404(Obra, id=id)
    ano_mes = request.GET.get("ano_mes")

    meses_abreviados = ["", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

    if ano_mes:
        print(ano_mes)
        # Divida a string ano_mes
        ano_mes_dividido = ano_mes.split('/')

        # Extrair o ano
        ano = ano_mes_dividido[0]

        # Encontrar o mês na lista
        mes = 0
        for i, n in enumerate(meses_abreviados):
            if n == ano_mes_dividido[1]:
                mes = i
                break

        debito_mensal = obra.calcular_debito_mensal(mes, ano) if obra else 0
        print(debito_mensal)
    else:
        debito_mensal = obra.calcular_debito_mensal() if obra else 0

    return JsonResponse({"debito_mensal": formatar_valor(debito_mensal)})

    
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