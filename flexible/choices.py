import html

from django.db import models
from django.utils.text import slugify

from flexible.models import TextField, IntegerField, \
                            DecimalField, DateField, \
                            DurationField, EmailField


# the abstract base for a flexible field choice
class FieldChoice(models.Model):
    index = models.IntegerField(default=0)
    slug = models.SlugField(max_length=256, blank=False)

    @property
    def verbose_value(self):
        """
        The verbose value for the field choice
        :return: string
            The verbose value
        """
        return self._value

    @property
    def escaped_value(self):
        """
        The value escaped for html rendering
        :return: string
            The escaped value
        """
        return self._value.replace('\'', "\\'")

    @property
    def _value(self):
        """
        The raw value
        :return:
            The raw value
        """
        raise NotImplementedError

    def copy(self, field):
        """
        Copies the field choice to another field
        :param field: Field
            The target field to copy to
        :return: FieldChoice
            The field choice
        """
        raise NotImplementedError

    def save(self, *args, **kwargs):
        self.slug = slugify(self._value)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Field choices"
        abstract = True


# a choice for a flexible text field
class TextFieldChoice(FieldChoice):
    field = models.ForeignKey(TextField, on_delete=models.CASCADE)
    value = models.CharField(max_length=256, blank=False)

    @property
    def _value(self):
        return self.value

    def copy(self, field):
        choice = TextFieldChoice.objects.get(pk=self.pk)
        choice.pk = None
        choice.field = field
        choice.save()

        return choice

    class Meta:
        verbose_name_plural = "Text Field choices"
        unique_together = (('field', 'value'), ('field', 'slug'))

    def __str__(self):
        return f'Choice \'{self.value}\' for \'{self.field}\''


# a choice for a flexible integer field
class IntegerFieldChoice(FieldChoice):
    field = models.ForeignKey(IntegerField, on_delete=models.CASCADE)
    value = models.IntegerField()

    @property
    def _value(self):
        return self.value

    def copy(self, field):
        choice = IntegerFieldChoice.objects.get(pk=self.pk)
        choice.pk = None
        choice.field = field
        choice.save()

        return choice

    class Meta:
        verbose_name_plural = "Integer Field choices"
        unique_together = (('field', 'value'), ('field', 'slug'))

    def __str__(self):
        return f'Choice \'{self.value}\' for \'{self.field}\''


# a choice for a flexible decimal field
class DecimalFieldChoice(FieldChoice):
    field = models.ForeignKey(DecimalField, on_delete=models.CASCADE)
    value = models.DecimalField(decimal_places=DecimalField.decimal_places,
                                max_digits=DecimalField.max_digits)

    @property
    def _value(self):
        return self.value

    def copy(self, field):
        choice = DecimalFieldChoice.objects.get(pk=self.pk)
        choice.pk = None
        choice.field = field
        choice.save()

        return choice

    class Meta:
        verbose_name_plural = "Decimal Field choices"
        unique_together = (('field', 'value'), ('field', 'slug'))

    def __str__(self):
        return f'Choice \'{self.value}\' for \'{self.field}\''


# a choice for a flexible duration field
class DurationFieldChoice(FieldChoice):
    field = models.ForeignKey(DurationField, on_delete=models.CASCADE)
    value = models.DurationField()

    @property
    def _value(self):
        return self.value

    def copy(self, field):
        choice = DurationFieldChoice.objects.get(pk=self.pk)
        choice.pk = None
        choice.field = field
        choice.save()

        return choice

    class Meta:
        verbose_name_plural = "Duration Field choices"
        unique_together = (('field', 'value'), ('field', 'slug'))

    def __str__(self):
        return f'Choice \'{self.value}\' for \'{self.field}\''


# a choice for a flexible date field
class DateFieldChoice(FieldChoice):
    field = models.ForeignKey(DateField, on_delete=models.CASCADE)
    value = models.DateField()

    @property
    def _value(self):
        return self.value

    def copy(self, field):
        choice = DateFieldChoice.objects.get(pk=self.pk)
        choice.pk = None
        choice.field = field
        choice.save()

        return choice

    class Meta:
        verbose_name_plural = "Date Field choices"
        unique_together = (('field', 'value'), ('field', 'slug'))

    def __str__(self):
        return f'Choice \'{self.value}\' for \'{self.field}\''


# a choice for a flexible email field
class EmailFieldChoice(FieldChoice):
    field = models.ForeignKey(EmailField, on_delete=models.CASCADE)
    value = models.EmailField()

    @property
    def _value(self):
        return self.value

    def copy(self, field):
        choice = EmailFieldChoice.objects.get(pk=self.pk)
        choice.pk = None
        choice.field = field
        choice.save()

        return choice

    class Meta:
        verbose_name_plural = "Email Field choices"
        unique_together = (('field', 'value'), ('field', 'slug'))

    def __str__(self):
        return f'Choice \'{self.value}\' for \'{self.field}\''
