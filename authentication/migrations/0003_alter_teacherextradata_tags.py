# Generated by Django 4.1 on 2022-08-24 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_teacherextradata_acronym"),
    ]

    operations = [
        migrations.AlterField(
            model_name="teacherextradata",
            name="tags",
            field=models.TextField(blank=True, null=True),
        ),
    ]
