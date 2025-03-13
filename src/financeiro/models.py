from datetime import date, timedelta, timezone
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator, MaxValueValidator
from dateutil.relativedelta import relativedelta
from django.forms import ValidationError

class Banco(models.Model):
    imagem_url = models.URLField(blank=True, null=True)
    public_id = models.CharField(max_length=255, null=True, blank=True)

    nome = models.CharField(max_length=100)
    
    def __str__(self):
        return self.nome

class Adiantamento(models.Model):
    nome = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)
    observacao = models.TextField(blank=True)
    obra = models.ForeignKey('locais.Obra', on_delete=models.CASCADE)

class Aditivo(models.Model):
    nome = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dias = models.IntegerField(null=True, blank=True)
    data = models.DateField()
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT, null=True, blank=True)
    modalidade = models.CharField(max_length=10, choices=[
        ('prazo', 'Prazo'),
        ('valor', 'Valor'),
    ])
    observacao = models.TextField(blank=True)
    obra = models.ForeignKey('locais.Obra', on_delete=models.CASCADE)   

    def __str__(self):
        return f"{self.data} | {self.nome} ({self.valor})"

class BM(models.Model):
    nome = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField(null=False, blank=False)
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=50, blank=True)
    observacao = models.TextField(blank=True)
    obra = models.ForeignKey('locais.Obra', on_delete=models.CASCADE)  
      
    def __str__(self):
        return f"{self.data} | {self.nome} (R${self.valor})"


class Despesa(models.Model):
    nome = models.CharField(max_length=100)
    forma_pag = models.CharField(max_length=20, choices=[
        ('boleto', 'Boleto'),
        ('cartao', 'Cartão'),
        ('pix', 'Pix'),
        ('especie', 'Espécie'),
    ])
    data = models.DateField(blank=False, null=False)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('a_pagar', 'À pagar'),
        ('pago', 'Pago'),
    ])
    data_pagamento = models.DateField(blank=True, null=True)

    modalidade = models.CharField(max_length=50, choices=[
        ('mao_de_obra', 'Mão de Obra'),
        ('insumos', 'Insumos'),
        ('combustivel', 'Combustível'),
        ('administracao', 'Administração'),
        ('outra', 'Outra'),
    ], blank=True, null=True)

    modalidadeEscritorio = models.CharField(max_length=50, choices=[
        ('imposto', 'Imposto'),
        ('contador', 'Contador'),
        ('rastreamento', 'Rastreamento'),
        ('parcela_carro', 'Parcela do carro'),
    ], blank=True, null=True)

    # GFK para associar com Obra ou Escritório
    tipo_local = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    id_local = models.PositiveIntegerField()
    local = GenericForeignKey('tipo_local', 'id_local')
    
    def clean(self):
        super().clean()
        
        # Pegando o modelo referenciado pelo tipo_local
        tipo_modelo = self.tipo_local.model_class()

        if tipo_modelo.__name__ == 'Escritorio':
            if not self.modalidadeEscritorio:
                raise ValidationError({'modalidadeEscritorio': 'Este campo é obrigatório para Escritório.'})
            if self.modalidade:
                raise ValidationError({'modalidade': 'Este campo não deve ser preenchido para Escritório.'})

        elif tipo_modelo.__name__ == 'Obra':
            if not self.modalidade:
                raise ValidationError({'modalidade': 'Este campo é obrigatório para Obra.'})
            if self.modalidadeEscritorio:
                raise ValidationError({'modalidadeEscritorio': 'Este campo não deve ser preenchido para Obra.'})

    def __str__(self):
        nome_limite = self.nome[:20]
        if len(self.nome) > 20:
            nome_limite += '...'
        return f"{self.data} | {self.local} | {nome_limite} | ({self.modalidade} | R${self.valor})"


class Cartao(models.Model):
    cor = models.CharField(max_length=30, blank=True, default='zinc')

    nome = models.CharField(max_length=100)
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)
    final = models.CharField(max_length=4)
    vencimento = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Insira um número entre 1 e 31"
    )
    quant_dias = models.IntegerField()  # Dias entre fechamento e vencimento
    melhor_dia = models.DateField(blank=True, null=True)  # Será calculado

    escritorio = models.ForeignKey("locais.Escritorio", on_delete=models.CASCADE, related_name="cartoes")

    def calcular_melhor_dia(self):
        """Calcula o melhor dia de compra com base no vencimento."""
        hoje = date.today()
        try:
            vencimento_data_atual = date(hoje.year, hoje.month, self.vencimento)
        except ValueError:
            # Ajuste para meses sem o dia exato (ex: 31 de fevereiro → último dia do mês)
            proximo_mes = hoje.month + 1 if hoje.month < 12 else 1
            ano_ajustado = hoje.year if hoje.month < 12 else hoje.year + 1
            vencimento_data_atual = date(ano_ajustado, proximo_mes, 1) - timedelta(days=1)

        # Calcula o melhor dia baseado nos dias antes do vencimento
        self.melhor_dia = vencimento_data_atual - timedelta(days=self.quant_dias)
        self.save()
        return self.melhor_dia

    def __str__(self):
        return f"{self.final} | {self.nome} | {self.banco}"


