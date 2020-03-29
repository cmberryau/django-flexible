from django import forms
from django.contrib import admin

from flexible.expressions import *
from flexible.conditions_admin import *
from flexible.actions_admin import *


@admin.register(ModelExpression)
class ModelExpressionAdmin(admin.ModelAdmin):
    exclude = [
        'model',
    ]

    inlines = [
        ModelExpressionConditionGroupInline,
        ModelExpressionActionInline,
        AlternateModelExpressionActionInline,
    ]

    def get_model_perms(self, request):
            return {}


class ModelExpressionInline(admin.TabularInline):
    show_change_link = True
    model = ModelExpression
    extra = 0


@admin.register(FieldExpression)
class FieldExpressionAdmin(admin.ModelAdmin):
    exclude = [
        'field',
    ]

    inlines = [
        FieldExpressionConditionGroupInline,
        FieldExpressionActionInline,
        DefaultFieldExpressionActionInline,
    ]

    def get_model_perms(self, request):
            return {}


class FieldExpressionInline(admin.TabularInline):
    show_change_link = True
    model = FieldExpression
    extra = 0
