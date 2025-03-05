from itertools import chain
from django.db import models
from financeiro.models import Aditivo, Adiantamento, BM, Despesa, NotaBoleto, NotaCartao, NotaEspecie, NotaPix
from django.contrib.contenttypes.models import ContentType
from datetime import date, timedelta

from users.models import User


class Escritorio(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cnpj = models.CharField(max_length=18)
    debito_mensal = models.DecimalField(max_digits=10, decimal_places=2, default='0') # mensal, despesas com status de 'à pagar' somadas
    debito_geral = models.DecimalField(max_digits=10, decimal_places=2, default='0') # todas as despesas com status de 'à pagar' somadas
    funcionarios = models.ManyToManyField(User, related_name='funcionarios_escritorio', blank=True)
    admins = models.ManyToManyField(User, related_name='admin_escritorio', blank=True)
    membros = models.ManyToManyField(User, related_name='membros', blank=True)

    def calcular_debito_geral(self):
        despesas_gerais = Despesa.objects.filter(
            tipo_local=ContentType.objects.get_for_model(Escritorio),
            id_local=self.id,
            status='a_pagar'
        )
        total_despesas_gerais = sum(despesa.valor for despesa in despesas_gerais)

        self.debito_geral = total_despesas_gerais
        self.save()
        return self.debito_geral

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
        return self.debito_mensal

    def __str__(self):
        return f"{self.nome} (CNPJ: {self.cnpj})"


class Obra(models.Model):
    imagem_url = models.URLField(blank=True, null=True)
    public_id = models.CharField(max_length=255, null=True, blank=True)

    nome = models.CharField(max_length=100)
    local = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_final = models.DateField(blank=True, null=True)
    valor_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # valor_inicial + aditivos
    valor_receber = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # valor_total - (sum(adiantamentos) + sum(BMs))
    debito_mensal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # mensal, despesas com status de 'à pagar' somadas
    debito_geral = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # todas as despesas com status de 'à pagar' somadas
    custo_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # todas as despesas somadas geral (independente do status)
    prazo_inicial = models.DateField()
    prazo_atual = models.DateField(blank=True, null=True) #prazo_inicial + dias de aditivo do tipo prazo

    escritorio = models.ForeignKey(Escritorio, on_delete=models.CASCADE, related_name="obras")

    # Função para calcular o valor total
    def calcular_valor_total(self):
        aditivos = Aditivo.objects.filter(obra=self)

        total_aditivos = sum(aditivo.valor for aditivo in aditivos if aditivo.valor is not None)
        
        # Verifica se valor_inicial e total_aditivos não são None
        self.valor_total = self.valor_inicial + total_aditivos if self.valor_inicial is not None else 0
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

    def calcular_debito_mensal(self, mes=None, ano=None, salvar=True):
        hoje = date.today()
        mes = mes or hoje.month
        ano = ano or hoje.year

        tipo_local_obra = ContentType.objects.get_for_model(Obra)

        # Obtém todas as notas filtradas pelo mês e ano especificados
        notas = list(chain(
            NotaBoleto.objects.filter(tipo_local=tipo_local_obra, id_local=self.id, status='a_pagar', data__month=mes, data__year=ano),
            NotaEspecie.objects.filter(tipo_local=tipo_local_obra, id_local=self.id, status='a_pagar', data__month=mes, data__year=ano),
            NotaPix.objects.filter(tipo_local=tipo_local_obra, id_local=self.id, status='a_pagar', data__month=mes, data__year=ano),
            NotaCartao.objects.filter(
                tipo_local=tipo_local_obra,
                id_local=self.id,
                status='a_pagar',
                parcelas__status='a_pagar',
                parcelas__data_vencimento__month=mes,
                parcelas__data_vencimento__year=ano
            ).distinct()  # Evita duplicação caso haja várias parcelas no mesmo mês
        ))
        
        # Soma todos os valores das notas
        total_mensal = sum(nota.valor for nota in notas)

        # Atualiza e salva a Obra apenas se salvar=True
        if salvar:
            self.debito_mensal = total_mensal
            self.save(update_fields=['debito_mensal'])  # Otimiza o update para não salvar tudo

        return total_mensal
    

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
    
    def calcular_total_adiantamentos(self):
        adiamentos = Adiantamento.objects.filter(obra=self)
        total_adiamentos = sum(adiamento.valor for adiamento in adiamentos) if adiamentos.exists() else 0
        return total_adiamentos

    def calcular_total_bms(self):
        bms = BM.objects.filter(obra=self)
        total_bms = sum(bm.valor for bm in bms) if bms.exists() else 0
        return total_bms

    def calcular_soma_adiantamento_bm(self):
        total_adiantamentos = self.calcular_total_adiantamentos()
        total_bms = self.calcular_total_bms()
        return total_adiantamentos + total_bms

    def __str__(self):
        return self.nome

        
class AcessoEscritorio(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]

    user_receptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_receptor')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin')
    ADMINISTRADOR = 'ADM'
    FUNCIONARIO = 'FUNC'
    CARGO_CHOICES = [
        (ADMINISTRADOR, 'Administrador'),
        (FUNCIONARIO, 'Funcionário'),
    ]
    
    cargo = models.CharField(
        max_length=4,
        choices=CARGO_CHOICES,
        blank=False,
    )
    escritorio = models.ForeignKey(Escritorio, on_delete=models.CASCADE, related_name='escritorio')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')