# Generated by Django 2.2.9 on 2020-01-13 10:18

import batch.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('batch', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='num_dimensions',
        ),
        migrations.AddField(
            model_name='project',
            name='min_block_size_x',
            field=models.IntegerField(default=0, validators=[batch.models.not_negative]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='min_block_size_y',
            field=models.IntegerField(default=0, validators=[batch.models.not_negative]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='min_block_size_z',
            field=models.IntegerField(default=0, validators=[batch.models.not_negative]),
        ),
        migrations.AddField(
            model_name='project',
            name='num_channels',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
    ]