class NotaCartao(Despesa):
    cartao = models.ForeignKey(Cartao, on_delete=models.SET_NULL, null=True)
    quant_parcelas = models.IntegerField(default=1)
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    status_parcelamento = models.CharField(max_length=20, choices=[
        ('a_pagar', 'À pagar'),
        ('pago', 'Pago'),
    ])
    
    def calcular_vencimentos_parcelas(self):
        """Calcula a data de vencimento de cada parcela."""
        hoje = date.today()
        melhor_dia = self.cartao.melhor_dia
        vencimento_dia = self.cartao.vencimento

        # Determina o vencimento da primeira parcela
        if melhor_dia and hoje > melhor_dia:
            primeiro_vencimento = date(hoje.year, hoje.month, vencimento_dia) + relativedelta(months=1)
        else:
            primeiro_vencimento = date(hoje.year, hoje.month, vencimento_dia)

        # Garante que não crie datas inválidas (ex: 31 de fevereiro)
        try:
            primeiro_vencimento = primeiro_vencimento.replace(day=vencimento_dia)
        except ValueError:
            primeiro_vencimento = primeiro_vencimento.replace(day=1) - timedelta(days=1)

        # Cria os vencimentos das parcelas
        vencimentos = [
            primeiro_vencimento + relativedelta(months=i) for i in range(self.quant_parcelas)
        ]

        return vencimentos
    
    def atualizar_proximo_pagamento(self):
        parcelas_a_pagar = self.parcelas.filter(status='a_pagar').order_by('data_vencimento')

        if parcelas_a_pagar.exists():
            parcela_atual = parcelas_a_pagar.first()
            parcela_atual.status = 'pago'
            parcela_atual.save()

            # Verifica se ainda há parcelas pendentes
            if self.parcelas.filter(status='a_pagar').exists():
                self.status_parcelamento = 'a_pagar'
            else:
                self.status_parcelamento = 'pago'
                self.status = 'pago'

            self.save()
            return parcela_atual.data_vencimento, self.status_parcelamento

        return None, self.status_parcelamento


    def save(self, *args, **kwargs):
        is_new = self._state.adding  # Verifica se a instância é nova
        super().save(*args, **kwargs)  # Salva a NotaCartao antes de criar as parcelas

        if is_new and not self.parcelas.exists():  # Garante que só cria parcelas se for nova
            vencimentos = self.calcular_vencimentos_parcelas()
            parcelas = [
                Parcela(
                    nota_cartao=self,
                    numero=i + 1,
                    data_vencimento=vencimento,
                    valor=self.valor_parcela,
                    status="a_pagar"
                )
                for i, vencimento in enumerate(vencimentos)
            ]
            Parcela.objects.bulk_create(parcelas)  # Criação eficiente em lote


class Parcela(models.Model):
    nota_cartao = models.ForeignKey(NotaCartao, on_delete=models.CASCADE, related_name='parcelas')
    numero = models.IntegerField()  # Número da parcela (ex: 1, 2, 3...)
    data_vencimento = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('a_pagar', 'À pagar'),
        ('pago', 'Pago'),
    ])

    def __str__(self):
        return f"Parcela {self.numero} de {self.nota_cartao} - Vence em {self.data_vencimento}"


class Pagamento(models.Model):
    parcela = models.ForeignKey(Parcela, on_delete=models.CASCADE, related_name='pagamentos')
    data_pagamento = models.DateField(auto_now_add=True)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Pagamento em {self.data_pagamento} - {self.valor_pago} reais"

class Fatura(models.Model):    
    cartao = models.ForeignKey(Cartao, on_delete=models.SET_NULL, null=True)
    data_pagamento = models.DateField()
    valor = models.IntegerField()
    observacao = models.TextField(null=True, blank=True)

class NotaBoleto(Despesa):
    recipiente = models.CharField(max_length=100, null=True, blank=True)
    quant_boletos = models.IntegerField()
    vencimento = models.DateField(blank=False, null=False)
    num_notafiscal = models.CharField(max_length=50, null=True, blank=True)
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT, null=True, blank=True)

class NotaPix(Despesa):
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)

class NotaEspecie(Despesa):
    pagador = models.CharField(max_length=100)

class Funcionario(models.Model):
    nome = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50)
    custo_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)

    def custo_total_funcionario(self):
        custo_total = 0
        maos_de_obra = MaoDeObra.objects.filter(funcionario=self)
        for mao in maos_de_obra:
            custo_total += mao.despesa.valor
        return custo_total

    def __str__(self):
        return f"{self.nome} - {self.cargo}"
    
class MaoDeObra(models.Model):
    despesa = models.ForeignKey(Despesa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True)
    categoria = models.CharField(
        max_length=20,
        choices=[
            ('adiantamento', 'Adiantamento'),
            ('passagem', 'Passagem'),
            ('alimentacao', 'Alimentação'),
            ('reembolso', 'Reembolso'),
        ]
    )
    valor_reembolso = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.funcionario} - {self.categoria} | {self.despesa.status}"

    

