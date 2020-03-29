from django import forms
from django.contrib import admin

from polymorphic.admin import StackedPolymorphicInline

from flexible.conditions import *
from flexible.models import *


class ExpressionConditionGroupAdmin(admin.ModelAdmin):
    readonly_fields = [
        'expression'
    ]


@admin.register(ModelExpressionCondition)
class ModelExpressionConditionAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
            return {}


class ModelExpressionConditionInline(admin.TabularInline):
    model = ModelExpressionCondition
    extra = 0
    show_change_link = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_expression_condition_group_pk = None

    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.model_expression_condition_group_pk = obj.pk
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'condition':
            # if we couldn't get the pk already
            if self.model_expression_condition_group_pk is None:
                # get the FieldExpression pk from the request
                self.model_expression_condition_group_pk = request.resolver_match.kwargs.get('object_id')

            if self.model_expression_condition_group_pk is not None:
                # get the actual ModelExpression
                model_expression = ModelExpressionConditionGroup.objects.get(pk=int(self.model_expression_condition_group_pk)).expression
                # get the actual Model
                model = model_expression.model
                # only get Condition instances that are part of our Model
                kwargs['queryset'] = Condition.objects.filter(model=model)
            else:
                # if it's new return an empty queryset
                kwargs['queryset'] = Condition.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ModelExpressionConditionGroup)
class ModelExpressionConditionGroupAdmin(ExpressionConditionGroupAdmin):
    inlines = [
        ModelExpressionConditionInline
    ]

    def get_model_perms(self, request):
            return {}


class ModelExpressionConditionGroupInline(admin.TabularInline):
    model = ModelExpressionConditionGroup
    extra = 0
    show_change_link = True


@admin.register(FieldExpressionCondition)
class FieldExpressionConditionAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
            return {}


class FieldExpressionConditionInline(admin.TabularInline):
    model = FieldExpressionCondition
    extra = 0
    show_change_link = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_expression_condition_group_pk = None

    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.field_expression_condition_group_pk = obj.pk
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'condition':
            # if we couldn't get the pk already
            if self.field_expression_condition_group_pk is None:
                # get the FieldExpression pk from the request
                self.field_expression_condition_group_pk = request.resolver_match.kwargs.get('object_id')

            if self.field_expression_condition_group_pk is not None:
                # get the actual FieldExpression
                field_expression = FieldExpressionConditionGroup.objects.get(pk=int(self.field_expression_condition_group_pk)).expression
                # get the actual Model
                model = field_expression.field.model
                # only get Condition instances that are part of our Model
                kwargs['queryset'] = Condition.objects.filter(model=model)
            else:
                # if it's new return an empty queryset
                kwargs['queryset'] = Condition.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(FieldExpressionConditionGroup)
class FieldExpressionConditionGroupAdmin(ExpressionConditionGroupAdmin):
    inlines = [
        FieldExpressionConditionInline
    ]

    def get_model_perms(self, request):
            return {}


class FieldExpressionConditionGroupInline(admin.TabularInline):
    model = FieldExpressionConditionGroup
    extra = 0
    show_change_link = True


class ConditionInline(StackedPolymorphicInline):
    class ConcreteConditionInline(StackedPolymorphicInline.Child):
        formfield_overrides = {
            models.TextField: {
                'widget': forms.Textarea(attrs={
                    'rows': 1, 'cols': 60
                })
            },
        }

        show_change_link = True

    class FieldForeignKeyInline(ConcreteConditionInline):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.model_pk = None

        def get_formset(self, request, obj=None, **kwargs):
            if obj is not None:
                self.model_pk = obj.pk
            return super().get_formset(request, obj, **kwargs)

        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == 'field':
                if self.model_pk is None:
                    self.model_pk = request.resolver_match.kwargs.get('object_id')
                    
                if self.model_pk is not None:
                    # get the actual Model
                    model = Model.objects.get(pk=int(self.model_pk))
                    # only get Fields that match our model
                    kwargs['queryset'] = self._field_model.objects.filter(model=model, evaluated=False)
                else:
                    # return an empty set if the model is new
                    kwargs['queryset'] = self._field_model.objects.none()

            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        @property
        def _field_model(self):
            raise NotImplementedError

    class TextFieldConditionInline(FieldForeignKeyInline):
        model = TextFieldCondition

        @property
        def _field_model(self):
            return TextField

    class BooleanFieldConditionInline(FieldForeignKeyInline):
        model = BooleanFieldCondition

        @property
        def _field_model(self):
            return BooleanField

    class AlwaysTrueFieldConditionInline(ConcreteConditionInline):
        model = AlwaysTrueCondition

    class AlwaysFalseFieldConditionInline(ConcreteConditionInline):
        model = AlwaysFalseCondition

    class HasAttributeConditionInline(ConcreteConditionInline):
        model = HasAttributeCondition

    model = Condition
    child_inlines = [
        TextFieldConditionInline,
        BooleanFieldConditionInline,
        AlwaysTrueFieldConditionInline,
        AlwaysFalseFieldConditionInline,
        HasAttributeConditionInline,
    ]
    extra = 0
