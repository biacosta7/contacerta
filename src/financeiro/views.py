from datetime import datetime
from decimal import Decimal, InvalidOperation
from pyexpat.errors import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse

from locais.models import Obra, Escritorio
from .models import Aditivo, Despesa, Cartao, NotaBoleto, NotaPix, NotaEspecie, NotaCartao, MaoDeObra, Banco
from django.contrib.contenttypes.models import ContentType

import logging

logger = logging.getLogger(__name__)

def limpar_e_converter_valor(valor, request, redirect_url='locais:home'):
    # Substituir separadores para o formato decimal
    valor = valor.replace('.', '').replace(',', '.')
    
    try:
        # Converter para Decimal
        return Decimal(valor)
    except InvalidOperation:
        # Adicionar mensagem de erro e redirecionar
        messages.error(request, 'Valor inválido.')
        return redirect(redirect_url)

def limpar_e_converter_data(data_str, request, redirect_url='locais:home', formato='%d/%m/%Y'):
    try:
        # Converter para datetime.date usando o formato especificado
        return datetime.strptime(data_str, formato).date()
    except ValueError:
        # Adicionar mensagem de erro e redirecionar
        messages.error(request, f'Formato de data inválido. Use o formato {formato}.')
        return redirect(redirect_url)

def criar_despesa(request, tipo, id):
    obra = get_object_or_404(Obra, id=id)
    despesas = Despesa.objects.filter(tipo_local=ContentType.objects.get_for_model(obra), id_local=id)

    if request.method == 'POST':
        try:
            descricao = request.POST.get('descricao')
            forma_pag = request.POST.get('forma_pag')
            status = request.POST.get('status')
            valor = request.POST.get('valor')
            observacao = request.POST.get('observacao')
            modalidade = request.POST.get('modalidade')
            data = request.POST.get('data_emissao')
            data_pagamento = request.POST.get('data_pagamento')

            # Obtendo o local baseado no tipo
            if tipo == 'obra':
                local = get_object_or_404(Obra, id=id)
            elif tipo == 'escritorio':
                local = get_object_or_404(Escritorio, id=id)
            else:
                logger.error(f"Tipo inválido fornecido: {tipo}")
                return redirect('locais:home')  # Redirecione ou levante um erro se o tipo for inválido
            
            try:
                if data:
                    data = datetime.strptime(data, '%d/%m/%Y').date()
                    print(f"Data válida: {data} ({type(data)})")
                else:
                    print("Campo de data não preenchido")

                if data_pagamento:
                    data_pagamento = datetime.strptime(data_pagamento, '%d/%m/%Y').date()
                    print(f"Data válida: {data_pagamento} ({type(data_pagamento)})")
                else:
                    data_pagamento = None
                    print("Campo de data_pagamento não preenchido")
            except ValueError as e:
                messages.error(request, f'Erro na data: {str(e)}')
                return redirect('locais:home')


            tipo_local = ContentType.objects.get_for_model(local)
            logger.debug(f"tipo_local: {tipo_local}")
            print(" - DATA - ", data)
            valor = limpar_e_converter_valor(valor, request)

            print(f"Data final antes da criação: {data} ({type(data)})")

            campos_despesa = {
                "nome": descricao,
                "forma_pag": forma_pag,
                "data": data,
                "valor": valor,
                "observacao": observacao,
                "status": status,
                "modalidade": modalidade,
                "tipo_local": tipo_local,
                "id_local": id,
                "local": local,
                "data_pagamento": data_pagamento,
            }

            # Tratando formas de pagamento
            if forma_pag == 'cartao':
                logger.debug("Processando pagamento com cartão...")
                cartao_id = request.POST.get('cartao')
                quant_parcelas = request.POST.get('quant_parcelas')
                valor_parcela = request.POST.get('valor_parcela')

                cartao = get_object_or_404(Cartao, id=cartao_id)
                valor_parcela = limpar_e_converter_valor(valor_parcela, request, redirect_url='locais:home')
        
                NotaCartao.objects.create(
                    **campos_despesa,
                    cartao=cartao,
                    quant_parcelas=quant_parcelas,
                    valor_parcela=valor_parcela
                )
                logger.info(f"NotaCartao criada para despesa com cartão {cartao.id}")
            
            elif forma_pag == 'boleto':
                logger.debug("Processando pagamento com boleto...")

                vencimento = request.POST.get('vencimento')
                banco_id = request.POST.get('banco')

                vencimento = limpar_e_converter_data(vencimento, request)
                banco = get_object_or_404(Banco, id=banco_id)

                NotaBoleto.objects.create(
                    **campos_despesa,
                    recipiente=request.POST.get('recipiente'),
                    quant_boletos=request.POST.get('quant_boletos'),
                    vencimento=vencimento,
                    num_notafiscal=request.POST.get('num_notafiscal'),
                    banco=banco
                )

            elif forma_pag == 'pix':
                logger.debug("Processando pagamento com PIX...")
                banco_id = request.POST.get('banco')
                banco = get_object_or_404(Banco, id=banco_id)

                NotaPix.objects.create(
                    **campos_despesa,
                    banco=banco
                )
            elif forma_pag == 'especie':
                logger.debug("Processando pagamento em espécie...")
                NotaEspecie.objects.create(
                    **campos_despesa,
                    pagador=request.POST.get('recipiente')
                )

            if modalidade == 'mao_de_obra':
                logger.debug("Processando modalidade Mão de obra...")
                funcionario_id = request.POST.get('funcionario')
                funcionario = get_object_or_404(Banco, id=funcionario_id)

                MaoDeObra.objects.create(
                    **campos_despesa,
                    funcionario=funcionario,
                    categoria=request.POST.get('categoria')
                )

            if tipo == 'obra':
                return redirect('locais:detalhe_obra', tipo='obra', id=id)
            else:
                return redirect('locais:detalhe_escritorio', tipo='escritorio', id=id)


        except IntegrityError as e:
            logger.exception(f"Erro ao criar despesa: {e}")
            return render(request, 'locais/detalhe_obra.html', {
                'obra': obra,
                'despesas': despesas,
                'error': str(e),
            })
    else:
        return render(request, 'locais/detalhe_obra.html', {
            'obra': obra,
            'despesas': despesas,
        })

