# Generated by Django 2.2.9 on 2020-01-16 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('batch', '0004_auto_20200115_1343'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='updated_on',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
