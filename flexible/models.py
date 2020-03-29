import logging

import html
import csv
import io
import datetime

from django import forms
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext as _
from django.utils.text import slugify
from django.contrib.postgres.fields import JSONField

from polymorphic.models import PolymorphicModel

from flexible import widgets
from flexible.apps import JS_INDENT

from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__file__)


def selectors_escape(s):
    """
    Escapes all selectors used in html, css, js & jquery
    :param s: string
        The string to escape
    :return: string
        The escaped string
    """
    selectors_reserved = '\!"#$%&\'()*+,./:;<=>?@[]^``{|}~'
    for char in selectors_reserved:
        s = s.replace(char, f'\\\\{char}')
    return s


# the flexible model definition
class Model(models.Model):
    error_messages = {
        'column_count_mismatch': _("Column count is mismatched"),
        'too_many_rows': _("Too many csv rows provided"),
    }

    # the name of the model
    name = models.CharField(max_length=256, blank=False)
    # the date the model was created
    created = models.DateTimeField(auto_now_add=True)
    # the date the model was last modified
    modified = models.DateTimeField(auto_now=True)
    # is the model ready to be used?
    ready = models.BooleanField(default=False)
    # a reference to the default model where this model is copied from
    copied_from = models.ForeignKey('self', null=True, blank=True, default=None, on_delete=models.SET_NULL)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fields = None

    def create_instance(self):
        """
        Creates an instance of this model
        :return: ModelInstance
            An instance of this model
        """
        return ModelInstance.objects.create(model=self)

    def get_fields(self):
        """
        The fields of the model
        :return: QuerySet<Field>
            The set of fields for this model
        """
        return self.field_set.order_by('index')

    def get_non_evaluated_fields(self):
        """
        The non evaluated fields of the model
        :return: QuerySet<Field>
            The set of non evaluated fields for this model
        """
        return self.get_fields().filter(evaluated=False)

    def get_instances(self):
        """
        The instances of the model
        :return: QuerySet<ModelInstance>
            The set of instances of this model
        """
        return self.modelinstance_set.all()

    def copy(self, name=None):
        """
        Copies the model
        :return: Model
            A copy of the model
        """
        model = Model.objects.get(pk=self.pk)

        # make a copy of the model
        model.pk = None
        if name is None:
            name = f"{self.name}_Copy"

        # copy the name
        model.name = name
        # reference of the original model
        model.copied_from = self
        # copy is default marked as not ready
        model.ready = False
        model.save()

        # copy fields onto the new model
        # description components are copied with fields
        try:
            fields = self.get_fields()
            for field in fields:
                field.copy(model)
        except Exception:
            model.delete()
            raise

        # copy expressions
        try:
            expressions = self.modelexpression_set.all()
            for expression in expressions:
                expression.copy(model)
        except Exception:
            model.delete()
            raise

        return model

    def js(self, indent=''):
        """
        The expressions of the model as js
        :return: string
            The expressions of this model as js
        """

        expressions = self.modelexpression_set.all()
        js = ''
        if expressions.count() > 0:
            js_on_field_set_change_func_name = 'onFieldSetChange'
            js = indent + f'function {js_on_field_set_change_func_name}()\n'
            js = js + indent + '{\n'

            for expression in expressions:
                js = js + indent + f'{expression.js(indent + JS_INDENT)}\n'
            js = js + indent + '}\n'

            field_change_js = f'$(\'form :input\').on(\'keypress change focusout\', function()\n'
            field_change_js = field_change_js + indent + JS_INDENT + '{\n'
            field_change_js = field_change_js + indent + JS_INDENT + JS_INDENT + f'{js_on_field_set_change_func_name}();\n'
            field_change_js = field_change_js + indent + JS_INDENT + '})'

            document_ready_js = '$(document).ready(function()\n'
            document_ready_js = document_ready_js + indent + '{\n'
            document_ready_js = document_ready_js + indent + JS_INDENT + f'{js_on_field_set_change_func_name}();\n'
            document_ready_js = document_ready_js + indent + JS_INDENT + f'{field_change_js}\n'
            document_ready_js = document_ready_js + indent + '});'

            js = js + indent + f'\n'
            js = js + indent + document_ready_js

        return js

    def clean_values(self, fields):
        """
        Cleans the values, taking the entire model into account
        :param fields: dict
            The incoming dictionary of fields
        :return: dict
            The cleaned dictionary of fields
        """
        expressions = self.modelexpression_set.all()
        for expression in expressions:
            expression.execute(fields)

        return fields

    def compatible(self, model):
        """
        Evaluates if two models are field-compatible with each other.
        Two models are field-compatible if they have the same number
        of fields, matching field slugs and matching field types.
        :param model: Model
            The model to evaluate against
        :return: bool
            True if field-compatible, False otherwise
        """
        a_field_set = self.field_set.all()
        b_field_set = model.field_set.all()

        # first check the field count
        if a_field_set.count() != b_field_set.count():
            return False

        a_fields = self.fields
        b_fields = model.fields

        # go through all fields and check compatibility
        for field_name, a_field in a_fields.items():
            b_field = b_fields.get(field_name)

            # ensure field is not missing
            if b_field is None:
                return False

            # check field compatibility
            if not a_field.compatible(b_field):
                return False

        return True

    def clean_from_values(self, values, ignore_choices=False):
        """
        Validates values against the model
        :param values: list
            The the list of values to validate
        :param ignore_choices: bool
            Should the instance validation ignore field choices?
        """
        # get all non-evaluated fields
        fields = self.get_non_evaluated_fields()
        field_count = fields.count()

        # validate that the field count matches the value count
        if len(values) != field_count:
            raise RuntimeError(f'Model field and value count mismatch {len(values)} != {field_count}')

        # validate the values against the fields
        i = 0
        validation_messages = set()
        cleaned_values = []
        for field in fields:
            try:
                cleaned_values.append(field.clean_value(values[i], ignore_choices))
            except ValidationError as e:
                validation_messages.add(e.message)
            i = i + 1

        # combine all validation errors
        if len(validation_messages) > 0:
            raise ValidationError(list(validation_messages))

        return cleaned_values

    def create_instance_from_values(self, values, ignore_choices=True):
        """
        Creates an instance from values
        :param values: list
            The list of values to create from
        :param ignore_choices: bool
            Should the instance validation ignore field choices?
        :return: ModelInstance
            The created model instance
        """
        # clean the values to begin
        cleaned_values = self.clean_from_values(values, ignore_choices)
        # get all non-evaluated fields
        fields = self.get_non_evaluated_fields()

        # create a model instance
        model_instance = self.create_instance()
        try:
            # create the field instances
            i = 0
            for field in fields:
                # None values are just ignored
                cleaned_value = cleaned_values[i]
                if cleaned_value is not None:
                    field.create_instance(model_instance, cleaned_value)

                i = i + 1
        except Exception:
            # if creation of any field instance fails, delete the model instance
            model_instance.delete()
            # raise the exception
            raise

        return model_instance

    @property
    def fields(self):
        """
        The dictionary of fields of the model
        :return: dict
            The field names mapped to the fields
        """
        # if this object has no fields, and model isn't brand new
        if self._fields is None and self.pk is not None:
            # get the field models from the model
            fields = self.get_fields()
            self._fields = {}
            for field in fields:
                self._fields[field.name] = field

        return self._fields

    @property
    def fieldset_id(self):
        """
        The HTML fieldset element id for the model
        :return: string
            The fieldset id
        """
        return selectors_escape(html.escape(f"fieldset_id_{self.name.lower().replace(' ', '_')}"))

    @property
    def instance_count(self):
        """
        The number of instances the model has
        :return: int
            The number of instances
        """
        return self.modelinstance_set.all().count()

    class Meta:
        verbose_name_plural = "Models"

    def __str__(self):
        return self.name


