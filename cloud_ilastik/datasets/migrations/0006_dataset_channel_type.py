# Generated by Django 2.2.9 on 2020-03-25 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datasets", "0005_auto_20200117_1549"),
    ]

    operations = [
        migrations.AddField(
            model_name="dataset",
            name="channel_type",
            field=models.CharField(
                choices=[("Intensity", "intensity"), ("IndexedColor", "indexed")], default="intensity", max_length=15
            ),
        ),
    ]
