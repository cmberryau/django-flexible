from django.contrib import admin

from polymorphic.admin import StackedPolymorphicInline

from flexible.expressions import *
from flexible.actions import *
from flexible.models import Field


@admin.register(ModelExpressionAction)
class ModelExpressionActionAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
            return {}


class ModelExpressionActionInline(admin.TabularInline):
    model = ModelExpressionAction
    extra = 0
    show_change_link = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_expression_pk = None

    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.model_expression_pk = obj.pk
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'action':
            # if we couldn't get the pk already
            if self.model_expression_pk is None:
                # get the Model pk from the request
                self.model_expression_pk = request.resolver_match.kwargs.get('object_id')

            if self.model_expression_pk is not None:
                # get the actual ModelExpression
                model_expression = ModelExpression.objects.get(pk=int(self.model_expression_pk))
                # get the actual model
                model = model_expression.model
                # only get Action instances that are part of our Model
                kwargs['queryset'] = Action.objects.filter(model=model)
            else:
                # if it's new return an empty queryset
                kwargs['queryset'] = Action.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(AlternateModelExpressionAction)
class AlternateModelExpressionActionAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
            return {}


class AlternateModelExpressionActionInline(ModelExpressionActionInline):
    model = AlternateModelExpressionAction


@admin.register(FieldExpressionAction)
class FieldExpressionActionAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
            # return an empty dict, hides from admin index
            return {}


class FieldExpressionActionInline(admin.TabularInline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_expression_pk = None

    def get_formset(self, request, obj=None, **kwargs):
        if obj is not None:
            self.field_expression_pk = obj.pk
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'action':
            # if we couldn't get the pk already
            if self.field_expression_pk is None:
                # get the Model pk from the request
                self.field_expression_pk = request.resolver_match.kwargs.get('object_id')

            if self.field_expression_pk is not None:
                # get the actual FieldExpression
                field = FieldExpression.objects.get(pk=int(self.field_expression_pk)).field
                # get the actual model
                model = field.model
                # only get Action instances that are part of our Model
                kwargs['queryset'] = Action.objects.filter(model=model)
            else:
                # if it's new return an empty queryset
                kwargs['queryset'] = Action.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    model = FieldExpressionAction
    extra = 0
    show_change_link = True


@admin.register(DefaultFieldExpressionAction)
class DefaultFieldExpressionActionAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
            # return an empty dict, hides from admin index
            return {}


class DefaultFieldExpressionActionInline(FieldExpressionActionInline):
    model = DefaultFieldExpressionAction


class ActionInline(StackedPolymorphicInline):
    class ConcreteActionInline(StackedPolymorphicInline.Child):
        show_change_link = True

    class FieldForeignKeyInline(ConcreteActionInline):
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
                    # if the model is new, return an empty set
                    kwargs['queryset'] = self._field_model.objects.none()

            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        @property
        def _field_model(self):
            raise NotImplementedError

    class ShowFieldActionInline(FieldForeignKeyInline):
        model = ShowFieldAction

        @property
        def _field_model(self):
            return Field

    class HideFieldActionInline(FieldForeignKeyInline):
        model = HideFieldAction

        @property
        def _field_model(self):
            return Field

    class ReturnIntegerActionInline(ConcreteActionInline):
        model = ReturnIntegerAction

    class LogMessageActionInline(ConcreteActionInline):
        model = LogMessageAction

    class FormatDateFieldActionInline(FieldForeignKeyInline):
        model = FormatDateFieldAction

        @property
        def _field_model(self):
            return DateField

    class ReturnAttributeActionInline(ConcreteActionInline):
        model = ReturnAttributeAction

    class ReturnDaysBetweenDatesActionInline(ConcreteActionInline):
        model = ReturnDaysBetweenDatesAction

        @property
        def _field_model(self):
            return DateField

    model = Action
    child_inlines = [
        ShowFieldActionInline,
        HideFieldActionInline,
        ReturnIntegerActionInline,
        LogMessageActionInline,
        FormatDateFieldActionInline,
        ReturnAttributeActionInline,
        ReturnDaysBetweenDatesActionInline,
    ]
    extra = 0
