from django.core.serializers.json import DjangoJSONEncoder
import json
from locais.models import Obra
from financeiro.models import *
from datetime import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder

def info_obras(request):
    # Obtendo todas as obras
    obras = Obra.objects.all().values()

    # Função para formatar a data para 'dd/mm/yyyy'
    def format_date(date_value):
        if date_value:
            return date_value.strftime('%d/%m/%Y')  # Formato: dd/mm/yyyy
        return None

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

    return {'bancos': bancos}

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

    return {'cartoes_json': cartoes_json}


def despesas(request):
    despesas = Despesa.objects.all().values() 
    return {
        'despesas': despesas,
    }