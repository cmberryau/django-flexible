from django.db import models

from polymorphic.models import PolymorphicModel

from flexible.expressions import Operator, ModelExpression, FieldExpression
from flexible.models import Model, TextField, IntegerField, \
                            BooleanField, DecimalField, \
                            DateField, DurationField, \
                            EmailField, NON_POLYMORPHIC_CASCADE
from flexible.instances import TextFieldInstance, IntegerFieldInstance, \
                                BooleanFieldInstance, DecimalFieldInstance, \
                                DateFieldInstance, DurationFieldInstance, \
                                EmailFieldInstance


class ConditionGroup(models.Model):
    operator = models.TextField(blank=True, null=True, choices=Operator.OPERATOR_CHOICES)
    index = models.IntegerField(default=0)
    nested = models.BooleanField(default=False)

    error_messages = {
        'no_previous_operator': "No previous operator found for condition",
        'no_conditions': "Group contains no conditions",
        'cyclic_ref': "Cyclic reference detected"
    }

    def evaluate(self, obj, condition_set=None):
        conditions = self.conditions
        conditions_count = conditions.count()

        if condition_set is None:
            condition_set = set()
        else:
            for condition in conditions:
                if condition in condition_set:
                    raise RuntimeError(self.error_messages['cyclic_ref'])
                else:
                    condition_set.add(condition)

        if conditions_count > 0:
            result = conditions[0].evaluate(obj=obj, condition_set=condition_set)
            for i in range(1, conditions_count):
                operator = conditions[i - 1].operator
                if operator is None:
                    raise RuntimeError(self.error_messages['no_previous_operator'])
                result = Operator.operate(operator=operator, a=result, b=conditions[i].evaluate(obj=obj,
                                                                                                condition_set=condition_set))
        else:
            raise RuntimeError(self.error_messages['no_conditions'])

        return result

    def add_condition(self, condition, index=0, operator=None):
        raise NotImplementedError

    def create_nested_group(self, model, index=0, operator=None):
        raise NotImplementedError

    def copy(self, expression):
        group = type(self).objects.get(pk=self.pk)
        group.pk = None
        group.expression = expression
        group.save()

        conditions = self.conditions
        for condition in conditions:
            condition.copy(group)

        return group

    @property
    def conditions(self):
        raise NotImplementedError

    class Meta:
        abstract = True


class ModelExpressionConditionGroup(ConditionGroup):
    # the model expression that the group belongs to
    expression = models.ForeignKey(ModelExpression, on_delete=models.CASCADE)

    def js(self, indent=''):
        conditions = self.conditions
        conditions_count = conditions.count()

        if conditions_count > 0:
            js = conditions[0].js()
            for i in range(1, conditions_count):
                operator = conditions[i - 1].operator
                if operator is None:
                    raise RuntimeError(self.error_messages['no_previous_operator'])
                js = js + ' '
                js = js + Operator.js(operator=operator)
                js = js + ' '
                js = js + conditions[i].js()
        else:
            raise RuntimeError(self.error_messages['no_conditions'])

        return js

    def add_condition(self, condition, index=0, operator=None):
        return self.modelexpressioncondition_set.create(group=self, condition=condition,
                                                        index=index, operator=operator)

    def create_nested_group(self, model, index=0, operator=None):
        group = ModelExpressionConditionGroup.objects.create(expression=self.expression,
                                                             nested=True)
        nested_group = NestedModelExpressionConditionGroup.objects.create(parent_group=self,
                                                                          child_group=group,
                                                                          model=model)

        self.add_condition(nested_group, index=index, operator=operator)
        return group

    @property
    def conditions(self):
        return self.modelexpressioncondition_set.order_by('index')

    class Meta:
        verbose_name_plural = "Model expression condition groups"

    def __str__(self):
        return f"Model expression condition group"


class FieldExpressionConditionGroup(ConditionGroup):
    # the field expression that the group belongs to
    expression = models.ForeignKey(FieldExpression, on_delete=models.CASCADE)

    def add_condition(self, condition, index=0, operator=None):
        return self.fieldexpressioncondition_set.create(group=self, condition=condition,
                                                        index=index, operator=operator)

    def create_nested_group(self, model, index=0, operator=None):
        group = FieldExpressionConditionGroup.objects.create(expression=self.expression,
                                                             nested=True)
        nested_group = NestedFieldExpressionConditionGroup.objects.create(parent_group=self,
                                                                          child_group=group,
                                                                          model=model)
        self.add_condition(condition=nested_group, index=index, operator=operator)
        return group

    @property
    def conditions(self):
        return self.fieldexpressioncondition_set.order_by('index')

    class Meta:
        verbose_name_plural = "Field expression condition groups"

    def __str__(self):
        return f"Field expression condition group"


