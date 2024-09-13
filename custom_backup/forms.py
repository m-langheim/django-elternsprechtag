from django import forms


class RestoreFileForm(forms.Form):
    backup_file = forms.FileField()


class RestoreForm(forms.Form):
    flush = forms.BooleanField(label="Flush Database", required=False)
    deletedirs = forms.BooleanField(label="Delete BACKUP_DIRS", required=False)


class CreateForm(forms.Form):
    compress = forms.BooleanField(label="compress Backup", required=False, initial=True)
