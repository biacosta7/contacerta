from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from .models import Despesa

def criar_despesa(request):
    if request.method == 'POST':
        # Obtenção de campos do formulário
        descricao = request.POST.get('descricao')
        forma_pag = request.POST.get('forma_pag')
        data = request.POST.get('data')
        valor = request.POST.get('valor')
        observacao = request.POST.get('observacao', '')  # Campo opcional
        status = request.POST.get('status')
        data_pagamento = request.POST.get('data_pagamento')  # Pode ser vazio
        modalidade = request.POST.get('modalidade')
        tipo_local_id = request.POST.get('tipo_local')  # ContentType ID
        id_local = request.POST.get('id_local')  # ID do local associado

        # Validações básicas
        if not descricao or not forma_pag or not data or not valor or not status or not modalidade or not tipo_local_id or not id_local:
            messages.error(request, 'Todos os campos obrigatórios devem ser preenchidos.')
            return redirect('criar_despesa')

        try:
            # Conversão de valores
            tipo_local = ContentType.objects.get(id=tipo_local_id)
            valor = float(valor)  # Certificar que o valor é numérico
            data = datetime.strptime(data, '%Y-%m-%d').date()

            # Validação do status e data de pagamento
            if status == 'pago' and not data_pagamento:
                messages.error(request, 'Uma despesa marcada como "Pago" deve ter uma data de pagamento.')
                return redirect('criar_despesa')
            data_pagamento = datetime.strptime(data_pagamento, '%Y-%m-%d').date() if data_pagamento else None

            # Criação da despesa
            despesa = Despesa.objects.create(
                descricao=descricao,
                forma_pag=forma_pag,
                data=data,
                valor=valor,
                observacao=observacao,
                status=status,
                data_pagamento=data_pagamento,
                modalidade=modalidade,
                tipo_local=tipo_local,
                id_local=id_local,
            )
            messages.success(request, 'Despesa criada com sucesso.')
            return redirect('locais:home')
        except ContentType.DoesNotExist:
            messages.error(request, 'O tipo de local especificado é inválido.')
        except ValueError:
            messages.error(request, 'Certifique-se de que os valores numéricos e datas estão no formato correto.')

    # Renderizar formulário
    return redirect('locais:home')