# an instance of a Model
class ModelInstance(models.Model):
    # fields of the model instance
    _field_instances = None
    # the model of the instance
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    # the compiled json for the model instance
    json = JSONField(blank=True, null=True)

    def get(self, field_name, default=None):
        """
        Gets a field instance from the model instance
        :param field_name: string
            The field name
        :param default:
            The value to return when no model instance is found
        :return:
            The returned model instance
        """
        return self.fields.get(field_name, default)

    def to_json(self, force_update=False, obj=None):
        """
        Returns the model instance as json
        :param force_update: bool
            Should the json be forced to update?
        :param obj: object
            The optional object used for field evaluation
        :return: dict
            The model instance as a json dict
        """
        if obj is None:
            obj = self

        # update json if forced or if we don't have json yet
        if force_update or self.json is None:
            fields = self.model.get_fields()
            json_dict = {}

            # go through the fields, performing either evaluation or value fetching
            for field in fields:
                if not field.evaluated:
                    try:
                        value = field.get_instance(self).value
                    # catch not exist only on get instance
                    except ObjectDoesNotExist:
                        value = None
                else:
                    value = field.evaluate(obj)

                json_dict[field.name] = field.to_json(value)

            # set the instance's json to the created dict
            self.json = json_dict
            self.save()

        return self.json

    def to_csv(self):
        """
        Returns the model instance as a csv line
        :return: string
            The model instance as a csv line
        """
        # get the fields and values of the instance
        fields_values = self.to_json().items()

        csv_list = []
        # get values from the json dict
        for field, value in fields_values:
            csv_list.append(value)

        # write to a string io object
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(csv_list)

        # get the value from the string io object
        return output.getvalue()

    def to_post_dict(self):
        """
        Returns the uncompressed post dict for the model instance
        :return: dict
            The uncompressed post dict
        """
        post_dict = {}
        for field_name, field in self.fields.items():
            post_dict.update(field.value_post_dict)

        return post_dict

    def update_json(self, obj=None):
        """
        Updates the compiled json
        :param obj: object
            The optional object used for field evaluation
        """
        if obj is None:
            obj = self

        self.json = self.to_json(force_update=True, obj=obj)
        self.save()

    def on_update(self, obj=None):
        """
        Should be called when the model instance is updated
        :param obj: object
            The optional object used for field evaluation
        """
        if obj is None:
            obj = self

        self.update_json(obj)

    def equals(self, other):
        """
        Compares the instance against another for content equality
        :param other: ModelInstance
            The model instance to compare against
        :return: bool
            True when instances are equal, False when not
        """
        if self == other:
            return True

        if other.model_id != self.model_id:
            return False

        return self.to_json() == other.to_json()

    @property
    def fields(self):
        """
        The dictionary of fields of the model instance
        :return: dict
            The field names mapped to the fields
        """
        # if this object has no field instances, and instance isn't brand new
        if self._field_instances is None and self.pk is not None:
            # get the field models from the model
            fields = self.model.get_fields()
            # create and fill the field instances dictionary
            self._field_instances = {}
            for field in fields:
                if not field.evaluated:
                    try:
                        # some instances may miss fields, account for it
                        field_instance = field.get_instance(self)
                        self._field_instances[field.name] = field_instance
                    except ObjectDoesNotExist:
                        self._field_instances[field.name] = None

        return self._field_instances

    @property
    def description(self):
        """
        The description of the model instance
        :return: string
            The description of the model instance
        """
        # get the description components
        components = ModelDescriptionComponent.objects.filter(
            field__in=self.model.field_set.all()).order_by('index')

        if components.count() > 0:
            description = ''

            for component in components:
                instance = component.field.get_instance(self)
                description = f"{description}{instance.value} "
        else:
            description = None

        return description

    class Meta:
        verbose_name_plural = "Model Instances"

    def __str__(self):
        return f"Instance of {self.model}"


