# Generated by Django 5.1.5 on 2025-02-10 18:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('locais', '0004_escritorio_admins_escritorio_funcionarios'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='escritorio',
            name='ceo',
        ),
    ]
