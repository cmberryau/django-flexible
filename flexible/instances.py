from django.db import models

from flexible.models import DecimalField


# the abstract base for Field instances
class FieldInstance(models.Model):
    @property
    def value_json(self):
        """
        Returns the field instance value ready for json serialisation
        :return: dict
            The field instance value ready for json serialisation
        """
        return self.field.to_json(self._value)

    @property
    def value_post_dict(self):
        """
        The FieldInstance value as a decompressed post dict
        :return: string
            The decompressed FieldInstance value
        """
        return self.field.to_post_dict(self._value)

    @property
    def value_form(self):
        """
        Returns the field instance value ready for django forms
        :return:
            The field instance value ready ready for django forms
        """
        return self._value

    @property
    def _value(self):
        raise NotImplementedError

    # the field model for this field instance
    field = models.ForeignKey('Field', on_delete=models.CASCADE)
    # the model instance this field instance belongs to
    model_instance = models.ForeignKey('ModelInstance', on_delete=models.CASCADE)

    class Meta:
        abstract = True
        verbose_name_plural = "Field Instances"


# an instance of Field for text data
class TextFieldInstance(FieldInstance):
    @property
    def _value(self):
        return self.value

    # the value of the text field
    value = models.TextField(blank=False)

    class Meta:
        verbose_name_plural = f"TextField {FieldInstance._meta.verbose_name_plural}"
        # we can't have more than one of the same field for the one model instance
        unique_together = ('field', 'model_instance')

    def __str__(self):
        return f"TextField instance with value \'{self.value}\'"


# an instance of Field for integer data
class IntegerFieldInstance(FieldInstance):
    @property
    def _value(self):
        return self.value

    # the value of the integer field
    value = models.IntegerField()

    class Meta:
        verbose_name_plural = f"Integer {FieldInstance._meta.verbose_name_plural}"
        # we can't have more than one of the same field for the one model instance
        unique_together = ('field', 'model_instance')

    def __str__(self):
        return f"IntegerField instance with value \'{self.value}\'"


# an instance of Field for decimal data
class DecimalFieldInstance(FieldInstance):
    @property
    def _value(self):
        return self.value

    # the value of the integer field
    value = models.DecimalField(decimal_places=DecimalField.decimal_places, max_digits=DecimalField.max_digits)

    class Meta:
        verbose_name_plural = f"Decimal {FieldInstance._meta.verbose_name_plural}"
        # we can't have more than one of the same field for the one model instance
        unique_together = ('field', 'model_instance')

    def __str__(self):
        return f"DecimalField instance with value \'{self.value}\'"


# an instance of Field for boolean data
class BooleanFieldInstance(FieldInstance):
    @property
    def _value(self):
        return self.value

    # the value of the boolean field
    value = models.BooleanField()

    class Meta:
        verbose_name_plural = f"Boolean {FieldInstance._meta.verbose_name_plural}"
        # we can't have more than one of the same field for the one model instance
        unique_together = ('field', 'model_instance')

    def __str__(self):
        return f"BooleanField instance with value \'{self.value}\'"


# an instance of Field for date data
class DateFieldInstance(FieldInstance):
    @property
    def value_form(self):
        return self.value.strftime('%d/%m/%Y')

    @property
    def _value(self):
        return self.value

    # the value of the date field
    value = models.DateField()

    class Meta:
        verbose_name_plural = f"Date {FieldInstance._meta.verbose_name_plural}"
        # we can't have more than one of the same field for the one model instance
        unique_together = ('field', 'model_instance')

    def __str__(self):
        return f"DateField instance with value \'{self.value}\'"


# an instance of Field for duration data
class DurationFieldInstance(FieldInstance):
    @property
    def _value(self):
        return self.value

    # the value of the duration field
    value = models.DurationField()

    class Meta:
        verbose_name_plural = f"Duration {FieldInstance._meta.verbose_name_plural}"
        # we can't have more than one of the same field for the one model instance
        unique_together = ('field', 'model_instance')

    def __str__(self):
        return f"DurationField instance with value \'{self.value}\'"


# an instance of Field for email data
class EmailFieldInstance(FieldInstance):
    @property
    def _value(self):
        return self.value

    # the value of the email field
    value = models.EmailField()

    class Meta:
        verbose_name_plural = f"Email {FieldInstance._meta.verbose_name_plural}"
        # we can't have more than one of the same field for the one model instance
        unique_together = ('field', 'model_instance')

    def __str__(self):
        return f"EmailField instance with value \'{self.value}\'"
