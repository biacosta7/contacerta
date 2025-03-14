# Generated by Django 5.1.5 on 2025-01-27 15:13

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('locais', '0002_alter_obra_custo_total_alter_obra_debito_geral_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banco',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('logo_path', models.CharField(blank=True, default='assets/bancosLogo/default_logo.png', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Despesa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('forma_pag', models.CharField(choices=[('boleto', 'Boleto'), ('cartao', 'Cartão'), ('pix', 'Pix'), ('especie', 'Espécie')], max_length=20)),
                ('data', models.DateField()),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('observacao', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('a_pagar', 'À pagar'), ('pago', 'Pago')], max_length=20)),
                ('data_pagamento', models.DateField(blank=True, null=True)),
                ('modalidade', models.CharField(choices=[('mao_de_obra', 'Mão de Obra'), ('insumos', 'Insumos'), ('combustivel', 'Combustível')], max_length=50)),
                ('id_local', models.PositiveIntegerField()),
                ('tipo_local', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
        ),
        migrations.CreateModel(
            name='Funcionario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('cargo', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Aditivo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('valor', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('dias', models.IntegerField(blank=True, null=True)),
                ('data', models.DateField()),
                ('modalidade', models.CharField(choices=[('prazo', 'Prazo'), ('valor', 'Valor')], max_length=10)),
                ('observacao', models.TextField(blank=True)),
                ('obra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='locais.obra')),
                ('banco', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financeiro.banco')),
            ],
        ),
        migrations.CreateModel(
            name='Adiantamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('data', models.DateField()),
                ('observacao', models.TextField(blank=True)),
                ('obra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='locais.obra')),
                ('banco', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financeiro.banco')),
            ],
        ),
        migrations.CreateModel(
            name='BM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                ('data', models.DateField()),
                ('codigo', models.CharField(blank=True, max_length=50)),
                ('observacao', models.TextField(blank=True)),
                ('banco', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financeiro.banco')),
                ('obra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='locais.obra')),
            ],
        ),
        migrations.CreateModel(
            name='Cartao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('final', models.CharField(max_length=4)),
                ('vencimento', models.IntegerField(help_text='Insira um número entre 1 e 31', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(31)])),
                ('quant_dias', models.IntegerField()),
                ('melhor_dia', models.DateField(blank=True, null=True)),
                ('banco', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financeiro.banco')),
            ],
        ),
        migrations.CreateModel(
            name='NotaEspecie',
            fields=[
                ('despesa_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='financeiro.despesa')),
                ('pagador', models.CharField(max_length=100)),
            ],
            bases=('financeiro.despesa',),
        ),
        migrations.CreateModel(
            name='MaoDeObra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('categoria', models.CharField(choices=[('adiantamento', 'Adiantamento'), ('passagem', 'Passagem'), ('alimentacao', 'Alimentação'), ('reembolso', 'Reembolso')], max_length=20)),
                ('despesa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='financeiro.despesa')),
                ('funcionario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='financeiro.funcionario')),
            ],
        ),
        migrations.CreateModel(
            name='NotaBoleto',
            fields=[
                ('despesa_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='financeiro.despesa')),
                ('recipiente', models.CharField(max_length=100)),
                ('quant_boletos', models.IntegerField()),
                ('vencimento', models.DateField()),
                ('num_notafiscal', models.CharField(max_length=50)),
                ('banco', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financeiro.banco')),
            ],
            bases=('financeiro.despesa',),
        ),
        migrations.CreateModel(
            name='NotaCartao',
            fields=[
                ('despesa_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='financeiro.despesa')),
                ('quant_parcelas', models.IntegerField()),
                ('valor_parcela', models.DecimalField(decimal_places=2, max_digits=10)),
                ('cartao', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='financeiro.cartao')),
            ],
            bases=('financeiro.despesa',),
        ),
        migrations.CreateModel(
            name='NotaPix',
            fields=[
                ('despesa_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='financeiro.despesa')),
                ('banco', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='financeiro.banco')),
            ],
            bases=('financeiro.despesa',),
        ),
    ]
