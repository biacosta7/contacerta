# Generated by Django 5.1.5 on 2025-02-09 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0009_fatura'),
    ]

    operations = [
        migrations.AddField(
            model_name='fatura',
            name='valor',
            field=models.IntegerField(default='0'),
            preserve_default=False,
        ),
    ]
