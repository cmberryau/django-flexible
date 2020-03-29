from django.contrib import admin
from django.db import transaction, DatabaseError

from polymorphic.admin import PolymorphicInlineSupportMixin, StackedPolymorphicInline

from flexible.models import *
from flexible.choices import *
from flexible.instances import *
from flexible.expressions_admin import *
from flexible.actions_admin import *
from flexible.conditions_admin import *
from flexible.imports_admin import *

field_fields = [
    'name',
    'index',
    'verbose_name',
    'description',
    'required',
    'hidden',
    'evaluated',
    'generate_metrics',
]


class FieldInline(StackedPolymorphicInline):
    class ConcreteFieldInlineBase(StackedPolymorphicInline.Child):
        show_change_link = True
        formfield_overrides = {
            models.TextField: {
                'widget': forms.Textarea(attrs={
                    'rows': 1, 'cols': 60
                })
            },
        }

        fields = field_fields

        readonly_fields = [
            'name'
        ]

    class TextFieldInline(ConcreteFieldInlineBase):
        model = TextField

        fields = field_fields + [
            'dropdown',
            'fixed_choices',
            'text_area',
        ]

    class IntegerFieldInline(ConcreteFieldInlineBase):
        model = IntegerField

    class DecimalFieldInline(ConcreteFieldInlineBase):
        model = DecimalField

    class BooleanFieldInline(ConcreteFieldInlineBase):
        model = BooleanField

    class DateFieldInline(ConcreteFieldInlineBase):
        model = DateField

    class DurationFieldInline(ConcreteFieldInlineBase):
        model = DurationField

    class EmailFieldInline(ConcreteFieldInlineBase):
        model = EmailField

    model = Field
    child_inlines = [
        TextFieldInline,
        IntegerFieldInline,
        DecimalFieldInline,
        BooleanFieldInline,
        DateFieldInline,
        DurationFieldInline,
        EmailFieldInline,
    ]
    extra = 0
    ordering = [
        'index',
    ]


class ModelDescriptionComponentInline(admin.TabularInline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_pk = None

    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.model_pk = obj.pk
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'field':
            # if we couldn't get the pk already
            if self.model_pk is None:
                # get the Model pk from the request
                self.model_pk = request.resolver_match.kwargs.get('object_id')

            if self.model_pk is not None:
                # get the actual Model
                model = Model.objects.get(pk=int(self.model_pk))
                # only get Field instances that are part of our Model
                kwargs['queryset'] = Field.objects.filter(model=model)
            else:
                # if it's a new model return an empty queryset
                kwargs['queryset'] = Field.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    model = ModelDescriptionComponent
    extra = 0
    ordering = [
        'index',
    ]


@admin.register(Model)
class ModelAdmin(PolymorphicInlineSupportMixin, admin.ModelAdmin):
    inlines = [
        FieldInline,
        ModelDescriptionComponentInline,
        ModelExpressionInline,
        ActionInline,
        ConditionInline,
    ]

    fields = [
        'name',
        'ready',
        'created',
        'modified',
    ]

    readonly_fields = [
        'created',
        'modified',
    ]

    actions = [
        'copy',
    ]

    def copy(self, request, queryset):
        for model in queryset:
            with transaction.atomic():
                try:
                    model = Model.objects.filter(id=model.id).select_for_update(nowait=True)[0]
                except DatabaseError:
                    self.message_user(request, f"Failed to copy model {model}, could not get model lock")
                else:
                    self.message_user(request, f"Copied model {model} to {model.copy()}")

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return self.readonly_fields + [
                'instance_count',
            ]

        return self.readonly_fields


class ConcreteFieldInstanceInlineBase(admin.TabularInline):
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(attrs={
                'rows': 1, 'cols': 60
            })
        },
    }
    extra = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_instance_pk = None

    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.model_instance_pk = obj.pk
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'field':
            # if we couldn't get the pk already
            if self.model_instance_pk is None:
                # get the ModelInstance pk from the request
                self.model_instance_pk = request.resolver_match.kwargs.get('object_id')

                if self.model_instance_pk is not None:
                    # get the actual ModelInstance
                    model_instance = ModelInstance.objects.get(pk=int(self.model_instance_pk))
                    # only get Field instances that match our instances model
                    kwargs['queryset'] = self.field_model.objects.filter(model=model_instance.model)
                else:
                    # if it's a new model instance return an empty queryset
                    kwargs['queryset'] = Field.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @property
    def field_model(self):
        raise NotImplementedError


