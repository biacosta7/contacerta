from decimal import Decimal, InvalidOperation
from django.core.serializers.json import DjangoJSONEncoder
import json
from locais.models import Obra
from financeiro.models import *
from datetime import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import escape
from django.db.models import Prefetch


# Função para formatar a data para 'dd/mm/yyyy'
def format_date(date_value):
    if date_value:
        return date_value.strftime('%d/%m/%Y')  # Formato: dd/mm/yyyy
    return None

def formatar_valor(valor):
    if valor is None:
        valor = 0  # Substitua por 0 ou outro valor desejado
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    
def info_obras(request):
    # Obtendo todas as obras
    obras = Obra.objects.all()

    # Atualizar valores calculados e formatar as obras
    obras_formatadas = []
    for obra in obras:
        obra.calcular_debito_mensal()  # Atualiza o débito mensal
        obra.calcular_valor_total()
        obra.calcular_valor_receber()
        obra.calcular_debito_geral()
        obra.calcular_custo_total()
        obra.calcular_prazo_atual()
        total_adiantamentos = obra.calcular_total_adiantamentos()
        total_bms = obra.calcular_total_bms()
        soma_adiantamento_bm = obra.calcular_soma_adiantamento_bm()

        obra_dict = {
            'id': obra.id, 
            'nome': obra.nome,
            'valor_inicial': formatar_valor(obra.valor_inicial),
            'valor_total': formatar_valor(obra.valor_total),
            'valor_receber': formatar_valor(obra.valor_receber),
            'local': obra.local,
            'data_inicio': format_date(obra.data_inicio) if obra.data_inicio else None,
            'data_final': format_date(obra.data_final) if obra.data_final else None,
            'prazo_inicial': format_date(obra.prazo_inicial) if obra.prazo_inicial else None,
            'debito_mensal': formatar_valor(obra.debito_mensal),  # Formata o valor aqui
            'debito_geral': formatar_valor(obra.debito_geral),
            'custo_total': formatar_valor(obra.custo_total),
            'prazo_inicial': format_date(obra.prazo_inicial) if obra.prazo_inicial else None,
            'prazo_atual': format_date(obra.prazo_atual) if obra.prazo_atual else None,
            'total_adiantamentos': formatar_valor(total_adiantamentos) if total_adiantamentos is not None else formatar_valor(0),
            'total_bms': formatar_valor(total_bms) if total_bms is not None else formatar_valor(0),
            'soma_adiantamento_bm': formatar_valor(soma_adiantamento_bm) if soma_adiantamento_bm is not None else formatar_valor(0),
        }

        obras_formatadas.append(obra_dict)


    return {
        'obras_json': json.dumps(obras_formatadas, cls=DjangoJSONEncoder),
    }

def bancos(request):
    bancos = Banco.objects.all().values()

    return {
        'bancos': bancos,         
        'bancos_json': json.dumps(list(bancos), cls=DjangoJSONEncoder),
    }

def cartoes(request):
    cartoes = Cartao.objects.select_related('banco').all()
    faturas = Fatura.objects.select_related('cartao').all()

    cartoes_lista = []
    for cartao in cartoes:
        cartao_dict = {
            'id': cartao.id,
            'nome': cartao.nome,
            'final': cartao.final,
            'vencimento': cartao.vencimento,
            'banco': cartao.banco.nome,
            'banco_id': cartao.banco.id,
            'quant_dias': cartao.quant_dias,
            'melhor_dia': cartao.melhor_dia.strftime('%d/%m/%Y') if cartao.melhor_dia else None,
        }

        if not cartao.melhor_dia:
            melhor_dia = cartao.calcular_melhor_dia()
            cartao_dict['melhor_dia'] = melhor_dia.strftime('%d/%m/%Y')

        cartoes_lista.append(cartao_dict)

    faturas_lista = []
    for fatura in faturas:
        faturas_dict = {
            'id': fatura.id,
            'cartao_id': fatura.cartao.id,
            'valor': formatar_valor(fatura.valor),
            'observacao': fatura.observacao,
            'data_pagamento': fatura.data_pagamento.strftime('%d/%m/%Y') if fatura.data_pagamento else None,
        }
        faturas_lista.append(faturas_dict)


    # Serializa os dados para JSON
    cartoes_json = json.dumps(cartoes_lista, cls=DjangoJSONEncoder)
    faturas_json = json.dumps(faturas_lista, cls=DjangoJSONEncoder)


    # Verifica se há busca no request
    query = request.GET.get('search')
    cartao_busca = None
    if query:
        cartao_busca = cartoes.filter(final=query).first()

    return {
        'cartoes': cartoes,
        'cartoes_json': cartoes_json, 
        'cartao_busca': cartao_busca,
        'faturas_json': faturas_json,
    }


    