class Condition(PolymorphicModel):
    exception_messages = {
        'model_missing_field': "Provided model does not contain field named %",
        'model_field_mismatch': "Provided model contains field named % but type does not match",
    }

    error_messages = {
        'cyclic_ref': "Cyclic reference detected"
    }

    model = models.ForeignKey(Model, on_delete=NON_POLYMORPHIC_CASCADE)

    def evaluate(self, obj, condition_set=None):
        raise NotImplementedError

    def js(self, indent=''):
        raise NotImplementedError

    def copy(self, model):
        condition = type(self).objects.get(pk=self.pk)

        condition.pk = None
        condition.id = None
        condition.model = model
        condition.save()

        return condition

    class Meta:
        verbose_name_plural = "Conditions"

    def __str__(self):
        return "Base Condition"


class ModelExpressionCondition(models.Model):
    # the group which the condition belongs to
    group = models.ForeignKey(ModelExpressionConditionGroup, on_delete=models.CASCADE)
    # the condition in the group
    condition = models.OneToOneField(Condition, on_delete=models.CASCADE)
    # the optional operator for the condition
    operator = models.TextField(blank=True, null=True, choices=Operator.OPERATOR_CHOICES)
    # index of the condition
    index = models.IntegerField(default=0)

    def evaluate(self, obj, condition_set=None):
        return self.condition.evaluate(obj, condition_set)

    def js(self, indent=''):
        return self.condition.js()

    def copy(self, group):
        # simply copy the model expression condition
        expression_condition = ModelExpressionCondition.objects.get(pk=self.pk)
        expression_condition.pk = None
        expression_condition.group = group
        expression_condition.condition = expression_condition.condition.copy(group.expression.model)
        expression_condition.save()

        return expression_condition

    class Meta:
        verbose_name_plural = "Model expression conditions"

    def __str__(self):
        return f"{self.condition}"


class FieldExpressionCondition(models.Model):
    # the group which the condition belongs to
    group = models.ForeignKey(FieldExpressionConditionGroup, on_delete=models.CASCADE)
    # the condition in the group
    condition = models.OneToOneField(Condition, on_delete=models.CASCADE)
    # the optional operator for the condition
    operator = models.TextField(blank=True, null=True, choices=Operator.OPERATOR_CHOICES)
    # index of the condition
    index = models.IntegerField(default=0)

    def evaluate(self, obj, condition_set=None):
        return self.condition.evaluate(obj, condition_set)

    def copy(self, group):
        # simply copy the model expression condition
        expression_condition = FieldExpressionCondition.objects.get(pk=self.pk)
        expression_condition.pk = None
        expression_condition.group = group
        expression_condition.condition = expression_condition.condition.copy(group.expression.field.model)
        expression_condition.save()

        return expression_condition

    class Meta:
        verbose_name_plural = "Field expression conditions"

    def __str__(self):
        return f"{self.condition}"


class NestedModelExpressionConditionGroup(Condition):
    # the parent group
    parent_group = models.ForeignKey(ModelExpressionConditionGroup,
                                     related_name='nestedgroups_set',
                                     on_delete=NON_POLYMORPHIC_CASCADE)
    # the nested child group
    child_group = models.OneToOneField(ModelExpressionConditionGroup,
                                       on_delete=NON_POLYMORPHIC_CASCADE)

    def evaluate(self, obj, condition_set=None):
        if condition_set is None:
            condition_set = set()
        if self.child_group in condition_set:
            # if already evaluated, then cyclic ref detected
            raise RuntimeError(self.error_messages['cyclic_ref'])
        else:
            condition_set.add(self.child_group)
        return self.child_group.evaluate(obj, condition_set)

    def js(self, indent=''):
        raise NotImplementedError

    class Meta:
        verbose_name_plural = "Nested model expression condition groups"

    def __str__(self):
        return "Nested model condition group"


class NestedFieldExpressionConditionGroup(Condition):
    # the parent group
    parent_group = models.ForeignKey(FieldExpressionConditionGroup,
                                        related_name='nestedgroups_set',
                                        on_delete=NON_POLYMORPHIC_CASCADE)
    # the nested child group
    child_group = models.OneToOneField(FieldExpressionConditionGroup,
                                    on_delete=NON_POLYMORPHIC_CASCADE)

    def evaluate(self, obj, condition_set=None):
        if condition_set is None:
            condition_set = set()
        if self.child_group in condition_set:
            # if already evaluated, then cyclic ref detected
            raise RuntimeError(self.error_messages['cyclic_ref'])
        else:
            condition_set.add(self.child_group)
        return self.child_group.evaluate(obj, condition_set)

    def js(self, indent=''):
        raise NotImplementedError

    class Meta:
        verbose_name_plural = "Nested field expression condition groups"

    def __str__(self):
        return "Nested field condition group"