class TextFieldInstanceInline(ConcreteFieldInstanceInlineBase):
    model = TextFieldInstance

    @property
    def field_model(self):
        return TextField


class IntegerFieldInstanceInline(ConcreteFieldInstanceInlineBase):
    model = IntegerFieldInstance

    @property
    def field_model(self):
        return IntegerField


class DecimalFieldInstanceInline(ConcreteFieldInstanceInlineBase):
    model = DecimalFieldInstance

    @property
    def field_model(self):
        return DecimalField


class BooleanFieldInstanceInline(ConcreteFieldInstanceInlineBase):
    model = BooleanFieldInstance

    @property
    def field_model(self):
        return BooleanField


class DateFieldInstanceInline(ConcreteFieldInstanceInlineBase):
    model = DateFieldInstance

    @property
    def field_model(self):
        return DateField


class DurationFieldInstanceInline(ConcreteFieldInstanceInlineBase):
    model = DurationFieldInstance

    @property
    def field_model(self):
        return DurationField


class EmailFieldInstanceInline(ConcreteFieldInstanceInlineBase):
    model = EmailFieldInstance

    @property
    def field_model(self):
        return EmailField


@admin.register(ModelInstance)
class ModelInstanceAdmin(admin.ModelAdmin):
    inlines = [
        TextFieldInstanceInline,
        IntegerFieldInstanceInline,
        DecimalFieldInstanceInline,
        BooleanFieldInstanceInline,
        DateFieldInstanceInline,
        DurationFieldInstanceInline,
        EmailFieldInstanceInline
    ]


class ChoiceInline(admin.TabularInline):
    extra = 0
    ordering = [
        'index',
    ]
    readonly_fields = [
        'slug'
    ]


class FieldAdmin(admin.ModelAdmin):
    exclude = [
        'model'
    ]

    def get_model_perms(self, request):
        # return an empty dict, hides from admin index
        return {}


class TextFieldChoiceInline(ChoiceInline):
    model = TextFieldChoice


@admin.register(TextField)
class TextFieldAdmin(FieldAdmin):
    inlines = [
        TextFieldChoiceInline,
        FieldExpressionInline,
    ]


@admin.register(BooleanField)
class BooleanFieldAdmin(FieldAdmin):
    inlines = [
        FieldExpressionInline,
    ]


class IntegerFieldChoiceInline(ChoiceInline):
    model = IntegerFieldChoice


@admin.register(IntegerField)
class IntegerFieldAdmin(FieldAdmin):
    inlines = [
        IntegerFieldChoiceInline,
        FieldExpressionInline,
    ]


class DecimalFieldChoiceInline(ChoiceInline):
    model = DecimalFieldChoice


@admin.register(DecimalField)
class DecimalFieldAdmin(FieldAdmin):
    inlines = [
        DecimalFieldChoiceInline,
        FieldExpressionInline,
    ]


class DateFieldChoiceInline(ChoiceInline):
    model = DateFieldChoice


@admin.register(DateField)
class DateFieldAdmin(FieldAdmin):
    inlines = [
        DateFieldChoiceInline,
        FieldExpressionInline,
    ]


class DurationFieldChoiceInline(ChoiceInline):
    model = DurationFieldChoice


@admin.register(DurationField)
class DurationFieldAdmin(FieldAdmin):
    inlines = [
        DurationFieldChoiceInline,
        FieldExpressionInline,
    ]


class EmailFieldChoiceInline(ChoiceInline):
    model = EmailFieldChoice


@admin.register(EmailField)
class EmailFieldAdmin(FieldAdmin):
    inlines = [
        EmailFieldChoiceInline,
        FieldExpressionInline,
    ]
