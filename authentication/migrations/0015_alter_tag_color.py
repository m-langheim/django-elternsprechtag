# Generated by Django 4.1 on 2022-10-04 13:18

import authentication.models
import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0014_alter_tag_color"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="color",
            field=colorfield.fields.ColorField(
                default=authentication.models.generate_new_color,
                image_field=None,
                max_length=18,
                samples=None,
            ),
        ),
    ]
