from datetime import date, timedelta
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator, MaxValueValidator


class Banco(models.Model):
    nome = models.CharField(max_length=100)
    logo_path = models.CharField(
        max_length=255,
        blank=True, 
        default='assets/bancosLogo/default_logo.png'
    )
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
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)
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
    ])

    # GFK para associar com Obra ou Escritório
    tipo_local = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    id_local = models.PositiveIntegerField()
    local = GenericForeignKey('tipo_local', 'id_local')

    def __str__(self):
        nome_limite = self.nome[:20]
        if len(self.nome) > 20:
            nome_limite += '...'
        return f"{self.data} | {self.local} | {nome_limite} | ({self.modalidade} | R${self.valor})"

class Cartao(models.Model):
    nome = models.CharField(max_length=100)
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)
    final = models.CharField(max_length=4)
    vencimento = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(31)
        ],
        help_text="Insira um número entre 1 e 31"
    )
    quant_dias = models.IntegerField()
    melhor_dia = models.DateField(blank=True, null=True) # vencimento - quant_dias
    
    def calcular_melhor_dia(self):
        hoje = date.today()

        if self.vencimento and self.quant_dias:
            try:
                # Tenta criar a data com o vencimento atual
                vencimento_data_atual = date(hoje.year, hoje.month, self.vencimento)
            except ValueError:
                # Caso o vencimento seja inválido (exemplo: 31 de fevereiro)
                if hoje.month == 12:  # Se for dezembro, ajusta para janeiro do próximo ano
                    vencimento_data_atual = date(hoje.year + 1, 1, 1) - timedelta(days=1)
                else:
                    # Primeiro dia do próximo mês, menos um dia (último dia do mês atual)
                    vencimento_data_atual = date(hoje.year, hoje.month + 1, 1) - timedelta(days=1)

            # Calcula o melhor dia com base em quant_dias
            self.melhor_dia = vencimento_data_atual - timedelta(days=self.quant_dias)
            self.save()

        return self.melhor_dia
    
    def __str__(self):
        return f"{self.final} | {self.nome} | {self.banco}"


class NotaCartao(Despesa):
    cartao = models.ForeignKey(Cartao, on_delete=models.SET_NULL, null=True)
    quant_parcelas = models.IntegerField()
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)

class NotaBoleto(Despesa):
    recipiente = models.CharField(max_length=100)
    quant_boletos = models.IntegerField()
    vencimento = models.DateField(blank=False, null=False)
    num_notafiscal = models.CharField(max_length=50)
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)

class NotaPix(Despesa):
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)

class NotaEspecie(Despesa):
    pagador = models.CharField(max_length=100)

class Funcionario(models.Model):
    nome = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50)

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

    

