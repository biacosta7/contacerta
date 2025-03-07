import json
import locale
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from financeiro.models import Aditivo, Banco, Cartao, Funcionario, MaoDeObra, NotaCartao, Pagamento, Parcela
from locais.models import AcessoEscritorio, Obra, Escritorio, Despesa
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from users.models import User

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

def filtrar(request, dados, tipo_filtro):
    dados_filtrados = dados
    
    modalidade_aditivo = None
    funcionario = []
    categoria = []
    modalidade = []
    modalidade_escritorio = []
    forma_pag_formatado = []
    total_filtro = 0

    ano_mes = request.GET.getlist('ano_mes')
    data = request.GET.get('data_filtro')
    forma_pag = request.GET.getlist('forma_pag')
    
    if tipo_filtro == 'aditivo':
        modalidade_aditivo = request.GET.getlist('modalidade_aditivo')

    else:
        funcionario = request.GET.getlist('funcionario_filtro')
        categoria = request.GET.getlist('categoria')
        modalidade = request.GET.getlist('modalidade')
        modalidade_escritorio = request.GET.getlist('modalidade_escritorio')
    
    for i in forma_pag:
        if i == "cartao":
            forma_pag_formatado.append("Cartão")
        elif i == "boleto":
            forma_pag_formatado.append("Boleto")
        elif i == "pix":
            forma_pag_formatado.append("Pix")
        elif i == "especie":
            forma_pag_formatado.append("Espécie")
    
    filtros_preenchidos = {
        "Ano-Mês": ano_mes,
        "Data": data,
        "Funcionario": funcionario,
        "Modalidade": modalidade,
        "Categoria": categoria,
        "Forma": forma_pag_formatado,
        "Modalidade escritório": modalidade_escritorio,
        "Tipo do Aditivo": modalidade_aditivo
    }

    filtros_preenchidos_filtrados = {}

    # Itera sobre cada chave e valor de 'filtros_preenchidos'
    for k, v in filtros_preenchidos.items():
        if v:
            filtros_preenchidos_filtrados[k] = v

    if not any(filtros_preenchidos.values()):
        return None, {}, 0

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
            dados_filtrados = dados_filtrados.filter(filtros)
    
    if data:
        data = datetime.strptime(data, '%d/%m/%Y').date()
        dados_filtrados = dados_filtrados.filter(data=data)

    if forma_pag:
        dados_filtrados = dados_filtrados.filter(forma_pag__in=forma_pag) if forma_pag else dados_filtrados

    if tipo_filtro == "aditivo":
            dados_filtrados = dados_filtrados.filter(modalidade__in=modalidade_aditivo) if modalidade_aditivo else dados_filtrados

            for elemento in modalidade_aditivo:
                if elemento == "valor":
                    total_filtro = sum(aditivo.valor for aditivo in dados_filtrados)

    elif tipo_filtro == 'adiantamento-bm':
        pass
    
    else:
        if tipo_filtro == 'obra':
            if modalidade:
                dados_filtrados = dados_filtrados.filter(modalidade__in=modalidade) if modalidade else dados_filtrados

        elif tipo_filtro == 'escritorio':
            if modalidade_escritorio:
                dados_filtrados = dados_filtrados.filter(modalidade_escritorio__in=modalidade_escritorio) if modalidade_escritorio else dados_filtrados
                
        if funcionario:
            mao_de_obra_filtro = MaoDeObra.objects.filter(funcionario_id__in=funcionario)
            if mao_de_obra_filtro.exists():
                dados_filtrados = dados_filtrados.filter(id__in=mao_de_obra_filtro.values_list('despesa_id', flat=True))

        if categoria:
            categoria_filtro = MaoDeObra.objects.filter(categoria__in=categoria)
            if categoria_filtro.exists():
                dados_filtrados = dados_filtrados.filter(id__in=categoria_filtro.values_list('despesa_id', flat=True))


        total_filtro = sum(despesa.valor for despesa in dados_filtrados)

    if not dados_filtrados.exists():
        messages.error(request, "Não há despesas correspondentes aos filtros aplicados.")

    return dados_filtrados, filtros_preenchidos_filtrados, total_filtro


