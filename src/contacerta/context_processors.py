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
    obras = Obra.objects.all().values()

    # Formatar as datas no objeto obras
    for obra in obras:
        if obra.get('data_inicio'):
            obra['data_inicio'] = format_date(obra['data_inicio'])
        if obra.get('data_final'):
            obra['data_final'] = format_date(obra['data_final'])
        if obra.get('prazo_inicial'):
            obra['prazo_inicial'] = format_date(obra['prazo_inicial'])

    return {
        'obras_json': json.dumps(list(obras), cls=DjangoJSONEncoder),
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


def calcular_debito_mensal_total(mes=None, ano=None):
        hoje = date.today()

        mes = mes if mes else hoje.month
        ano = ano if ano else hoje.year

        despesas_mensais = Despesa.objects.filter(
            status='a_pagar',
            data__month=mes,
            data__year=ano
        )
        total_mensal = sum(despesa.valor for despesa in despesas_mensais)
        debito_mensal = formatar_valor(total_mensal)

        return debito_mensal


def despesas(request):
    despesas = Despesa.objects.all().values() 
    debito_mensal_total = calcular_debito_mensal_total()

    # Otimização usando select_related e prefetch_related
    nota_cartao = NotaCartao.objects.select_related('cartao__banco').all().values()
    nota_boleto = NotaBoleto.objects.select_related('banco').all().values()
    nota_pix = NotaPix.objects.select_related('banco').all().values()
    nota_especie = NotaEspecie.objects.all().values()
    mao_de_obra = MaoDeObra.objects.select_related('funcionario').values(
        'id', 'nome', 'forma_pag', 'data', 'valor', 'observacao', 'status', 
        'data_pagamento', 'modalidade', 'categoria', 'funcionario_id'
    )
    funcionarios = Funcionario.objects.values('id', 'nome', 'cargo')
    debito_mensal_total = calcular_debito_mensal_total()

    return {
        'nota_cartao_json': json.dumps(list(nota_cartao), cls=DjangoJSONEncoder),
        'nota_boleto_json': json.dumps(list(nota_boleto), cls=DjangoJSONEncoder),
        'nota_pix_json': json.dumps(list(nota_pix), cls=DjangoJSONEncoder),
        'nota_especie_json': json.dumps(list(nota_especie), cls=DjangoJSONEncoder),
        'mao_de_obra_json': json.dumps(list(mao_de_obra), cls=DjangoJSONEncoder),
        'funcionarios_json': json.dumps(list(funcionarios), cls=DjangoJSONEncoder),
        'debito_mensal_total': debito_mensal_total,
        'despesas': despesas,
        'despesas_json': json.dumps(list(despesas), cls=DjangoJSONEncoder),
    }

def funcionarios(request):
    funcionarios = Funcionario.objects.all().values()

    return {'funcionarios': funcionarios}