def NON_POLYMORPHIC_CASCADE(collector, field, sub_objs, using):
    return models.CASCADE(collector, field, sub_objs.non_polymorphic(), using)


# the flexible field definition
class Field(PolymorphicModel):
    FIELD_TYPE_TEXT_TINY = 'text'
    FIELD_TYPE_INTEGER_TINY = 'integer'
    FIELD_TYPE_DECIMAL_TINY = 'decimal'
    FIELD_TYPE_BOOLEAN_TINY = 'boolean'
    FIELD_TYPE_DATE_TINY = 'date'
    FIELD_TYPE_DURATION_TINY = 'duration'
    FIELD_TYPE_EMAIL_TINY = 'email'

    FIELD_TYPE_TEXT = "Text"
    FIELD_TYPE_INTEGER = "Integer"
    FIELD_TYPE_DECIMAL = "Decimal"
    FIELD_TYPE_BOOLEAN = "Boolean"
    FIELD_TYPE_DATE = "Date"
    FIELD_TYPE_DURATION = "Duration"
    FIELD_TYPE_EMAIL = "Email"

    FIELD_TYPE_TEXT_LONG = "Text field"
    FIELD_TYPE_INTEGER_LONG = "Whole number field"
    FIELD_TYPE_DECIMAL_LONG = "Decimal number field"
    FIELD_TYPE_BOOLEAN_LONG = "Yes / No field"
    FIELD_TYPE_DATE_LONG = "Date field"
    FIELD_TYPE_DURATION_LONG = "Duration field"
    FIELD_TYPE_EMAIL_LONG = "Email field"

    FIELD_TYPE_CHOICES = (
        (FIELD_TYPE_TEXT_TINY, FIELD_TYPE_TEXT),
        (FIELD_TYPE_INTEGER_TINY, FIELD_TYPE_INTEGER),
        (FIELD_TYPE_DECIMAL_TINY, FIELD_TYPE_DECIMAL),
        (FIELD_TYPE_BOOLEAN_TINY, FIELD_TYPE_BOOLEAN),
        (FIELD_TYPE_DATE_TINY, FIELD_TYPE_DATE),
        (FIELD_TYPE_DURATION_TINY, FIELD_TYPE_DURATION),
        (FIELD_TYPE_EMAIL_TINY, FIELD_TYPE_EMAIL),
    )

    FIELD_TYPE_LONG_CHOICES = (
        (FIELD_TYPE_TEXT_TINY, FIELD_TYPE_TEXT_LONG),
        (FIELD_TYPE_INTEGER_TINY, FIELD_TYPE_INTEGER_LONG),
        (FIELD_TYPE_DECIMAL_TINY, FIELD_TYPE_DECIMAL_LONG),
        (FIELD_TYPE_BOOLEAN_TINY, FIELD_TYPE_BOOLEAN_LONG),
        (FIELD_TYPE_DATE_TINY, FIELD_TYPE_DATE_LONG),
        (FIELD_TYPE_DURATION_TINY, FIELD_TYPE_DURATION_LONG),
        (FIELD_TYPE_EMAIL_TINY, FIELD_TYPE_EMAIL_LONG),
    )

    # field type map is updated by each field
    FIELD_TYPE_MAP = {
    }

    # defaults for fields
    default_index = 0
    max_name_length = 256
    max_verbose_name_length = 256

    # the model that this field belongs to
    model = models.ForeignKey(Model, on_delete=NON_POLYMORPHIC_CASCADE)
    # index order of the field, from 0 to N with 0 being first
    index = models.IntegerField(default=default_index, blank=False)
    # the name of the field
    name = models.SlugField(max_length=max_name_length, blank=False)
    # the verbose name of the field
    verbose_name = models.CharField(max_length=max_verbose_name_length, blank=False)
    # is the field required?
    required = models.BooleanField()
    # is the field hidden?
    hidden = models.BooleanField(default=False)
    # the description for the field
    description = models.TextField(blank=True)
    # is the field evaluated?
    evaluated = models.BooleanField(default=False)
    # should the fields metrics be generated?
    generate_metrics = models.BooleanField(default=False)

    choice_field_placeholder = _("Select an option...")

    def create_instance(self, model_instance, value):
        """
        :param model_instance: ModelInstance
            The model instance to create a field instance for
        :param value:
            The value that the instance should hold
        :return: FieldInstance
            The newly created field instance
        """
        raise NotImplementedError

    def get_instance(self, model_instance):
        """
        :param model_instance: ModelInstance
            The model instance to fetch the field instance for
        :return: FieldInstance
            The field instance for the given model instance
        """
        if self.evaluated:
            raise RuntimeError("Field is evaluated, but get_instance method is being called.")
        return self.get_instance_impl(model_instance)

    def get_instance_impl(self, model_instance):
        raise NotImplementedError

    def get_form_field(self):
        """
        Returns the form field for this field
        :return: FormField
            The form field for this field
        """
        if self.required and self.hidden:
            required = False
        else:
            required = self.required

        return self.get_form_field_impl(required=required, label=html.escape(self.verbose_name))

    def get_form_field_impl(self, required, label, widget=None):
        """
        Evaluates the form field for this field
        :param required: bool
            Is the field required?
        :param label: string
            The label for the field
        :param widget: forms.Widget
            The optional widget for the field
        :return:
        """
        raise NotImplementedError

    def get_choice_form_field(self):
        """
        Returns the form field for this field's choice type
        :return: FormField
            The form field for this field
        """
        raise NotImplementedError

    def copy(self, model):
        """
        Copies the field onto a model
        :param model: Model
            The model to copy onto
        :return: Field
            The copied field
        """
        field = Field.objects.get(pk=self.pk)

        # pk and id must be wiped for django-polymorphic
        field.pk = None
        field.id = None
        field.model = model
        field.save()

        # if supported, copy choices for the field
        if field.supports_choices:
            for choice in self.choices:
                choice.copy(field)

        # copy any field expression
        try:
            field_expression = self.fieldexpression
            field_expression.copy(field)
        except ObjectDoesNotExist:
            pass

        # copy model description components
        description_components = self.modeldescriptioncomponent_set.all()
        for description_component in description_components:
            description_component.copy(model, field)

        return field

    def prepare_form(self, form):
        """
        Prepares a given form for the field
        :param form: django.forms.Form
            The form to prepare
        """
        pass

    def clean_value(self, value, ignore_choices=False):
        """
        Cleans a given value for the field
        :param value:
            The value to clean
        :param ignore_choices: bool
            Should any choices be ignored?
        :return value:
            The cleaned value
        """
        if self.required and (not value or value is None) and not self.hidden:
            raise ValidationError(f"Field '{self}' is required, but is not found")

        return value

    def evaluate(self, obj):
        """
        Evaluates the field against the given object
        :param obj:
            Object to evaluate against
        :return:
            The evaluated value of the field
        """
        if not self.evaluated:
            raise RuntimeError("Field is not evaluated, but evaluate method is being called.")

        try:
            expression = self.fieldexpression
        except ObjectDoesNotExist:
            raise RuntimeError("Field is evaluated, but does not have an expression")

        return expression.execute(obj=obj)

    def evaluate_json(self, obj):
        """
        Evaluates the field against the given object
        :param obj:
            Object to evaluate against
        :return:
            The evaluated value of the field
        """
        if not self.evaluated:
            raise RuntimeError("Field is not evaluated, but evaluate method is being called.")

        try:
            expression = self.fieldexpression
        except ObjectDoesNotExist:
            raise RuntimeError("Field is evaluated, but does not have an expression")

        return self.to_json(expression.execute(obj=obj))

    def to_json(self, value):
        """
        Returns the given value to json
        :param value:
            The value to convert to json
        :return:
            The value converted to json
        """
        raise NotImplementedError

    def from_json(self, json_string):
        """
        Converts a json string to a value
        :param json_string: string
            The json string to convert from
        :return:
            The value converted from json
        """
        raise NotImplementedError

    def delete(self, using=None, keep_parents=False):
        super().delete(using, keep_parents)

    def save(self, *args, **kwargs):
        self.name = slugify(self.verbose_name)
        super().save(*args, **kwargs)

    def create_choice(self, value, index=None):
        """
        Creates a new choice for the field
        :param value:
            The value for the choice
        :param index: int
            The optional index
        :return:
        """
        raise NotImplementedError

    def compatible(self, field):
        """
        Evaluates if two fields are compatible
        :param field:
        :return:
        """
        a = self
        b = field

        # ensure both are the same concrete type
        if not isinstance(a, b.__class__):
            return False

        # ensure that both have the same name
        if a.name != b.name:
            return False

        return True

    def to_post_dict(self, value):
        """
        Decompresses a given value to a post dict
        :param value:
            The value to decompress to a post dict
        :return: dict
            The decompressed post dict
        """
        return {
            self.name: value
        }

    @property
    def choices(self):
        """
        The choices for the field
        :return: list
            The list of choices for the field
        """
        raise NotImplementedError

    @property
    def div_id(self):
        """
        The HTML div element id that wraps the field
        :return: string
            The div id
        """
        return selectors_escape(html.escape(f'div_id_{self.name}'))

    @property
    def input_id(self):
        """
        The HTML input field element id for the field
        :return: string
            The input field id
        """
        return selectors_escape(html.escape(f'id_{self.name}'))

    @property
    def tiny_type_name(self):
        """
        The field type name in tiny
        :return: string
            The tiny version of the field type name
        """
        raise NotImplementedError

    @property
    def type_name(self):
        """
        The field types name
        :return: string
            The name of the field type
        """
        raise NotImplementedError

    @property
    def long_type_name(self):
        """
        The field type name in long and descriptive
        :return: string
            The long version of the field type name
        """
        raise NotImplementedError

    @property
    def supports_choices(self):
        """
        Does the field support choices?
        :return: bool
            True if the field supports choices, False otherwise
        """
        raise NotImplementedError

    class Meta:
        verbose_name_plural = "Fields"
        unique_together = ('name', 'model')

    def __str__(self):
        return f"{self.verbose_name} for {self.model}"


