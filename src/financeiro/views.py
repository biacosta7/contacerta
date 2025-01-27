from datetime import datetime
from decimal import Decimal, InvalidOperation
from pyexpat.errors import messages
from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from locais.models import Obra, Escritorio
from .models import Aditivo, Despesa, Cartao, Funcionario, NotaBoleto, NotaPix, NotaEspecie, NotaCartao, MaoDeObra, Banco
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


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

@login_required
def criar_despesa(request, tipo, id):
    next_url = request.GET.get('next')
    obra = get_object_or_404(Obra, id=id)
    despesas = Despesa.objects.filter(tipo_local=ContentType.objects.get_for_model(obra), id_local=id)

    if request.method == 'POST':
        try:
            with transaction.atomic():
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

                    despesa = NotaCartao.objects.create(
                        **campos_despesa,
                        cartao=cartao,
                        quant_parcelas=quant_parcelas,
                        valor_parcela=valor_parcela
                    )
                    logger.info(f"NotaCartao criada para despesa com cartão {cartao.id}")
                    print("Nota:", despesa)
                
                elif forma_pag == 'boleto':
                    logger.debug("Processando pagamento com boleto...")

                    vencimento = request.POST.get('vencimento')
                    banco_id = request.POST.get('banco')

                    vencimento = limpar_e_converter_data(vencimento, request)
                    banco = get_object_or_404(Banco, id=banco_id)

                    despesa = NotaBoleto.objects.create(
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

                    despesa = NotaPix.objects.create(
                        **campos_despesa,
                        banco=banco
                    )
                elif forma_pag == 'especie':
                    logger.debug("Processando pagamento em espécie...")
                    
                    despesa = NotaEspecie.objects.create(
                        **campos_despesa,
                        pagador=request.POST.get('recipiente')
                    )

                # Processa a modalidade Mão de Obra
                if modalidade == 'mao_de_obra':
                    logger.debug("Associando modalidade Mão de obra...")
                    funcionario_id = request.POST.get('funcionario')
                    funcionario = get_object_or_404(Funcionario, id=funcionario_id)
                    despesa = get_object_or_404(Despesa, id=despesa.id)

                    MaoDeObra.objects.create(
                        despesa=despesa,
                        funcionario=funcionario,
                        categoria=request.POST.get('categoria')
                    )

                if next_url:
                    return redirect(next_url)
                else:
                    # Redireciona para o detalhe de obra ou escritório com base no tipo
                    if tipo == 'obra':
                        return redirect('locais:detalhe_obra', id=id)
                    else:
                        return redirect('locais:detalhe_escritorio', id=id)

        except IntegrityError as e:
            logger.exception(f"Erro ao criar despesa: {e}")
            return render(request, 'locais/detalhe_obra.html', {
                'obra': obra,
                'despesas': despesas,
            })
        else:
            return render(request, 'locais/detalhe_obra.html', {
                'obra': obra,
                'despesas': despesas,
            })

@login_required
def editar_despesa(request, despesa_id):
    next_url = request.GET.get('next')
    despesa = get_object_or_404(Despesa, id=despesa_id)

    if request.method == 'POST':
        try:
            nome = request.POST.get('nome')
            forma_pag = request.POST.get('forma_pag')
            status = request.POST.get('status')
            valor = request.POST.get('valor')
            observacao = request.POST.get('observacao')
            modalidade = request.POST.get('modalidade')
            data = request.POST.get('data_emissao')
            data_pagamento = request.POST.get('data_pagamento')

            try:
                if data:
                    data = datetime.strptime(data, '%d/%m/%Y').date()
                    print(f"Data válida: {data} ({type(data)})")
                else:
                    print("Campo de data não preenchido")

                if data_pagamento:
                    if data_pagamento == '-':
                        data_pagamento = None
                    else:
                        data_pagamento = datetime.strptime(data_pagamento, '%d/%m/%Y').date()
                        print(f"Data válida: {data_pagamento} ({type(data_pagamento)})")
                else:
                    data_pagamento = None
                    print("Campo de data_pagamento não preenchido")
            except ValueError as e:
                messages.error(request, f'Erro na data: {str(e)}')
                return redirect('locais:home')


            print(" - DATA - ", data)
            valor = limpar_e_converter_valor(valor, request)

            print(f"Data final antes da edição: {data} ({type(data)})")

            despesa.nome = nome
            despesa.forma_pag = forma_pag
            despesa.status = status
            despesa.valor = valor
            despesa.observacao = observacao
            despesa.modalidade = modalidade
            despesa.data = data
            despesa.data_pagamento = data_pagamento
            despesa.save()

            # Tratando formas de pagamento
            if forma_pag == 'cartao':
                logger.debug("Processando pagamento com cartão...")
                cartao_id = request.POST.get('cartao')
                quant_parcelas = request.POST.get('quant_parcelas')
                valor_parcela = request.POST.get('valor_parcela')

                cartao = get_object_or_404(Cartao, id=cartao_id)
                valor_parcela = limpar_e_converter_valor(valor_parcela, request, redirect_url='locais:home')

                notaCartao = get_object_or_404(NotaCartao, id=despesa_id)

                notaCartao.cartao = cartao
                notaCartao.quant_parcelas = quant_parcelas
                notaCartao.valor_parcela = valor_parcela
                notaCartao.save()
                
                logger.info(f"NotaCartao editada para despesa com cartão {cartao.id}")
            
            elif forma_pag == 'boleto':
                logger.debug("Processando pagamento com boleto...")

                vencimento = request.POST.get('vencimento')
                banco_id = request.POST.get('banco')

                vencimento = limpar_e_converter_data(vencimento, request)
                banco = get_object_or_404(Banco, id=banco_id)

                notaBoleto = get_object_or_404(NotaBoleto, id=despesa_id)

                notaBoleto.recipiente = request.POST.get('recipiente') 
                notaBoleto.quant_boletos = request.POST.get('quant_boletos') 
                notaBoleto.vencimento = vencimento
                notaBoleto.num_notafiscal = request.POST.get('num_notafiscal') 
                notaBoleto.banco = banco
                notaBoleto.save()

            elif forma_pag == 'pix':
                logger.debug("Processando pagamento com PIX...")
                banco_id = request.POST.get('banco')
                banco = get_object_or_404(Banco, id=banco_id)

                notaPix = get_object_or_404(NotaPix, id=despesa_id)
                notaPix.banco = banco
                notaPix.save()

            elif forma_pag == 'especie':
                logger.debug("Processando pagamento em espécie...")

                notaEspecie = get_object_or_404(NotaEspecie, id=despesa_id)
                notaEspecie.pagador = request.POST.get('pagador')


            if modalidade == 'mao_de_obra':
                logger.debug("Processando modalidade Mão de obra...")
                funcionario_id = request.POST.get('funcionario')
                funcionario = get_object_or_404(Funcionario, id=funcionario_id)

                maoDeObra = get_object_or_404(MaoDeObra, despesa=despesa_id)
                maoDeObra.funcionario = funcionario
                maoDeObra.categoria = request.POST.get('categoria')
                maoDeObra.save()

            return redirect(next_url if next_url else 'financeiro:cartoes')

        except IntegrityError as e:
            logger.exception(f"Erro ao criar despesa: {e}")
            return redirect(next_url if next_url else 'locais:home')
    else:
        return redirect(next_url if next_url else 'locais:home')

@login_required
def deletar_despesa(request, despesa_id):
    next_url = request.GET.get('next')
    despesa = get_object_or_404(Despesa, id=despesa_id)

    despesa.delete()
    messages.success(request, 'Despesa deletada com sucesso.')
    return redirect(next_url if next_url else 'locais:home')


@login_required
def criar_cartao(request):
    next_url = request.GET.get('next')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        banco_id = request.POST.get('banco')
        final = request.POST.get('final')
        vencimento = request.POST.get('vencimento')
        quant_dias = request.POST.get('quant_dias')
        # melhor_dia = request.POST.get('melhor_dia')

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

    return redirect(next_url if next_url else 'financeiro:cartoes')

@login_required
def ver_cartoes(request):
    cartoes = Cartao.objects.all()
    num_cartoes = Cartao.objects.count()

    return render(request, 'financeiro/cartoes.html', {'cartoes': cartoes, 'num_cartoes': num_cartoes})


@login_required
def editar_obra(request, cartao_id):
    next_url = request.GET.get('next')

    cartao = get_object_or_404(Cartao, id=cartao_id)

    if request.method == 'POST':
        nome = request.POST.get('nome')
        banco_id = request.POST.get('banco')
        final = request.POST.get('final')
        vencimento = request.POST.get('vencimento')
        quant_dias = request.POST.get('quant_dias')
        # melhor_dia = request.POST.get('melhor_dia')

        # Obtenha a instância do banco ou retorne um erro 404 se não existir
        banco = get_object_or_404(Banco, id=banco_id)

        cartao.nome = nome
        cartao.banco = banco
        cartao.final = final
        cartao.vencimento = vencimento
        cartao.quant_dias = quant_dias
        #cartao.melhor_dia = melhor_dia

        cartao.save()
        messages.success(request, 'Cartão atualizado com sucesso.')

    return redirect(next_url if next_url else 'financeiro:cartoes')


@login_required
def deletar_cartao(request, cartao_id):
    next_url = request.GET.get('next')
    cartao = get_object_or_404(Cartao, id=cartao_id)

    cartao.delete()
    messages.success(request, 'Cartão deletado com sucesso.')
    return redirect(next_url if next_url else 'financeiro:cartoes')



@login_required
def criar_banco(request):
    next_url = request.GET.get('next')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        Banco.objects.create(nome=nome)    
   
    # Redireciona para o 'next' ou para uma página padrão 
    return redirect(next_url if next_url else 'financeiro:cartoes')

    
@login_required
def atualizar_status(request, despesa_id):
    next_url = request.GET.get('next')
    # Pega a despesa com o id fornecido, ou retorna 404 se não existir
    despesa = get_object_or_404(Despesa, id=despesa_id)
    
    # Alterna o status da despesa entre 'a_pagar' e 'pago'
    if despesa.status == 'a_pagar':
        despesa.status = 'pago'
    else:
        despesa.status = 'a_pagar'
    
    # Salva a despesa com o novo status
    despesa.save()
    
    return redirect(next_url if next_url else 'financeiro:cartoes')
    

@login_required
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

@login_required
def criar_funcionario(request):
    next_url = request.GET.get('next')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        cargo = request.POST.get('cargo')

        funcionario = Funcionario.objects.create(
            nome=nome,
            cargo=cargo
        )
        funcionario.save()

    return redirect(next_url if next_url else 'financeiro:cartoes')

    