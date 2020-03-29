import logging

from django.db import models
from django.core.exceptions import ValidationError

from polymorphic.models import PolymorphicModel

from flexible.models import Model, Field, DateField, DecimalField, \
    NON_POLYMORPHIC_CASCADE

logger = logging.getLogger(__file__)


class Action(PolymorphicModel):
    exception_messages = {
        'model_missing_field': "Provided model does not contain field named %",
        'model_field_mismatch': "Provided model contains field named % but type does not match",
    }

    model = models.ForeignKey(Model, on_delete=NON_POLYMORPHIC_CASCADE)

    def execute(self, obj):
        raise NotImplementedError

    def js(self, indent=''):
        raise NotImplementedError

    def copy(self, model):
        raise NotImplementedError

    class Meta:
        verbose_name_plural = "Actions"

    def __str__(self):
        return f"Base action"


class ShowFieldAction(Action):
    field = models.ForeignKey(Field, on_delete=NON_POLYMORPHIC_CASCADE)

    def execute(self, obj):
        # field is shown, so ensure it is there if required
        value = obj.get(self.field.name)
        if self.field.required and not value or value is None:
            raise ValidationError(f"{self.field} is shown and required but is not found")

    def js(self, indent=''):
        js = f'$(\'#{self.field.div_id}\').prop(\'hidden\', false);'
        if self.field.required:
            js = f'{js}$(\'#{self.field.input_id}\').prop(\'required\', true);'
        return js

    def copy(self, model):
        action = ShowFieldAction.objects.get(pk=self.pk)
        field = model.fields.get(self.field.name)

        if field is None:
            raise RuntimeError(self.exception_messages['model_missing_field'] % self.field.name)
        if not isinstance(field, type(action.field)):
            raise RuntimeError(self.exception_messages['model_field_mismatch'] % self.field.name)

        action.id = None
        action.pk = None
        action.field = field
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Show Field Actions"

    def __str__(self):
        return f"Show field {self.field}"


class HideFieldAction(Action):
    field = models.ForeignKey(Field, on_delete=NON_POLYMORPHIC_CASCADE)

    def execute(self, obj):
        pass

    def js(self, indent=''):
        js = f'$(\'#{self.field.div_id}\').prop(\'hidden\', true);'
        if self.field.required:
            js = f'{js}$(\'#{self.field.input_id}\').prop(\'required\', false);'
        return js

    def copy(self, model):
        action = HideFieldAction.objects.get(pk=self.pk)
        field = model.fields.get(self.field.name)

        if field is None:
            raise RuntimeError(self.exception_messages['model_missing_field'] % self.field.name)
        if not isinstance(field, type(action.field)):
            raise RuntimeError(self.exception_messages['model_field_mismatch'] % self.field.name)

        action.id = None
        action.pk = None
        action.field = field
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Hide Field Actions"

    def __str__(self):
        return f"Hide field {self.field}"


class ReturnIntegerAction(Action):
    value = models.IntegerField(default=0)

    def execute(self, obj):
        return self.value

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnIntegerAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return Integer Actions"

    def __str__(self):
        return f"Return integer {self.value}"


class LogMessageAction(Action):
    message = models.CharField(max_length=256, blank=False)

    def execute(self, obj):
        logger.info(self.message, stack=True)
        return None

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = LogMessageAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Log message Actions"

    def __str__(self):
        return f"Log message {self.message}"


class FormatDateFieldAction(Action):
    format = models.CharField(max_length=256, blank=False)
    field = models.ForeignKey(DateField, on_delete=NON_POLYMORPHIC_CASCADE)

    def execute(self, obj):
        field = obj.get(self.field.name)
        if field is None:
            return None

        return field.value.strftime(self.format)

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = FormatDateFieldAction.objects.get(pk=self.pk)
        field = model.fields.get(self.field.name)

        if field is None:
            raise RuntimeError(self.exception_messages['model_missing_field'] % self.field.name)
        if not isinstance(field, type(action.field)):
            raise RuntimeError(self.exception_messages['model_field_mismatch'] % self.field.name)

        action.id = None
        action.pk = None
        action.model = model
        action.field = field
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Format DateField Actions"

    def __str__(self):
        return f"Format {self.field} with {self.format}"


class ReturnAttributeAction(Action):
    attribute_name = models.CharField(max_length=256, blank=False)

    def execute(self, obj):
        if hasattr(obj, self.attribute_name):
            return getattr(obj, self.attribute_name)
        else:
            logger.info(f"obj does not have attribute {self.attribute_name}", stack=True)

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnAttributeAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return attribute action"

    def __str__(self):
        return f"Return attribute {self.attribute_name}"


class ReturnStringAction(Action):
    value = models.TextField(blank=False)

    def execute(self, obj):
        return self.value

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnStringAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return string action"

    def __str__(self):
        return f"Return string {self.value}"


class ReturnDecimalAction(Action):
    value = models.DecimalField(max_digits=DecimalField.max_digits,
                                decimal_places=DecimalField.decimal_places)

    def execute(self, obj):
        return self.value

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnDecimalAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return decimal action"

    def __str__(self):
        return f"Return decimal {self.value}"


class ReturnBooleanAction(Action):
    value = models.BooleanField(default=False)

    def execute(self, obj):
        return self.value

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnBooleanAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return boolean action"

    def __str__(self):
        return f"Return boolean {self.value}"


class ReturnDateAction(Action):
    value = models.DateField()

    def execute(self, obj):
        return self.value

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnDateAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return date action"

    def __str__(self):
        return f"Return date {self.value}"


class ReturnDurationAction(Action):
    value = models.DurationField()

    def execute(self, obj):
        return self.value

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnDurationAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return duration action"

    def __str__(self):
        return f"Return duration {self.value}"


class ReturnEmailAction(Action):
    value = models.EmailField()

    def execute(self, obj):
        return self.value

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnEmailAction.objects.get(pk=self.pk)

        action.id = None
        action.pk = None
        action.model = model
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return email action"

    def __str__(self):
        return f"Return email {self.value}"


class ReturnDaysBetweenDatesAction(Action):
    start = models.ForeignKey(DateField, on_delete=NON_POLYMORPHIC_CASCADE, related_name='start')
    end = models.ForeignKey(DateField, on_delete=NON_POLYMORPHIC_CASCADE, related_name='end')

    def execute(self, obj):
        start = obj.get(self.start.name)
        end = obj.get(self.end.name)

        if start is None or end is None:
            return None

        return (end.value - start.value).days

    def js(self, indent=''):
        super().js(indent)

    def copy(self, model):
        action = ReturnDaysBetweenDatesAction.objects.get(pk=self.pk)
        start = model.fields.get(self.start.name)

        if start is None:
            raise RuntimeError(self.exception_messages['model_missing_field'] % self.start.name)
        if not isinstance(start, type(action.field)):
            raise RuntimeError(self.exception_messages['model_field_mismatch'] % self.start.name)

        end = model.fields.get(self.end.name)

        if end is None:
            raise RuntimeError(self.exception_messages['model_missing_field'] % self.end.name)
        if not isinstance(end, type(action.field)):
            raise RuntimeError(self.exception_messages['model_field_mismatch'] % self.end.name)

        action.id = None
        action.pk = None
        action.model = model
        action.start = start
        action.end = end
        action.save()

        return action

    class Meta:
        verbose_name_plural = "Return days between dates action"

    def __str__(self):
        return f"Return dates between {self.start} and {self.end}"