# represents a flexible text field
class TextField(Field):
    # should choices be displayed as dropdown
    dropdown = models.BooleanField(default=False)
    # are choices fixed?
    fixed_choices = models.BooleanField(default=True)
    # should the field be a large text area?
    text_area = models.BooleanField(default=False)

    def create_instance(self, model_instance, value):
        return self.textfieldinstance_set.create(model_instance=model_instance, value=value)

    def get_instance_impl(self, model_instance):
        return self.textfieldinstance_set.get(model_instance=model_instance)

    def get_form_field_impl(self, required, label, widget=None):
        choice_set = self.choices

        # if the field is a dropdown, show it as such with choices
        if choice_set.count() > 0 and self.dropdown:
            # gather the choices
            choices = [(x.value, x.verbose_value) for x in choice_set]
            # insert the start placeholder choice
            choices.insert(0, (None, _(self.choice_field_placeholder)))

            return forms.ChoiceField(required=required, label=label, choices=choices)

        if self.text_area:
            return forms.CharField(required=required, label=label, widget=forms.Textarea)

        return forms.CharField(required=required, label=label)

    def get_choice_form_field(self):
        return forms.CharField()

    def prepare_form(self, form):
        """
        Prepares a given form for the field
        :param form: django.forms.Form
            The form to prepare
        """
        choices = self.choices

        if not self.dropdown and choices.count() > 0:
            form.field_choices[self.name] = choices

    def clean_value(self, value, ignore_choices=False):
        value = super().clean_value(value)

        if value:
            # validate the value is a string
            if not isinstance(value, str):
                logger.warning(f"Invalid type provided for \'{self.verbose_name}\'", stack=True)
                value = str(value)

            # strip whitespace off the value
            value = value.strip()

            # ensure before any choice checks that we have any choices
            if self.textfieldchoice_set.all().count() > 0:
                # if using fixed choices, find a choice corresponding to the value
                if value is not None and self.fixed_choices and not ignore_choices:
                    try:
                        value = self.choices.get(value__iexact=value).value
                    except ObjectDoesNotExist:
                        raise ValidationError(f"{value} not in choices for \'{self.verbose_name}\'")
        else:
            # blank text becomes null
            value = None

        return value

    def to_json(self, value):
        if value is None:
            return value

        if not type(value) is str:
            return str(value)

        return value

    def from_json(self, json_string):
        return json_string

    def create_choice(self, value, index=None):
        return self.textfieldchoice_set.create(value=value, index=index)

    @property
    def choices(self):
        return self.textfieldchoice_set.all().order_by('index', 'value')

    @property
    def tiny_type_name(self):
        return Field.FIELD_TYPE_TEXT_TINY

    @property
    def type_name(self):
        return Field.FIELD_TYPE_TEXT

    @property
    def long_type_name(self):
        return Field.FIELD_TYPE_TEXT_LONG

    @property
    def supports_choices(self):
        if self.text_area:
            return False
        return True

    class Meta:
        verbose_name_plural = "Text Fields"