def despesas(request):
    despesas_queryset = Despesa.objects.all().order_by('-data')  # Garante a ordenação
    despesas = list(despesas_queryset.values('id', 'nome', 'data', 'forma_pag', 'valor', 'observacao', 'status', 'data_pagamento', 'modalidade', 'modalidadeEscritorio'))  # Converte para lista de dicionários mantendo a ordem

    # Carrega notas de cartão e pré-carrega parcelas e pagamentos para otimizar consultas
    nota_cartao = NotaCartao.objects.select_related('cartao__banco').prefetch_related(
        Prefetch('parcelas', queryset=Parcela.objects.all(), to_attr='parcelas_relacionadas')
    ).all().values('id', 'cartao_id', 'status_parcelamento', 'quant_parcelas', 'valor_parcela', 'despesa_ptr_id')


    # Associa os pagamentos da despesa (assumindo que a despesa tem um campo relacionado 'nota_cartao')
    for despesa in despesas:
        if despesa.get('data'):
            despesa['data'] = format_date(despesa['data'])
        if despesa.get('data_pagamento'):
            despesa['data_pagamento'] = format_date(despesa['data_pagamento'])
        if despesa.get('valor'):
            despesa['valor_formatado'] = formatar_valor(despesa['valor'])
        try:
            nota = next((nota for nota in nota_cartao if nota['despesa_ptr_id'] == despesa['id']), None)
            
            if nota:
                nota['valor_parcela_formatado'] =  formatar_valor(nota['valor_parcela'])
                parcelas = list(Parcela.objects.filter(nota_cartao_id=nota['id']).values())  
                parcela_ids = [p['id'] for p in parcelas]  # Pegamos apenas os IDs  
                pagamentos = list(Pagamento.objects.filter(parcela__in=parcela_ids).values())  

                despesa['pagamentos_parcela'] = pagamentos

                # Formata os pagamentos para cada parcela
                for parcela in despesa['pagamentos_parcela']:
                    parcela['valor_pago_formatado'] = formatar_valor(parcela['valor_pago'])
                    parcela['data_pagamento_formatada'] = (parcela['data_pagamento']).strftime('%d/%m/%Y')

        except StopIteration:
            despesa.pagamentos_parcela = []  # Caso não encontre a nota_cartao associada


    nota_boleto = NotaBoleto.objects.select_related('banco').all().values()
    for nota in nota_boleto:
        if nota.get('vencimento'):
            nota['vencimento'] = format_date(nota['vencimento'])

    nota_pix = NotaPix.objects.select_related('banco').all().values()
    nota_especie = NotaEspecie.objects.all().values('id', 'pagador')
    mao_de_obra = MaoDeObra.objects.all().values(
        'id', 'despesa_id', 'categoria', 'funcionario_id', 'valor_reembolso'
    )

    return {
        'nota_cartao_json': json.dumps(list(nota_cartao), cls=DjangoJSONEncoder),
        'nota_boleto_json': json.dumps(list(nota_boleto), cls=DjangoJSONEncoder),
        'nota_pix_json': json.dumps(list(nota_pix), cls=DjangoJSONEncoder),
        'nota_especie_json': json.dumps(list(nota_especie), cls=DjangoJSONEncoder),
        'mao_de_obra_json': json.dumps(list(mao_de_obra), cls=DjangoJSONEncoder),
        'despesas': despesas,
        'despesas_json': json.dumps(list(despesas), cls=DjangoJSONEncoder),
    }

