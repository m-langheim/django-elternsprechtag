# Generated by Django 4.0.4 on 2022-05-23 13:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0005_student_child_email_upcomming_user_student'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upcomming_user',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='login.student'),
        ),
    ]
