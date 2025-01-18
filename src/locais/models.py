from django.db import models

class Obra(models.Model):
    nome = models.CharField(max_length=100)
    local = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_final = models.DateField(blank=True, null=True)
    valor_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2) # valor_inicial - aditivos
    valor_receber = models.DecimalField(max_digits=10, decimal_places=2) # valor_total - (sum(adiantamentos) + sum(BMs))
    debito_mensal = models.DecimalField(max_digits=10, decimal_places=2) # mensal, despesas com status de 'à pagar' somadas
    debito_geral = models.DecimalField(max_digits=10, decimal_places=2) # todas as despesas com status de 'à pagar' somadas
    custo_total = models.DecimalField(max_digits=10, decimal_places=2) # todas as despesas somadas geral (independente do status)
    prazo_inicial = models.DateField()
    prazo_atual = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Escritorio(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cnpj = models.CharField(max_length=18)
    ceo = models.CharField(max_length=100)
    debito_mensal = models.DecimalField(max_digits=10, decimal_places=2) # mensal, despesas com status de 'à pagar' somadas
    debito_geral = models.DecimalField(max_digits=10, decimal_places=2) # todas as despesas com status de 'à pagar' somadas

    def __str__(self):
        return f"{self.nome} (CNPJ: {self.cnpj})"