def funcionarios(request):
    funcionarios = Funcionario.objects.all()

    funcionarios_formatados = []

    for funcionario in funcionarios:
        custo_total = formatar_valor(funcionario.custo_total_funcionario())

        funcionarios_dict = {
            'id': funcionario.id,
            'nome': funcionario.nome,
            'cargo': funcionario.cargo,
            'custo_total': custo_total
        }

        funcionarios_formatados.append(funcionarios_dict)

    return {
        'funcionarios_lista': funcionarios_formatados,
        'funcionarios_json': json.dumps(list(funcionarios_formatados), cls=DjangoJSONEncoder),
    }

def aditivos(request):
    aditivos = Aditivo.objects.select_related('obra').all()

    aditivos_lista = []
    for aditivo in aditivos:

        if aditivo.banco != None:
            banco_nome = aditivo.banco.nome
            banco_id = aditivo.banco.id
        else:
            banco_nome = None
            banco_id = None
            
        aditivo_dict = {
            'id': aditivo.id,
            'nome': aditivo.nome,
            'valor': formatar_valor(aditivo.valor) if aditivo.valor else None,
            'dias': aditivo.dias,
            'data': aditivo.data.strftime('%d/%m/%Y') if aditivo.data else None,
            'banco': banco_nome,
            'banco_id': banco_id,
            'modalidade': aditivo.modalidade,
            'observacao': aditivo.observacao,
        }

        aditivos_lista.append(aditivo_dict)

    # Serializa os dados para JSON
    aditivos_json = json.dumps(aditivos_lista, cls=DjangoJSONEncoder)

    return {
        'aditivos': aditivos_lista,
        'aditivos_json': aditivos_json, 
    }

def adiantamentos(request):
    adiantamentos = Adiantamento.objects.select_related('obra', 'banco').all()

    adiantamentos_lista = []
    for adiantamento in adiantamentos:
        adiantamentos_dict = {
            'id': adiantamento.id,
            'nome': adiantamento.nome,
            'valor': formatar_valor(adiantamento.valor) if adiantamento.valor else None,
            'data': adiantamento.data.strftime('%d/%m/%Y') if adiantamento.data else None,
            'banco': adiantamento.banco.nome,
            'banco_id': adiantamento.banco.id,
            'observacao': adiantamento.observacao,
        }

        adiantamentos_lista.append(adiantamentos_dict)

    # Serializa os dados para JSON
    adiantamentos_json = json.dumps(adiantamentos_lista, cls=DjangoJSONEncoder)

    return {
        'adiantamentos_lista': adiantamentos_lista,
        'adiantamentos_json': adiantamentos_json, 
    }

def bms(request):
    bms = BM.objects.select_related('obra', 'banco').all()

    bms_lista = []
    for bm in bms:
        bms_dict = {
            'id': bm.id,
            'nome': bm.nome,
            'codigo': bm.codigo,
            'valor': formatar_valor(bm.valor) if bm.valor else None,
            'data': bm.data.strftime('%d/%m/%Y') if bm.data else None,
            'banco': bm.banco.nome,
            'banco_id': bm.banco.id,
            'observacao': bm.observacao,
        }

        bms_lista.append(bms_dict)

    # Serializa os dados para JSON
    bms_json = json.dumps(bms_lista, cls=DjangoJSONEncoder)

    return {
        'bms_lista': bms_lista,
        'bms_json': bms_json, 
    }