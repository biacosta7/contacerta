from datetime import datetime
from decimal import Decimal, InvalidOperation
from pyexpat.errors import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Despesa, Cartao, NotaBoleto, NotaPix, NotaEspecie, NotaCartao, MaoDeObra, Banco
from django.contrib.contenttypes.models import ContentType

def criar_despesa(request):
    if request.method == 'POST':
        descricao = request.POST.get('descricao')
        forma_pag = request.POST.get('forma_pag')
        status = request.POST.get('status')
        valor = request.POST.get('valor')
        observacao = request.POST.get('observacao', '')
        modalidade = request.POST.get('modalidade')

        # Obtendo os dados de cartão, boleto, pix e espécie, caso existam
        cartao_id = request.POST.get('cartao')
        recipiente = request.POST.get('recipiente')
        quant_boletos = request.POST.get('quant_boletos')
        vencimento = request.POST.get('vencimento')
        banco = request.POST.get('banco')
        num_notafiscal = request.POST.get('num_notafiscal')
        quant_parcelas = request.POST.get('quant_parcelas')
        valor_parcela = request.POST.get('valor_parcela')

        # O tipo de local é passado por meio do ContentType, você precisará obter
        tipo_local = request.POST.get('tipo_local')
        id_local = request.POST.get('id_local')
        local = ContentType.objects.get(id=tipo_local).get_object_for_this_type(id=id_local)

        # Criando a despesa
        despesa = Despesa.objects.create(
            nome=descricao,
            forma_pag=forma_pag,
            data=request.POST.get('data'),
            valor=valor,
            observacao=observacao,
            status=status,
            modalidade=modalidade,
            tipo_local=ContentType.objects.get(id=tipo_local),
            id_local=id_local,
            local=local
        )

        # Dependendo da forma de pagamento, você pode querer criar instâncias de modelos relacionados
        if forma_pag == 'cartao':
            cartao = Cartao.objects.get(id=cartao_id)
            NotaCartao.objects.create(
                cartao=cartao,
                despesa=despesa,
                quant_parcelas=quant_parcelas,
                valor_parcela=valor_parcela
            )
        elif forma_pag == 'boleto':
            NotaBoleto.objects.create(
                despesa=despesa,
                recipiente=recipiente,
                quant_boletos=quant_boletos,
                vencimento=vencimento,
                num_notafiscal=num_notafiscal,
                banco=banco
            )
        elif forma_pag == 'pix':
            NotaPix.objects.create(
                despesa=despesa,
                banco=banco
            )
        elif forma_pag == 'especie':
            NotaEspecie.objects.create(
                despesa=despesa,
                pagador=recipiente
            )

        # Retorne para a página de despesas ou uma página de sucesso
        return redirect('locais:home')  # Altere para o nome correto da URL que lista as despesas.

    else:
        # Caso o método não seja POST, apenas renderiza a página do formulário
        return render(request, 'financeiro/criar_despesa.html', {
            'cartoes': Cartao.objects.all(),
            'bancos': ['Banco Teste', 'Outro Banco']  # Lista de bancos, você pode ajustar isso conforme sua necessidade
        })

def criar_cartao(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        banco = request.POST.get('banco')
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
            return redirect('home')
        

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
    return render(request, 'cartoes.html', {'cartoes': cartoes})


def criar_banco(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        banco = Banco.objects.create(nome=nome)
        banco.save()
        return redirect('financeiro:cartoes')
    else:
        return render(request, 'financeiro/modais/criar_banco.html')