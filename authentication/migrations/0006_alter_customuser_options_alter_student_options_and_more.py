# Generated by Django 4.2 on 2023-10-14 20:49

import authentication.models
import colorfield.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_alter_customuser_email_alter_customuser_first_name_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'verbose_name': 'Benutzer', 'verbose_name_plural': 'Benutzer'},
        ),
        migrations.AlterModelOptions(
            name='student',
            options={'verbose_name': 'Student', 'verbose_name_plural': 'Schüler'},
        ),
        migrations.AlterModelOptions(
            name='tag',
            options={'verbose_name': 'Tag', 'verbose_name_plural': 'Tags'},
        ),
        migrations.AlterModelOptions(
            name='teacherextradata',
            options={'verbose_name': 'Zusatzinformationen zu einer Lehrkraft', 'verbose_name_plural': 'Zusatzinformationen zu Lehrkräften'},
        ),
        migrations.AlterModelOptions(
            name='upcomming_user',
            options={'verbose_name': 'Zukünftiger Nutzer', 'verbose_name_plural': 'Zukünftige Nutzer'},
        ),
        migrations.AlterField(
            model_name='customuser',
            name='date_joined',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Zugangsdatum'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True, verbose_name='E-Mail'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=48, verbose_name='Vorname'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=48, verbose_name='Nachname'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.IntegerField(choices=[(0, 'Elternteil'), (1, 'Lehrer'), (2, 'Anderes')], default=2, verbose_name='Rolle'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='students',
            field=models.ManyToManyField(blank=True, to='authentication.student', verbose_name='Schüler'),
        ),
        migrations.AlterField(
            model_name='student',
            name='child_email',
            field=models.EmailField(max_length=200, null=True, verbose_name='Email des Kindes'),
        ),
        migrations.AlterField(
            model_name='student',
            name='class_name',
            field=models.CharField(default='', max_length=2, verbose_name='Klassenname'),
        ),
        migrations.AlterField(
            model_name='student',
            name='first_name',
            field=models.CharField(max_length=48, verbose_name='Vorname'),
        ),
        migrations.AlterField(
            model_name='student',
            name='last_name',
            field=models.CharField(max_length=48, verbose_name='Nachname'),
        ),
        migrations.AlterField(
            model_name='student',
            name='registered',
            field=models.BooleanField(default=False, verbose_name='Elternteil registriert'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=colorfield.fields.ColorField(default=authentication.models.generate_new_color, image_field=None, max_length=18, samples=None, verbose_name='Farbe'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=32, verbose_name='Allgemeiner Name'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='synonyms',
            field=models.TextField(blank=True, null=True, verbose_name='Synonyme Bezeichnungen'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='acronym',
            field=models.CharField(default='', max_length=3, verbose_name='Abkürzung'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='image',
            field=models.ImageField(default='default.jpg', upload_to='teacher_pics/', verbose_name='Profilbild'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='room',
            field=models.IntegerField(blank=True, null=True, verbose_name='Raum'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='tags',
            field=models.ManyToManyField(blank=True, to='authentication.tag', verbose_name='Tags'),
        ),
        migrations.AlterField(
            model_name='teacherextradata',
            name='teacher',
            field=models.OneToOneField(limit_choices_to={'role': 1}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Nutzerobjekt der Lehrkraft'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='access_key',
            field=models.CharField(default=authentication.models.generate_unique_code, max_length=12, verbose_name='Access token'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Erstellungszeitpunkt'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='email_send',
            field=models.BooleanField(default=False, verbose_name='Email send'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='otp',
            field=models.CharField(default=authentication.models.generate_unique_otp, max_length=6, verbose_name='Einmalkennwort'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='otp_verified',
            field=models.BooleanField(default=False, verbose_name='Einmalkennwort wurde bestätigt'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='otp_verified_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Time of OTP key verification'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='student',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='authentication.student', verbose_name='Student'),
        ),
        migrations.AlterField(
            model_name='upcomming_user',
            name='user_token',
            field=models.CharField(default=authentication.models.generate_unique_code, max_length=12, primary_key=True, serialize=False, verbose_name='Nutzer Token'),
        ),
    ]