Field.FIELD_TYPE_MAP.update({
    Field.FIELD_TYPE_TEXT_TINY: TextField,
})


# represents a flexible integer field
class IntegerField(Field):
    def create_instance(self, model_instance, value):
        return self.integerfieldinstance_set.create(model_instance=model_instance, value=value)

    def get_instance_impl(self, model_instance):
        return self.integerfieldinstance_set.get(model_instance=model_instance)

    def get_form_field_impl(self, required, label, widget=None):
        return forms.IntegerField(required=required, label=label, widget=widget)

    def get_choice_form_field(self):
        return forms.IntegerField()

    def to_json(self, value):
        if value is None:
            return 0

        return value

    def from_json(self, json_string):
        if json_string is None:
            return 0

        return int(json_string)

    def create_choice(self, value, index=None):
        return self.integerfieldchoice_set.create(value=value, index=index)

    @property
    def choices(self):
        return self.integerfieldchoice_set.all().order_by('index')

    @property
    def tiny_type_name(self):
        return Field.FIELD_TYPE_INTEGER_TINY

    @property
    def type_name(self):
        return Field.FIELD_TYPE_INTEGER

    @property
    def long_type_name(self):
        return Field.FIELD_TYPE_INTEGER_LONG

    @property
    def supports_choices(self):
        return False

    class Meta:
        verbose_name_plural = "Integer Fields"


