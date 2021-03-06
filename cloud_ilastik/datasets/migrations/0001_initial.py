# Generated by Django 2.2.9 on 2020-01-13 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('url', models.URLField()),
                ('size_t', models.PositiveIntegerField(default=1)),
                ('size_z', models.PositiveIntegerField(default=1)),
                ('size_y', models.PositiveIntegerField()),
                ('size_x', models.PositiveIntegerField()),
                ('size_c', models.PositiveIntegerField(default=1)),
            ],
        ),
    ]
