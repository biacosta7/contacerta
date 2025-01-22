from django.db import models
from financeiro.models import Aditivo, Adiantamento, BM, Despesa
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta

class Obra(models.Model):
    nome = models.CharField(max_length=100)
    local = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_final = models.DateField(blank=True, null=True)
    valor_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # valor_inicial - aditivos
    valor_receber = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # valor_total - (sum(adiantamentos) + sum(BMs))
    debito_mensal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # mensal, despesas com status de 'à pagar' somadas
    debito_geral = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # todas as despesas com status de 'à pagar' somadas
    custo_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # todas as despesas somadas geral (independente do status)
    prazo_inicial = models.DateField()
    prazo_atual = models.DateField(blank=True, null=True) #prazo_inicial + dias de aditivo do tipo prazo

    # Função para calcular o valor total
    def calcular_valor_total(self):
        aditivos = Aditivo.objects.filter(obra=self)
        total_aditivos = sum(aditivo.valor for aditivo in aditivos)
        
        # Verifica se valor_inicial e total_aditivos não são None
        self.valor_total = self.valor_inicial - total_aditivos if self.valor_inicial is not None else 0
        self.save()
        return self.valor_total
    
    # Função para calcular o valor a receber
    def calcular_valor_receber(self):
        adiantamentos = Adiantamento.objects.filter(obra=self)
        total_adiantamentos = sum(adiantamento.valor for adiantamento in adiantamentos)

        bms = BM.objects.filter(obra=self)
        total_bms = sum(bm.valor for bm in bms)
        
        # Verifica se valor_total, total_adiantamentos e total_bms não são None
        self.valor_receber = (self.valor_total or 0) - (total_adiantamentos + total_bms)
        self.save()
        return self.valor_receber
    
    def calcular_debito_geral(self):
        despesas_gerais = Despesa.objects.filter(
            tipo_local=ContentType.objects.get_for_model(Obra),
            id_local=self.id,
            status='a_pagar'
        )
        total_despesas_gerais = sum(despesa.valor for despesa in despesas_gerais)

        self.debito_geral = total_despesas_gerais
        self.save()
        return self.debito_geral

    def calcular_debito_mensal(self, mes=None, ano=None):
        hoje = date.today()

        mes = mes if mes else hoje.month
        ano = ano if ano else hoje.year

        despesas_mensais = Despesa.objects.filter(
            tipo_local=ContentType.objects.get_for_model(Obra),
            id_local=self.id,
            status='a_pagar',
            data__month=mes,
            data__year=ano
        )
        total_mensal = sum(despesa.valor for despesa in despesas_mensais)
        self.debito_mensal = total_mensal
        self.save()
        return self.debito_mensal

    def calcular_custo_total(self):
        despesas = Despesa.objects.filter(
            tipo_local=ContentType.objects.get_for_model(Obra),
            id_local=self.id
        )
        total_despesas = sum(despesa.valor for despesa in despesas)

        self.custo_total = total_despesas
        self.save()
        return self.custo_total
    
    def calcular_prazo_atual(self):
        aditivos = Aditivo.objects.filter(obra=self, modalidade='prazo')

        total_dias_aditivos = sum(aditivo.dias for aditivo in aditivos)

        if self.prazo_inicial:
            self.prazo_atual = self.prazo_inicial + timedelta(days=total_dias_aditivos)
            self.save()
        return self.prazo_atual

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

    def calcular_debito_geral(self):
        despesas_gerais = Despesa.objects.filter(
            tipo_local=ContentType.objects.get_for_model(Escritorio),
            id_local=self.id,
            status='a_pagar'
        )
        total_despesas_gerais = sum(despesa.valor for despesa in despesas_gerais)

        self.debito_geral = total_despesas_gerais
        self.save()

    def calcular_debito_mensal(self, mes=None, ano=None):
        hoje = date.today()

        # Se mês ou ano não forem passados, utiliza o mês e ano atual
        mes = mes if mes else hoje.month
        ano = ano if ano else hoje.year

        despesas_mensais = Despesa.objects.filter(
            tipo_local=ContentType.objects.get_for_model(Escritorio),
            id_local=self.id,
            status='a_pagar',
            data__month=mes,
            data__year=ano
        )
        total_mensal = sum(despesa.valor for despesa in despesas_mensais)
        self.debito_mensal = total_mensal
        self.save()

    def __str__(self):
        return f"{self.nome} (CNPJ: {self.cnpj})"