Field.FIELD_TYPE_MAP.update({
    Field.FIELD_TYPE_INTEGER_TINY: IntegerField,
})


# represents a flexible decimal field
class DecimalField(Field):
    error_messages = {
        'exceeded_digits': _("Only %d digits are allowed.")
    }

    decimal_places = 3
    max_digits = 10

    def create_instance(self, model_instance, value):
        return self.decimalfieldinstance_set.create(model_instance=model_instance, value=value)

    def get_instance_impl(self, model_instance):
        return self.decimalfieldinstance_set.get(model_instance=model_instance)

    def get_form_field_impl(self, required, label, widget=None):
        return forms.DecimalField(required=required, label=label, widget=widget)

    def get_choice_form_field(self):
        return forms.DecimalField()

    def clean_value(self, value, ignore_choices=False):
        if value is None:
            value = 0

        # clamp the decimal places down
        try:
            value = Decimal(round(Decimal(value), self.decimal_places))
        except InvalidOperation:
            raise ValidationError(self.error_messages['exceeded_digits'] % self.max_digits, code='exceeded_digits')

        # ensure that max digits has not been exceeded
        if len(value.as_tuple().digits) > self.max_digits:
            raise ValidationError(self.error_messages['exceeded_digits'] % self.max_digits, code='exceeded_digits')

        return value

    def to_json(self, value):
        if value is None:
            return value

        if type(value) is not Decimal:
            raise RuntimeError

        return float(value)

    def from_json(self, json_string):
        if json_string is None:
            return 0

        return self.clean_value(float(json_string))

    def create_choice(self, value, index=None):
        return self.decimalfieldchoice_set.create(value=value, index=index)

    @property
    def choices(self):
        return self.decimalfieldchoice_set.all().order_by('index')

    @property
    def tiny_type_name(self):
        return Field.FIELD_TYPE_DECIMAL_TINY

    @property
    def type_name(self):
        return Field.FIELD_TYPE_DECIMAL

    @property
    def long_type_name(self):
        return Field.FIELD_TYPE_DECIMAL_LONG

    @property
    def supports_choices(self):
        return False

    class Meta:
        verbose_name_plural = "Decimal Fields"


