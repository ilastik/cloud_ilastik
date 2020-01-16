# Generated by Django 2.2.9 on 2020-01-16 11:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('datasets', '0002_auto_20200115_1010'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='is_public',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dataset',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
