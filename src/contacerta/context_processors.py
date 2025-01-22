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
    cartoes = Cartao.objects.all().values()

    return {'cartoes': cartoes}


def despesas(request):
    despesas = Despesa.objects.all().values()  # Obtém os valores crus
    return {
        'despesas': despesas,
    }