Field.FIELD_TYPE_MAP.update({
    Field.FIELD_TYPE_DECIMAL_TINY: DecimalField,
})


# represents a flexible boolean field
class BooleanField(Field):
    def create_instance(self, model_instance, value):
        return self.booleanfieldinstance_set.create(model_instance=model_instance, value=value)

    def get_instance_impl(self, model_instance):
        return self.booleanfieldinstance_set.get(model_instance=model_instance)

    def get_form_field_impl(self, required, label, widget=None):
        return forms.ChoiceField(required=required, label=label, widget=widget, choices=[
            (None, _(self.choice_field_placeholder)), ('True', 'Yes'), ('False', 'No')
        ])

    def get_choice_form_field(self):
        raise NotImplementedError

    def clean_value(self, value, ignore_choices=False):
        value = super().clean_value(value)

        if value is not None:
            # handle string input
            if type(value) is str:
                value = value.lower()
                if value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                elif value == '':
                    value = None
                else:
                    raise RuntimeError(f"Unexpected string '{value}' for BooleanField")
            # no other types are expected
            else:
                raise RuntimeError("Unexpected type for BooleanField")

        return value

    def to_json(self, value):
        if value is None:
            return value

        if type(value) is not bool:
            raise RuntimeError

        return value

    def from_json(self, json_string):
        return self.clean_value(json_string)

    def create_choice(self, value, index=None):
        raise NotImplementedError

    @property
    def choices(self):
        raise NotImplementedError

    @property
    def tiny_type_name(self):
        return Field.FIELD_TYPE_BOOLEAN_TINY

    @property
    def type_name(self):
        return Field.FIELD_TYPE_BOOLEAN

    @property
    def long_type_name(self):
        return Field.FIELD_TYPE_BOOLEAN_LONG

    @property
    def supports_choices(self):
        return False

    class Meta:
        verbose_name_plural = "Boolean Fields"


Field.FIELD_TYPE_MAP.update({
    Field.FIELD_TYPE_BOOLEAN_TINY: BooleanField,
})


# represents a flexible date field
class DateField(Field):
    def create_instance(self, model_instance, value):
        return self.datefieldinstance_set.create(model_instance=model_instance, value=value)

    def get_instance_impl(self, model_instance):
        return self.datefieldinstance_set.get(model_instance=model_instance)

    def get_form_field_impl(self, required, label, widget=None):
        return forms.DateField(required=required, label=label, widget=forms.TextInput(
                               attrs={
                                   'placeholder': _("Select to enter a date"),
                                   'class': 'form-control date',
                                   'type': 'text',
                               }),
                               input_formats=[
                                   '%d/%m/%Y',
                               ])

    def get_choice_form_field(self):
        return forms.DateField(widget=forms.TextInput(
                               attrs={
                                   'placeholder': _("Select to enter a date"),
                                   'class': 'form-control date',
                                   'type': 'text',
                               }),
                               input_formats=[
                                   '%d/%m/%Y',
                               ])

    def clean_value(self, value, ignore_choices=False):
        if type(value) is str:
            return datetime.datetime.strptime(super().clean_value(value, ignore_choices), '%d/%m/%Y')
        else:
            return super().clean_value(value, ignore_choices)

    def to_json(self, value):
        if value is None:
            return value

        return str(value)

    def from_json(self, json_string):
        if json_string is None:
            return json_string

        return datetime.datetime.strptime(json_string, '%Y-%m-%d')

    def create_choice(self, value, index=None):
        return self.datefieldchoice_set.create(value=value, index=index)

    def to_post_dict(self, value):
        return {
            self.name: value.strftime('%d/%m/%Y')
        }

    @property
    def choices(self):
        return self.datefieldchoice_set.all().order_by('index')

    @property
    def tiny_type_name(self):
        return Field.FIELD_TYPE_DATE_TINY

    @property
    def type_name(self):
        return Field.FIELD_TYPE_DATE

    @property
    def long_type_name(self):
        return Field.FIELD_TYPE_DATE_LONG

    @property
    def supports_choices(self):
        return False

    class Meta:
        verbose_name_plural = "Date Fields"


Field.FIELD_TYPE_MAP.update({
    Field.FIELD_TYPE_DATE_TINY: DateField,
})


