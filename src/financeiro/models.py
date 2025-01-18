from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Adiantamento(models.Model):
    nome = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField()
    banco = models.CharField(max_length=100)
    observacao = models.TextField(blank=True)
    obra = models.ForeignKey('locais.Obra', on_delete=models.CASCADE)

class Aditivo(models.Model):
    nome = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dias = models.IntegerField(null=True, blank=True)
    data = models.DateField()
    banco = models.CharField(max_length=100)
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
    data = models.DateField()
    banco = models.CharField(max_length=100)
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
    data = models.DateField()
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
        return f"{self.local} | {nome_limite} ({self.modalidade} | R${self.valor})"

class Cartao(models.Model):
    nome = models.CharField(max_length=100)
    banco = models.CharField(max_length=100)
    final = models.CharField(max_length=4)
    vencimento = models.DateField()
    quant_dias = models.IntegerField()
    melhor_dia = models.DateField() # vencimento - quant_dias

    def __str__(self):
        return f"{self.final} | {self.nome} | {self.banco}"

class NotaCartao(Despesa):
    cartao = models.ForeignKey(Cartao, on_delete=models.SET_NULL, null=True)
    quant_parcelas = models.IntegerField()
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2)

class NotaBoleto(Despesa):
    recipiente = models.CharField(max_length=100)
    quant_boletos = models.IntegerField()
    vencimento = models.DateField()
    num_notafiscal = models.CharField(max_length=50)
    banco = models.CharField(max_length=100)

class NotaPix(Despesa):
    banco = models.CharField(max_length=100)

class NotaEspecie(Despesa):
    pagador = models.CharField(max_length=100)

class Funcionario(models.Model):
    nome = models.CharField(max_length=100)
    cargo = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nome} - {self.cargo}"
    
class MaoDeObra(Despesa):
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

    def __str__(self):
        return f"{self.funcionario} - {self.categoria}"