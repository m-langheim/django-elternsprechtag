from django.db.models import F, Func, FloatField


class AbsoluteDifference(Func):
    function = "ABS"
    template = "%(function)s(%(expressions)s)"
    output_field = FloatField()