# represents a flexible duration field
class DurationField(Field):
    error_messages = {
        'negative_numbers': _("Negative numbers are not allowed.")
    }

    def create_instance(self, model_instance, value):
        return self.durationfieldinstance_set.create(model_instance=model_instance, value=value)

    def get_instance_impl(self, model_instance):
        return self.durationfieldinstance_set.get(model_instance=model_instance)

    def get_form_field_impl(self, required, label, widget=None):
        return forms.DurationField(required=required, label=label, widget=widgets.DurationWidget())

    def get_choice_form_field(self):
        return forms.DurationField(widget=widgets.DurationWidget())

    def clean_value(self, value, ignore_choices=False):
        # imports sometimes result in strings coming in
        if type(value) is str:
            value = datetime.timedelta(seconds=int(value))

        if value is not None:
            if value.days < 0 or value.seconds < 0:
                raise ValidationError(self.error_messages['negative_numbers'], code='negative_numbers')
            else:
                return value
        else:
            return None

    def to_json(self, value):
        if value is None:
            return value

        return int(value.total_seconds())

    def from_json(self, json_string):
        if json_string is None:
            return json_string

        seconds = int(float(json_string))

        return datetime.timedelta(seconds=seconds)

    def create_choice(self, value, index=None):
        return self.durationfieldchoice_set.create(value=value, index=index)

    def to_post_dict(self, value):
        # create the default duration widget
        widget = widgets.DurationWidget()
        decompressed_values = widget.decompress(value=value)

        index = 0
        decompressed_dict = {}

        for decompressed_value in decompressed_values:
            decompressed_dict[f'{self.name}_{index}'] = decompressed_value
            index = index + 1

        return decompressed_dict

    @property
    def choices(self):
        return self.durationfieldchoice_set.all().order_by('index')

    @property
    def tiny_type_name(self):
        return Field.FIELD_TYPE_DURATION_TINY

    @property
    def type_name(self):
        return Field.FIELD_TYPE_DURATION

    @property
    def long_type_name(self):
        return Field.FIELD_TYPE_DURATION_LONG

    @property
    def supports_choices(self):
        return False

    class Meta:
        verbose_name_plural = "Duration Fields"


Field.FIELD_TYPE_MAP.update({
    Field.FIELD_TYPE_DURATION_TINY: DurationField,
})


# represents a flexible email field
class EmailField(Field):
    def create_instance(self, model_instance, value):
        return self.emailfieldinstance_set.create(model_instance=model_instance, value=value)

    def get_instance_impl(self, model_instance):
        return self.emailfieldinstance_set.get(model_instance=model_instance)

    def get_form_field_impl(self, required, label, widget=None):
        return forms.EmailField(required=required, label=label, widget=widget)

    def get_choice_form_field(self):
        return forms.EmailField()

    def clean_value(self, value, ignore_choices=False):
        value = super(EmailField, self).clean_value(value)

        if not value:
            value = None

        return value

    def to_json(self, value):
        return value

    def from_json(self, json_string):
        return json_string

    def create_choice(self, value, index=None):
        return self.emailfieldchoice_set.create(value=value, index=index)

    @property
    def choices(self):
        return self.emailfieldchoice_set.all().order_by('index')

    @property
    def tiny_type_name(self):
        return Field.FIELD_TYPE_EMAIL_TINY

    @property
    def type_name(self):
        return Field.FIELD_TYPE_EMAIL

    @property
    def long_type_name(self):
        return Field.FIELD_TYPE_EMAIL_LONG

    @property
    def supports_choices(self):
        return False

    class Meta:
        verbose_name_plural = "Email Fields"


Field.FIELD_TYPE_MAP.update({
    Field.FIELD_TYPE_EMAIL_TINY: EmailField,
})


# the model instance description component
class ModelDescriptionComponent(models.Model):
    # the model that the the description component is associated with
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    # the field that is used as part of the description
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    # the index of the description component
    index = models.IntegerField(default=0, blank=False)

    def clean(self):
        super(ModelDescriptionComponent, self).clean()

        if self.field.model != self.model:
            raise ValidationError("Field model should match model")

    def copy(self, model, field):
        """
        Copies the model description component
        :param model: Model
            The model to copy onto
        :param field: Field
            The field to copy onto
        :return: ModelDescriptionComponent
            The copied model description component
        """
        description_component = ModelDescriptionComponent.objects.get(pk=self.pk)

        description_component.pk = None
        description_component.model = model
        description_component.field = field
        description_component.save()

        return description_component

    class Meta:
        verbose_name_plural = "Model Description Components"

    def __str__(self):
        return f"Description component for {self.field.model}'s " \
               f"{self.field} field at index {self.index}"