@login_required
def criar_obra(request, escritorio_id):
    escritorio = get_object_or_404(Escritorio, id=escritorio_id)
    if request.method == 'POST':

        imagem = request.FILES.get('imagem')
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
            return redirect('locais:home', escritorio_id=escritorio_id)
        
        # Limpar e converter o valor inicial para decimal
        valor_inicial = valor_inicial.replace('.', '').replace(',', '.')

        try:
            valor_inicial = Decimal(valor_inicial)
        except InvalidOperation:
            messages.error(request, 'Valor inicial inválido.')
            return redirect('locais:home', escritorio_id=escritorio_id)

        if Obra.objects.filter(nome=nome).exists():
            messages.error(request, 'Já existe uma obra com esse nome.')
            return redirect('locais:home', escritorio_id=escritorio_id)
        
        if imagem: 
            upload_result = cloudinary.uploader.upload(imagem)
            imagem_url = upload_result.get('secure_url')
            public_id = upload_result.get('public_id')  # Salva o ID gerado pelo Cloudinary
        else:
            imagem_url = None
            public_id = None

        obra = Obra.objects.create(
            imagem_url = imagem_url,
            public_id=public_id,
            escritorio=escritorio,
            nome=nome,
            local=local,
            data_inicio=data_inicio,
            data_final=data_final,
            valor_inicial=valor_inicial,
            prazo_inicial=prazo_inicial
        )
        obra.save()
        messages.success(request, 'Obra cadastrada com sucesso.')
        return redirect('locais:home', escritorio_id=escritorio_id)
    
    return render(request, 'locais/home.html', escritorio_id=escritorio_id) 

@login_required
def listar_obras(request, escritorio_id):
    escritorio = get_object_or_404(Escritorio, id=escritorio_id)

    # Pegando apenas as obras do escritório do usuário
    obras = Obra.objects.filter(escritorio=escritorio)
    for obra in obras:
        if obra.public_id:  # Usa o public_id armazenado
            auto_crop_url, _ = cloudinary_url(
                obra.public_id, gravity="auto"
            )
            obra.imagem = auto_crop_url
        else:
            obra.imagem = "https://s2-casavogue.glbimg.com/itdyzyUXwCOr9zHMqy1L_C-SXl4=/0x0:6000x4000/1000x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_d72fd4bf0af74c0c89d27a5a226dbbf8/internal_photos/bs/2022/u/4/Pml4bDR3S37ZhsiKxMDg/limpeza-pos-obra-01.jpg"

        # Formatar o valor inicial (presumivelmente você tenha uma função formatar_valor())
        obra.valor_inicial = formatar_valor(obra.valor_inicial)

    return render(request, 'locais/home.html', {'obras': obras, 'escritorio': escritorio})


@login_required
def editar_obra(request, obra_id):
    obra = get_object_or_404(Obra, id=obra_id)
    escritorio_id = obra.escritorio.id

    if request.method == 'POST':
        imagem = request.FILES.get('imagem_editar')
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
            return redirect('locais:home', escritorio_id=escritorio_id)
        
        # Limpar e converter o valor inicial para decimal
        valor_inicial = valor_inicial.replace('.', '').replace(',', '.')

        try:
            valor_inicial = Decimal(valor_inicial)
        except InvalidOperation:
            messages.error(request, 'Valor inicial inválido.')
            return redirect('locais:home', escritorio_id=escritorio_id)
        
        if imagem: 
            upload_result = cloudinary.uploader.upload(imagem)
            imagem_url = upload_result.get('secure_url')
            public_id = upload_result.get('public_id')  # Salva o ID gerado pelo Cloudinary
            obra.imagem_url = imagem_url
            obra.public_id = public_id

        obra.nome = nome
        obra.local = local
        obra.data_inicio = data_inicio
        obra.data_final = data_final
        obra.valor_inicial = valor_inicial
        obra.prazo_inicial = prazo_inicial

        obra.save()
        messages.success(request, 'Obra atualizada com sucesso.')
        return redirect('locais:home', escritorio_id=escritorio_id)

    # Renderizar o template com os dados da obra para edição
    return render(request, 'locais/home.html', {'obra': obra})

