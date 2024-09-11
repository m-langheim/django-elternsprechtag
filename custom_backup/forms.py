from django import forms


class BackupRestoreForm(forms.Form):
    backup_file = forms.FileField()
