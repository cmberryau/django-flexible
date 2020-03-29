import logging

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.html import escape

from crispy_forms import layout
from crispy_forms.helper import FormHelper

from flexible.choices import *
from flexible.models import *

logger = logging.getLogger(__file__)


class ModelInstanceForm(forms.Form):
    def __init__(self, model, instance=None, ignore_choices=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # get the fields from the model
        self.model = model
        fields = self.model.get_fields()
        fieldset_fields = []
        self.instance = instance
        self.ignore_choices = ignore_choices

        # used by typeahead, choices injected by TextField.prepare_form
        self.field_choices = {}

        # create the initial dict if we have an instance
        if instance is not None:
            self.initial = {}

        # set the form fields from the model fields
        for field in fields:
            if not field.evaluated:
                self.fields[field.name] = field.get_form_field()

                crispy_field = layout.Field(escape(field.name),
                                            data_toggle='tooltip',
                                            data_placement='top',
                                            data_trigger='hover',
                                            title=field.description,
                                            autocomplete='off'
                                            )

                fieldset_fields.append(crispy_field)

                # prepare the form for the field
                field.prepare_form(self)

                # if we've got an instance and it has the field, fill the initial for it
                if instance is not None:
                    instance_field = instance.fields.get(field.name)
                    if instance_field is not None:
                        if instance_field.value is not None:
                            self.initial[field.name] = instance_field.value_form

        # set up the form using django-crispy-form's stuff
        self.helper = FormHelper()
        self.helper.form_show_errors = False
        self.helper.layout = layout.Layout(
            layout.Fieldset(None, *fieldset_fields, css_id=self.model.fieldset_id),
        )

    def clean(self):
        super().clean()

        # clean the values for each field
        fields = self.model.get_fields()
        field_values = {}
        for field in fields:
            if not field.evaluated:
                cleaned = field.clean_value(self.cleaned_data.get(field.name),
                                            ignore_choices=self.ignore_choices)
                field_values[field.name] = cleaned
                self.cleaned_data[field.name] = cleaned

        # clean the values from the model's perspective
        self.model.clean_values(field_values)

    def save(self):
        # either get a new model instance or use the existing one
        if self.instance is not None:
            model_instance = self.update_model_instance(self.instance)
        else:
            # create a new model instance
            model_instance = self.save_model_instance(self.model.create_instance())

        return model_instance

    def update_model_instance(self, model_instance):
        # alter existing fields and add new ones where needed
        model_fields = self.model.get_fields()
        original_fields = {}
        try:
            for field in model_fields:
                if not field.evaluated:
                    new_value = self.cleaned_data.get(field.name)
                    # get the existing field on the instance
                    try:
                        field_instance = field.get_instance(model_instance)
                    except ObjectDoesNotExist:
                        field_instance = None

                    # the field does not exist on the instance
                    if field_instance is None:
                        if new_value is not None:
                            # no original value
                            original_fields[field] = None
                            # create the new field instance
                            field.create_instance(model_instance, new_value)
                    else:
                        # update to new value if different
                        if field_instance.value != new_value:
                            # cache the original value
                            original_fields[field] = field_instance.value
                            if new_value is None:
                                # delete the old value if new is None
                                field_instance.delete()
                            else:
                                # save the new value
                                field_instance.value = new_value
                                field_instance.save()
        except Exception:
            # attempt to revert all changes on any error
            try:
                self.revert_update(model_instance, original_fields)
            except Exception:
                logger.error(f"Failed to revert {model_instance.id}, likely in invalid state.", stack=True)
                raise

        return model_instance

    @classmethod
    def revert_update(cls, model_instance, cached_values):
        for field in cached_values:
            # no previous value, delete the new one
            if cached_values[field] is None:
                try:
                    new_instance = field.get_instance(model_instance)
                    new_instance.delete()
                except ObjectDoesNotExist:
                    pass
            # revert back to the old value
            else:
                try:
                    new_instance = field.get_instance(model_instance)
                except ObjectDoesNotExist:
                    # if the instance was deleted, recreate it
                    field.create_instance(model_instance, cached_values[field])
                else:
                    new_instance.value = cached_values[field]

    def save_model_instance(self, model_instance):
        # create and save the field instances
        model_fields = self.model.get_fields()
        try:
            for field in model_fields:
                if not field.evaluated:
                    # do not save empty field instances
                    new_field_value = self.cleaned_data.get(field.name)
                    if new_field_value is not None:
                        field.create_instance(model_instance, new_field_value)

        except Exception:
            # clean up all created entries on error
            for field in model_fields:
                try:
                    instance = field.get_instance(model_instance)
                    instance.delete()
                # if no instance was created due to error or anything, pass
                except ObjectDoesNotExist:
                    pass

            model_instance.delete()
            raise

        return model_instance


class FieldForm(forms.Form):
    error_messages = {
        'field_exists': _("A field with the same name already exists")
    }

    field_type_choices = Field.FIELD_TYPE_LONG_CHOICES
    field_type = forms.ChoiceField(choices=field_type_choices, required=True)
    field_name = forms.CharField(max_length=Field.max_name_length, required=True)
    field_description = forms.CharField(max_length=Field.max_verbose_name_length, required=False)
    field_required = forms.BooleanField(required=False)
    field_index = forms.IntegerField(required=False)

    def __init__(self, request, model, field=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.request = request
        self.model = model
        self.field = field

        # are we updating an existing field?
        if field is not None:
            # set the initial values
            self.initial = {
                'field_type': field.tiny_type_name,
                'field_name': field.verbose_name,
                'field_description': field.description,
                'field_required': field.required,
                'field_index': field.index
            }

            # change field type to non required if not creating a field
            self.fields['field_type'].required = False

    def save(self):
        # get the attributes for the field
        verbose_name = self.cleaned_data.get('field_name')
        required = self.cleaned_data.get('field_required')
        index = self.cleaned_data.get('field_index')
        description = self.cleaned_data.get('field_description')

        # are we creating a new field?
        if self.field is None:
            # get the new index based on existing fields
            if index is None:
                if self.model.field_set.all().count() > 0:
                    index = self.model.field_set.order_by('-index')[0].index + 1
                else:
                    index = 0

            # get the field type from map
            field_type = Field.FIELD_TYPE_MAP[self.cleaned_data.get('field_type')]

            # create the new field
            self.field = field_type.objects.create(model=self.model,
                                                   index=index,
                                                   verbose_name=verbose_name,
                                                   required=required,
                                                   description=description)

            # give the user a confirmation message
            messages.success(self.request, _(f"Field '{self.field.verbose_name}' successfully created"))
        # are we editing an existing field?
        else:
            # use the previous index if no index exists
            if index is None:
                index = self.field.index

            self.field.index = index
            self.field.verbose_name = verbose_name
            self.field.required = required
            self.field.description = description
            self.field.save()

            # give the user a confirmation message
            messages.success(self.request, _(f"Field '{self.field.verbose_name}' successfully edited"))

        return self.field

    def clean_field_required(self):
        cleaned_value = self.cleaned_data.get('field_required')

        if cleaned_value is None:
            cleaned_value = False

        return cleaned_value

    def clean_field_name(self):
        cleaned_value = self.cleaned_data.get('field_name')

        # if creating a new field, check that no field with the same name exists
        if self.field is None:
            try:
                Field.objects.get(model=self.model, name=slugify(cleaned_value))
                raise ValidationError(self.error_messages['field_exists'], code='field_exists')
            except ObjectDoesNotExist:
                pass

        return cleaned_value


class FieldChoiceForm(forms.Form):
    error_messages = {
        'choice_exists': _("A choice with the same value already exists")
    }

    choice_index = forms.IntegerField(required=False)

    def __init__(self, request, field, choice=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ensure that the field supports choices
        if not field.supports_choices:
            raise RuntimeError("Provided choice does not support choices")

        self.request = request
        self.field = field
        self.choice = choice

        # populate the initial value if we are editing a choice
        if choice is not None:
            self.initial = {
                field.name: choice.value
            }

        # get the choice formfield from the field
        self.fields[field.name] = field.get_choice_form_field()
        # force the formfield to be required
        self.fields[field.name].required = True

        # set up the form using django-crispy-forms's stuff
        crispy_field = layout.Field(html.escape(field.name))
        self.helper = FormHelper()
        # override django-crispy-forms default errors being shown
        self.helper.form_show_errors = False
        # override django-crispy-forms labels being shown
        self.helper.form_show_labels = False
        # set the django-crispy-forms layout
        self.helper.layout = layout.Layout(layout.Fieldset(None, crispy_field))

    def clean(self):
        super().clean()

        # first do the form clean
        cleaned_value = self.cleaned_data.get(self.field.name)
        if cleaned_value is None:
            raise RuntimeError("Cannot create empty choice")

        # then the field clean
        cleaned_value = self.field.clean_value(cleaned_value, ignore_choices=True)
        if cleaned_value is None:
            raise RuntimeError("Cannot create empty choice")

        # if creating a new choice, check that no choice with the same value exists
        if self.choice is None:
            try:
                self.field.choices.get(slug=slugify(cleaned_value))
                raise ValidationError(self.error_messages['choice_exists'], code='choice_exists')
            except ObjectDoesNotExist:
                pass

        self.cleaned_data[self.field.name] = cleaned_value

    def save(self):
        value = self.cleaned_data.get(self.field.name)
        index = self.cleaned_data.get('choice_index')

        # are we creating a new choice?
        if self.choice is None:
            if index is None:
                # get the index based on the existing choices
                if self.field.choices.count() > 0:
                    # get the highest indexed choice and increment
                    index = self.field.choices[self.field.choices.count() - 1].index + 1
                # just set index to zero
                else:
                    index = 0

            # create the choice from the field
            self.choice = self.field.create_choice(value=value, index=index)

            # give the user a confirmation message
            messages.success(self.request, _(f"Choice '{self.choice.value}' successfully created"))

        # or are we updating an existing choice
        else:
            if index is None:
                # if index is not provided, just use the old one
                index = self.choice.index

            # set the value for the choice and save
            self.choice.value = self.cleaned_data.get(self.field.name)
            self.choice.index = index
            self.choice.save()

            # give the user a confirmation message
            messages.success(self.request, _(f"Choice '{self.choice.value}' successfully edited"))

        return self.choice