@login_required
def deletar_obra(request, obra_id):
    obra = get_object_or_404(Obra, id=obra_id)
    escritorio_id = obra.escritorio.id

    obra.delete()
    messages.success(request, 'Obra deletada com sucesso.')
    return redirect('locais:home', escritorio_id=escritorio_id)

@login_required
def detalhar_obra(request, id):
    obra = get_object_or_404(Obra, id=id)
    tipo_local_obra = ContentType.objects.get_for_model(Obra)
    escritorio_id = obra.escritorio.id

    despesas = Despesa.objects.filter(tipo_local=tipo_local_obra, id_local=id).order_by('-data')  # Ordena por data decrescente (mais nova primeiro)

    aditivos = Aditivo.objects.filter(obra_id=obra.id).order_by('-data')
    
    for despesa in despesas:
        try:
            nota_cartao = NotaCartao.objects.get(despesa_ptr_id=despesa.id)
            parcelas = Parcela.objects.filter(nota_cartao=nota_cartao)
            pagamentos = Pagamento.objects.filter(parcela__in=parcelas)

            despesa.nota_cartao = nota_cartao  # Adiciona nota_cartao à instância de Despesa
            despesa.pagamentos_parcela = pagamentos
            despesa.valor_formatado = formatar_valor(despesa.valor)
            despesa.data_formatada = (despesa.data).strftime('%d/%m/%Y')

            for parcela in despesa.pagamentos_parcela:
                parcela.valor_pago_formatado = formatar_valor(parcela.valor_pago)
                parcela.data_pagamento_formatado = (parcela.data_pagamento).strftime('%d/%m/%Y')

        except NotaCartao.DoesNotExist:
            despesa.nota_cartao = None
            despesa.pagamentos_parcela = None

    # Calcula os valores para a obra, mas não formata aqui
    obra.debito_mensal = obra.calcular_debito_mensal()
    obra.valor_total = obra.calcular_valor_total()
    obra.valor_receber = obra.calcular_valor_receber()
    obra.debito_geral = obra.calcular_debito_geral()
    obra.custo_total = obra.calcular_custo_total()
    obra.prazo_atual = obra.calcular_prazo_atual()
    obra.valor_inicial_formatado = formatar_valor(obra.valor_inicial)

    orcamento_usado = obra.valor_total - obra.custo_total if obra.valor_total else 0
    
    porcentagem_orcamento_usado = 100 - ((orcamento_usado / obra.valor_total) * 100) if obra.valor_total else 0

    porcentagem_orcamento_usado = f"{porcentagem_orcamento_usado:.2f}"

    orcamento_usado = formatar_valor(orcamento_usado)

    meses = calcular_range_meses()

    aditivos_filtro = None
    despesas_filtro = None
    filtros_preenchidos = {}
    total_filtro = 0

    if request.method == 'GET':
        tipo_filtro = request.GET.get('tipo_filtro')
        if tipo_filtro == 'aditivo':
            aditivos_filtro, filtros_preenchidos, total_filtro = filtrar(request, aditivos, tipo_filtro)

            if aditivos_filtro:
                for aditivo in aditivos_filtro:
                    if aditivo.modalidade == "valor":
                        aditivo.valor_formatado = formatar_valor(aditivo.valor) 
            
        else:
            despesas_filtro, filtros_preenchidos, total_filtro = filtrar(request, despesas, tipo_filtro)

            if despesas_filtro:
                for despesa in despesas_filtro:
                    despesa.valor_formatado = formatar_valor(despesa.valor) 

    total_filtro = formatar_valor(total_filtro)

    request.session['despesas_ids'] = list(despesas_filtro.values_list("id", flat=True)) if despesas_filtro else list(despesas.values_list("id", flat=True))

    return render(request, 'locais/detalhe_obra.html', {
        'tipo_local': 'obra',
        'obra': obra,
        'despesas': despesas,
        'despesas_filtro': despesas_filtro,
        'aditivos_filtro': aditivos_filtro,
        'filtros_preenchidos': filtros_preenchidos,
        'meses': meses,
        'porcentagem_orcamento_usado': porcentagem_orcamento_usado,
        'orcamento_usado': orcamento_usado,
        'total_filtro': total_filtro,
        'escritorio_id': escritorio_id,
    })


