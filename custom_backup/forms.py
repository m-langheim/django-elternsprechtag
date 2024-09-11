from django import forms


class BackupRestoreForm(forms.Form):
    backup_data = forms.JSONField()