def criar_cartao(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        banco_id = request.POST.get('banco')
        final = request.POST.get('final')
        vencimento = request.POST.get('vencimento')
        quant_dias = request.POST.get('quant_dias')
        # melhor_dia = request.POST.get('melhor_dia')

        print(vencimento)

        # Converter as datas do formato dd/mm/yyyy para yyyy-mm-dd
        try:
            vencimento = datetime.strptime(vencimento, '%d/%m/%Y').date()
        except ValueError:
            messages.error(request, 'Formato de data inválido. Use o formato dd/mm/yyyy.')
            return redirect('locais:home')
        

        # Obtenha a instância do banco ou retorne um erro 404 se não existir
        banco = get_object_or_404(Banco, id=banco_id)

        # Criando o cartão
        cartao = Cartao.objects.create(
            nome=nome,
            banco=banco,
            final=final,
            vencimento=vencimento,
            quant_dias=quant_dias,
        )
        cartao.save()

        # Retorne para a página de cartões ou uma página de sucesso
        return redirect('financeiro:cartoes')  # Altere para o nome correto da URL que lista os cartões.

    else:
        # Caso o método não seja POST, apenas renderiza a página do formulário
        return render(request, 'financeiro/modais/criar_cartao.html')
    
def ver_cartoes(request):
    cartoes = Cartao.objects.all()
    return render(request, 'financeiro/cartoes.html', {'cartoes': cartoes})


def criar_banco(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        banco = Banco.objects.create(nome=nome)
        banco.save()
        return redirect('financeiro:cartoes')
    
    else:
        return render(request, 'financeiro/modais/criar_banco.html')
    

def atualizar_status(request, tipo, id, despesa_id):
    # Pega a despesa com o id fornecido, ou retorna 404 se não existir
    despesa = get_object_or_404(Despesa, id=despesa_id)
    
    # Alterna o status da despesa entre 'a_pagar' e 'pago'
    if despesa.status == 'a_pagar':
        despesa.status = 'pago'
    else:
        despesa.status = 'a_pagar'
    
    # Salva a despesa com o novo status
    despesa.save()
    
    if tipo == 'obra':
        return redirect('locais:detalhe_obra', tipo='obra', id=id)
    else:
        return redirect('locais:detalhe_escritorio', tipo='escritorio', id=id)
    

def criar_aditivo(request, tipo, id):

    if request.method == 'POST':
        nome = request.POST.get('nome')
        valor = request.POST.get('valor')
        dias = request.POST.get('dias')
        data = request.POST.get('data')
        banco_id = request.POST.get('banco')
        modalidade = request.POST.get('modalidade')
        observacao = request.POST.get('observacao')
        obra_id = request.POST.get('obra')

        # Converter as datas do formato dd/mm/yyyy para yyyy-mm-dd
        try:
            data = datetime.strptime(data, '%d/%m/%Y').date()
            
        except ValueError:
            messages.error(request, 'Formato de data inválido. Use o formato dd/mm/yyyy.')
            return redirect('locais:home')

        valor = limpar_e_converter_valor(valor, request, redirect_url='locais:home')

        # Obtenha a instância do banco ou retorne um erro 404 se não existir
        banco = get_object_or_404(Banco, id=banco_id)

        # Obtenha a instância da obra ou retorne um erro 404 se não existir
        obra = get_object_or_404(Obra, id=obra_id)

        # Criando o aditivo
        aditivo = Aditivo.objects.create(
            nome=nome,
            valor=valor,
            dias=dias,
            data=data,
            banco=banco,
            observacao=observacao,
            modalidade=modalidade,
            obra=obra
        )
        aditivo.save()

        if tipo == 'obra':
            return redirect('locais:detalhe_obra', tipo='obra', id=id)
        else:
            return redirect('locais:detalhe_escritorio', tipo='escritorio', id=id)

    else:
        return render(request, 'locais/detalhe_obra.html', {
            'obra': obra,
        })