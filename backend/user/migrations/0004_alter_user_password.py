# Generated by Django 3.2 on 2024-01-12 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_favorite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(help_text='Ваш Пароль', max_length=50, verbose_name='Пароль'),
        ),
    ]