class TextFieldCondition(Condition):
    # the field to test against
    field = models.ForeignKey(TextField, on_delete=NON_POLYMORPHIC_CASCADE)
    # the right hand side of the condition
    rhs = models.TextField(blank=True)

    CONDITION_EXISTS = 'exist'
    CONDITION_MATCH = 'match'
    CONDITION_DOES_NOT_MATCH = 'doesnotmatch'

    CONDITION_EXISTS_VERBOSE = "Exists"
    CONDITION_MATCH_VERBOSE = "Matches"
    CONDITION_DOES_NOT_MATCH_VERBOSE = "Does Not Match"

    CONDITION_CHOICES = [
        (CONDITION_EXISTS, CONDITION_EXISTS_VERBOSE),
        (CONDITION_MATCH, CONDITION_MATCH_VERBOSE),
        (CONDITION_DOES_NOT_MATCH, CONDITION_DOES_NOT_MATCH_VERBOSE),
    ]

    # the condition to be met
    condition = models.CharField(max_length=32, blank=False, default=CONDITION_MATCH, choices=CONDITION_CHOICES)

    def evaluate(self, obj, condition_set=None):
        # try to get value from choice first
        try:
            value = obj.get(self.field.name).value
        except AttributeError:
            value = obj.get(self.field.name)

        if self.condition == self.CONDITION_EXISTS:
            return value is not None and not value
        elif self.condition == self.CONDITION_DOES_NOT_MATCH:
            return value != self.rhs

        return value == self.rhs

    def js(self, indent=''):
        if self.condition == self.CONDITION_EXISTS:
            return f'$(\'#{self.field.input_id}\')[0].value.trim()'
        elif self.condition == self.CONDITION_DOES_NOT_MATCH:
            return f'$(\'#{self.field.input_id}\')[0].value.trim() != \'{self.rhs}\''
        return f'$(\'#{self.field.input_id}\')[0].value.trim() == \'{self.rhs}\''

    def copy(self, model):
        # ensure that the model has the same field
        field = model.fields.get(self.field.name)

        if field is None:
            raise RuntimeError(self.exception_messages['model_missing_field'] % self.field.name)
        if not isinstance(field, TextField):
            raise RuntimeError(self.exception_messages['model_field_mismatch'] % self.field.name)

        condition = TextFieldCondition.objects.get(pk=self.pk)
        condition.pk = None
        condition.id = None
        condition.field = field
        condition.model = model
        condition.save()

        return condition

    class Meta:
        verbose_name_plural = f"TextField conditions"

    def __str__(self):
        return f"{self.field} {self.condition} \'{self.rhs}\'"


class BooleanFieldCondition(Condition):
    # the field to test against
    field = models.ForeignKey(BooleanField, on_delete=NON_POLYMORPHIC_CASCADE)
    # the right hand side of the condition
    rhs = models.BooleanField()

    def evaluate(self, obj, condition_set=None):
        return obj.get(self.field.name) == self.rhs

    def js(self, indent=''):
        return f'$(\'#{self.field.input_id}\')[0].value == \'{self.rhs}\''

    def copy(self, model):
        # ensure that the model has the same field
        field = model.fields.get(self.field.name)

        if field is None:
            raise RuntimeError(self.exception_messages['model_missing_field'] % self.field.name)
        if not isinstance(field, BooleanField):
            raise RuntimeError(self.exception_messages['model_field_mismatch'] % self.field.name)

        condition = BooleanFieldCondition.objects.get(pk=self.pk)
        condition.pk = None
        condition.id = None
        condition.model = model
        condition.field = field
        condition.save()

        return condition

    class Meta:
        verbose_name_plural = "Boolean Field conditions"

    def __str__(self):
        return f"{self.field} == {self.rhs}"


class AlwaysTrueCondition(Condition):
    def evaluate(self, obj, condition_set=None):
        return True

    def js(self, indent=''):
        return f'true'

    class Meta:
        verbose_name_plural = "Always true conditions"

    def __str__(self):
        return "Always true condition"


class AlwaysFalseCondition(Condition):
    def evaluate(self, obj, condition_set=None):
        return False

    def js(self, indent=''):
        return f'false'

    class Meta:
        verbose_name_plural = "Always false conditions"

    def __str__(self):
        return "Always false condition"


class HasAttributeCondition(Condition):
    attribute_name = models.CharField(max_length=256, blank=False)

    def evaluate(self, obj, condition_set=None):
        return hasattr(obj, self.attribute_name)

    def js(self, indent=''):
        return f'false'

    class Meta:
        verbose_name_plural = "Has attribute conditions"

    def __str__(self):
        return f"Has attribute {self.attribute_name}"