@login_required
def consultar_debito_mensal(request, tipo, id):
    if tipo == 'escritorio':
        tipo = ContentType.objects.get_for_model(Escritorio)
        local = get_object_or_404(Escritorio, id=id)

    elif tipo == 'obra':
        tipo = ContentType.objects.get_for_model(Obra)
        local = get_object_or_404(Obra, id=id)
    
    ano_mes = request.GET.get("ano_mes")

    meses_abreviados = ["", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

    if ano_mes:
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

        debito_mensal = local.calcular_debito_mensal(mes, ano) if local else 0
    else:
        debito_mensal = local.calcular_debito_mensal() if local else 0

    return JsonResponse({"debito_mensal": formatar_valor(debito_mensal)})


# Escritório 
@login_required
def acesso_hub(request, user_id):
    acessos = AcessoEscritorio.objects.filter(user_receptor=user_id, status='pendente')
    escritorios = Escritorio.objects.filter(membros=request.user)

    context = {
        'user_id': user_id,
        'escritorios': escritorios,
        'acessos': acessos
    }
    return render(request, 'locais/hub.html', context)

@login_required
def criar_escritorio(request, user_id):
    next_url = request.GET.get('next')
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cnpj = request.POST.get('cnpj')

        if Escritorio.objects.filter(nome=nome).exists():
            messages.error(request, 'Já existe um escritório com esse nome.')
            return redirect(next_url if next_url else 'locais:hub', user_id=user_id)

        escritorio = Escritorio.objects.create(
            nome=nome,
            email=email,
            telefone=telefone,
            cnpj=cnpj,
        )
        escritorio.admins.add(user)
        escritorio.membros.add(user)
        escritorio.save()
        messages.success(request, 'Escritório cadastrado com sucesso.')
        return redirect('locais:home', escritorio.id)

    return redirect(next_url if next_url else 'locais:hub', user_id=user_id)

@login_required
def editar_escritorio(request, escritorio_id):
    next_url = request.GET.get('next')
    escritorio = get_object_or_404(Escritorio, id=escritorio_id)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        cnpj = request.POST.get('cnpj')

    escritorio.nome = nome
    escritorio.email = email
    escritorio.telefone = telefone
    escritorio.cnpj = cnpj

    escritorio.save()
    messages.success(request, 'Escritório atualizado com sucesso.')
    return redirect(next_url if next_url else 'locais:home', escritorio_id=escritorio_id)


@login_required
def enviar_acesso_escritorio(request, escritorio_id):
    next_url = request.GET.get('next')

    admin = request.user
    escritorio = get_object_or_404(Escritorio, id=escritorio_id)

    # Verifica se o usuário logado é admin do escritório
    if admin not in escritorio.admins.all():
        messages.error(request, 'Você não tem permissão para conceder acesso a este escritório.')
        return redirect(next_url if next_url else 'locais:home', escritorio_id=escritorio_id)

    if request.method == 'POST':
        receptor_email = request.POST.get('receptor')

        if not receptor_email:
            messages.error(request, 'Por favor, informe um e-mail válido.')
            return redirect(next_url if next_url else 'locais:home', escritorio_id=escritorio_id)

        user_receptor = User.objects.filter(email=receptor_email).first()

        if not user_receptor:
            messages.error(request, f'O email "{receptor_email}" não está cadastrado no sistema.')
            return redirect(next_url if next_url else 'locais:home', escritorio_id=escritorio_id)

        cargo = request.POST.get('cargo')

        AcessoEscritorio.objects.create(
            user_receptor=user_receptor,
            cargo=cargo,
            escritorio=escritorio,
            admin=admin,
        )

        messages.success(request, 'Acesso enviado com sucesso.')
        return redirect(next_url if next_url else 'locais:home', escritorio_id=escritorio_id)

    return redirect(next_url if next_url else 'locais:home', escritorio_id=escritorio_id)


@login_required
def responder_acesso_escritorio(request, acesso_id, escritorio_id):
    next_url = request.GET.get('next')
    acesso = get_object_or_404(AcessoEscritorio, id=acesso_id)
    escritorio = get_object_or_404(Escritorio, id=escritorio_id)
    
    if acesso.user_receptor == request.user:
        if request.method == 'POST':
            status_form = request.POST.get('status')

            if status_form == 'aprovado':
                acesso.status = 'aprovado'

                escritorio.membros.add(acesso.user_receptor)

                if acesso.cargo == 'ADM':
                    escritorio.admins.add(acesso.user_receptor)
                elif acesso.cargo == 'FUNC':
                    escritorio.funcionarios.add(acesso.user_receptor)

                acesso.save()
                escritorio.save()

                messages.success(request, 'Acesso concedido com sucesso.')
                return redirect('locais:home', escritorio_id=escritorio_id)
                
            elif status_form == 'rejeitado':
                acesso.status = 'rejeitado'
                acesso.save()
                messages.info(request, 'Acesso rejeitado com sucesso.')
            return redirect(next_url) if next_url else redirect('locais:hub', user_id=request.user.id)
            

    return redirect(next_url) if next_url else redirect('locais:hub', user_id=request.user.id)


@login_required
def detalhar_escritorio(request, escritorio_id=None):
    escritorio = Escritorio.objects.first()
    funcionarios = Funcionario.objects.all()
    bancos = Banco.objects.all()
    cartoes = Cartao.objects.all()
    tipo_local_escritorio = ContentType.objects.get_for_model(Escritorio)

    if escritorio_id:
        escritorio = get_object_or_404(Escritorio, id=escritorio_id)
        escritorio.debito_geral_formatado = formatar_valor(escritorio.calcular_debito_geral())
        escritorio.debito_mensal_formatado = formatar_valor(escritorio.calcular_debito_mensal())
    else:
        escritorio = None

    despesas = Despesa.objects.filter(
        tipo_local=tipo_local_escritorio,
        id_local=escritorio_id
    ).order_by('-data')  # Ordena por data decrescente (mais nova primeiro)

    acessos = AcessoEscritorio.objects.all()
    meses = calcular_range_meses()

    total_filtro = 0

    despesas_filtro, filtros_preenchidos, total_filtro = filtrar(request, despesas.order_by('-data'), 'escritorio')

    total_filtro = formatar_valor(total_filtro)

    if despesas_filtro:
        for despesa in despesas_filtro:
            despesa.valor_formatado = formatar_valor(despesa.valor)

    request.session['despesas_ids'] = list(despesas_filtro.values_list("id", flat=True)) if despesas_filtro else list(despesas.values_list("id", flat=True))
    
    for despesa in despesas:
        try:
            nota_cartao = NotaCartao.objects.get(despesa_ptr_id=despesa.id)
            parcelas = Parcela.objects.filter(nota_cartao=nota_cartao)
            pagamentos = Pagamento.objects.filter(parcela__in=parcelas)

            despesa.nota_cartao = nota_cartao  # Adiciona nota_cartao à instância de Despesa
            despesa.pagamentos_parcela = pagamentos
            despesa.valor_formatado = formatar_valor(despesa.valor)
        except NotaCartao.DoesNotExist:
            despesa.nota_cartao = None
            despesa.pagamentos_parcela = None
    
    # Formata os valores das despesas
    for despesa in despesas:
        despesa.valor_formatado = formatar_valor(despesa.valor)
        despesa.data_formatada = (despesa.data).strftime('%d/%m/%Y')
      
    return render(request, 'locais/detalhe_escritorio.html', {
        'tipo_local': 'escritorio',
        'escritorio': escritorio,
        'escritorio_id': escritorio.id,
        'funcionarios': funcionarios,
        'bancos': bancos,
        'cartoes': cartoes,
        'escritorio': escritorio,
        'acessos': acessos,
        'despesas_escritorio': despesas,
        'meses': meses,
        'despesas_filtro': despesas_filtro, 
        'filtros_preenchidos': filtros_preenchidos, 
        'total_filtro': total_filtro
    })


