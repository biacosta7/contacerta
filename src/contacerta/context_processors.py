from decimal import Decimal, InvalidOperation
from django.core.serializers.json import DjangoJSONEncoder
import json
from locais.models import Obra
from financeiro.models import *
from datetime import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder

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
    # Obtém todos os cartões com os dados necessários (evitando consultas adicionais)
    cartoes = Cartao.objects.select_related('banco').all()

    cartoes_lista = []
    for cartao in cartoes:
        cartao_dict = {
            'id': cartao.id,
            'nome': cartao.nome,
            'final': cartao.final,
            'vencimento': cartao.vencimento,
            'banco': cartao.banco.nome,
            'quant_dias': cartao.quant_dias,
            'melhor_dia': cartao.melhor_dia.strftime('%d/%m/%Y') if cartao.melhor_dia else None,
        }

        if not cartao.melhor_dia:
            melhor_dia = cartao.calcular_melhor_dia()
            cartao_dict['melhor_dia'] = melhor_dia.strftime('%d/%m/%Y')

        cartoes_lista.append(cartao_dict)

    # Serializa os dados para JSON
    cartoes_json = json.dumps(cartoes_lista, cls=DjangoJSONEncoder)

    # Verifica se há busca no request
    query = request.GET.get('search')
    cartao_busca = None
    if query:
        cartao_busca = cartoes.filter(final=query).first()

    return {
        'cartoes': cartoes,
        'cartoes_json': cartoes_json, 
        'cartao_busca': cartao_busca,
    }


def despesas(request):
    despesas = Despesa.objects.all().values() 

    for despesa in despesas:
        if despesa.get('data'):
            despesa['data'] = format_date(despesa['data'])
        if despesa.get('data_pagamento'):
            despesa['data_pagamento'] = format_date(despesa['data_pagamento'])

    # Otimização usando select_related e prefetch_related
    nota_cartao = NotaCartao.objects.select_related('cartao__banco').all().values()
    nota_boleto = NotaBoleto.objects.select_related('banco').all().values()
    for nota in nota_boleto:
        if nota.get('vencimento'):
            nota['vencimento'] = format_date(nota['vencimento'])


    nota_pix = NotaPix.objects.select_related('banco').all().values()
    nota_especie = NotaEspecie.objects.all().values()
    mao_de_obra = MaoDeObra.objects.all().values(
        'id', 'despesa', 'categoria', 'funcionario_id', 'valor_reembolso'
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
    funcionarios = Funcionario.objects.all().values()

    return {'funcionarios': funcionarios}

def aditivos(request):
    aditivos = Aditivo.objects.select_related('obra', 'banco').all()

    aditivos_lista = []
    for aditivo in aditivos:
        aditivo_dict = {
            'id': aditivo.id,
            'nome': aditivo.nome,
            'valor': formatar_valor(aditivo.valor) if aditivo.valor else None,
            'dias': aditivo.dias,
            'data': aditivo.data.strftime('%d/%m/%Y') if aditivo.data else None,
            'banco': aditivo.banco.nome,
            'banco_id': aditivo.banco.id,
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
