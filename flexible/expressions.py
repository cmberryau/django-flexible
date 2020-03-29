import logging

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from flexible.apps import JS_INDENT

logger = logging.getLogger(__file__)


class Operator:
    OPERATOR_CHOICE_AND = 'AND'
    OPERATOR_CHOICE_OR = 'OR'

    OPERATOR_CHOICES = [
        (OPERATOR_CHOICE_AND, OPERATOR_CHOICE_AND),
        (OPERATOR_CHOICE_OR, OPERATOR_CHOICE_OR),
    ]

    error_messages = {
        'invalid_operator': "No valid operator choice found",
    }

    @classmethod
    def operate(cls, operator, a, b):
        if operator == cls.OPERATOR_CHOICE_AND:
            return a and b
        elif operator == cls.OPERATOR_CHOICE_OR:
            return a or b
        raise RuntimeError(cls.error_messages['invalid_operator'])

    @classmethod
    def js(cls, operator):
        if operator == cls.OPERATOR_CHOICE_AND:
            return '&&'
        elif operator == cls.OPERATOR_CHOICE_OR:
            return '||'
        raise RuntimeError(cls.error_messages['invalid_operator'])

    @classmethod
    def AND(cls):
        return cls.OPERATOR_CHOICE_AND

    @classmethod
    def OR(cls):
        return cls.OPERATOR_CHOICE_OR


class ModelExpression(models.Model):
    # the name of the expression
    name = models.CharField(max_length=256)
    # the model using the expression
    model = models.ForeignKey('Model', on_delete=models.CASCADE)

    def add_action(self, action, index=0):
        return ModelExpressionAction.objects.create(expression=self,
                                                    action=action,
                                                    index=index)

    def add_alternate_action(self, action, index=0):
        return AlternateModelExpressionAction.objects.create(expression=self,
                                                             action=action,
                                                             index=index)

    def create_group(self, index=0, operator=None):
        return self.modelexpressionconditiongroup_set.create(expression=self,
                                                             index=index,
                                                             operator=operator)

    def execute(self, fields):
        if self._evaluate(fields):
            return self._execute_actions(fields=fields)
        return self._execute_alternate_actions(fields=fields)

    def js(self, indent=''):
        try:
            groups = self.groups
            groups_count = groups.count()
            if groups_count <= 0:
                raise RuntimeError("No condition groups found")

            # condition groups
            js = JS_INDENT
            js = js + f'if('
            if groups_count > 1:
                js = js + '('
            js = js + groups[0].js(indent)
            if groups_count > 1:
                js = js + ')'
            for i in range(1, groups_count):
                operator = groups[i - 1].operator
                if operator is None:
                    raise RuntimeError("No previous operator found")
                js = js + ' '
                js = js + Operator.js(operator=operator)
                js = js + ' '
                if groups_count > 1:
                    js = js + '('
                js = js + groups[i].js(indent)
                if groups_count > 1:
                    js = js + ')'
            js = js + ')'
            js = js + '\n'
            js = js + indent + '{\n'

            # actions
            js = js + self._actions_js(self.modelexpressionaction_set.order_by('index'), indent + JS_INDENT)
            js = js + indent + '}'

            # alternate actions
            actions = self.alternatemodelexpressionaction_set.order_by('index')
            if actions.count() > 0:
                js = js + '\n'
                js = js + indent + 'else\n'
                js = js + indent + '{\n'
                js = js + self._actions_js(actions, indent + JS_INDENT)
                js = js + indent + '}'
        except RuntimeError as e:
            # print out the error on the web browser console
            js = JS_INDENT + f'console.log(\'{e.args[0]}\');'
            # log error
            logger.error(f"RuntimeError for \'{self.name}\': {e.args[0]}", stack=True)

        return js

    def copy(self, model):
        # make a copy of the expression first
        expression = ModelExpression.objects.get(pk=self.pk)
        expression.pk = None
        expression.model = model
        expression.save()

        # copy model expression condition groups
        for group in self.modelexpressionconditiongroup_set.all():
            group.copy(expression)

        # a reference dict: old action obj => new action obj
        copy_action_dict = dict()

        # copy model expression actions
        for model_expression_action in self.modelexpressionaction_set.all():
            copied_me_action = model_expression_action.copy(expression)
            copy_action_dict[model_expression_action.action] = copied_me_action.action

        # copy model expression alternate actions
        for alternate_model_expression_action in self.alternatemodelexpressionaction_set.all():
            # if alt action is same as action, ref the already copied the action obj
            if alternate_model_expression_action.action in copy_action_dict:
                alternate_model_expression_action.copy(expression, copy_action_dict[alternate_model_expression_action.action])
            else:
                alternate_model_expression_action.copy(expression)

        return expression

    def _evaluate(self, fields):
        groups = self.groups
        if groups.count() <= 0:
            raise RuntimeError("No condition groups found")

        # condition evaluation
        result = groups[0].evaluate(obj=fields)
        for i in range(1, groups.count()):
            operator = groups[i - 1].operator
            if operator is None:
                raise RuntimeError("No previous operator found for group")
            result = Operator.operate(operator=operator, a=result, b=groups[i].evaluate(obj=fields))

        return result

    def _execute_actions(self, fields):
        return_values = []
        actions = self.modelexpressionaction_set.order_by('index')
        for action in actions:
            return_values.append(action.action.execute(fields))

    def _execute_alternate_actions(self, fields):
        return_values = []
        actions = self.alternatemodelexpressionaction_set.order_by('index')
        for action in actions:
            return_values.append(action.action.execute(fields))

    @property
    def groups(self):
        return self.modelexpressionconditiongroup_set.filter(nested=False).order_by('index')

    @classmethod
    def _actions_js(cls, actions, indent=''):
        js = ''
        for expression_action in actions:
            js = js + indent + expression_action.action.js()
            js = js + '\n'
        return js

    class Meta:
        verbose_name_plural = "Model expressions"

    def __str__(self):
        return self.name


class ModelExpressionActionBase(models.Model):
    # the model expression that owns this action
    expression = models.ForeignKey(ModelExpression, on_delete=models.CASCADE)
    # the action to be executed
    action = models.OneToOneField('Action', on_delete=models.CASCADE)
    # the index of the expression action
    index = models.IntegerField(default=0)

    def copy(self, expression, action=None):
        o = type(self).objects.get(pk=self.pk)
        o.pk = None
        o.id = None
        o.expression = expression
        if action is not None:
            o.action = action
        else:
            o.action = o.action.copy(expression.model)
        o.save()

        return o

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.action} for {self.expression}"


class ModelExpressionAction(ModelExpressionActionBase):
    class Meta:
        verbose_name_plural = "Model expression actions"


class AlternateModelExpressionAction(ModelExpressionActionBase):
    class Meta:
        verbose_name_plural = "Alternate model expression actions"


class FieldExpression(models.Model):
    # the name of the expression
    name = models.CharField(max_length=256)
    # the field using the expression
    field = models.OneToOneField('Field', on_delete=models.CASCADE)

    def create_group(self, index=0, operator=None):
        return self.fieldexpressionconditiongroup_set.create(expression=self,
                                                             index=index,
                                                             operator=operator)

    def add_action(self, action, index=0):
        return FieldExpressionAction.objects.create(expression=self,
                                                    action=action,
                                                    index=index)

    def add_default_action(self, action):
        return DefaultFieldExpressionAction.objects.create(expression=self,
                                                           action=action)

    def execute(self, obj):
        groups = self.groups
        actions = self.actions

        groups_count = groups.count()
        if groups_count <= 0:
            raise RuntimeError("No condition groups found")

        if actions.count() != groups_count:
            raise RuntimeError("Actions count does not match groups count")

        for i in range(0, groups_count):
            if groups[i].evaluate(obj=obj):
                return actions[i].action.execute(obj=obj)

        return self.defaultfieldexpressionaction.action.execute(obj=obj)

    def copy(self, field):
        # copy the field expression first
        field_expression = FieldExpression.objects.get(pk=self.pk)
        field_expression.pk = None
        field_expression.field = field
        field_expression.save()

        groups = self.groups
        for group in groups:
            group.copy(field_expression)

        actions = self.actions
        for action in actions:
            action.copy(field_expression)

        try:
            self.defaultfieldexpressionaction.copy(field_expression)
        except ObjectDoesNotExist:
            pass

        return field_expression

    @property
    def groups(self):
        return self.fieldexpressionconditiongroup_set.filter(nested=False).order_by('index')

    @property
    def actions(self):
        return self.fieldexpressionaction_set.order_by('index')

    class Meta:
        verbose_name_plural = "Field expressions"

    def __str__(self):
        return self.name


class FieldExpressionActionBase(models.Model):
    # the action to be executed
    action = models.OneToOneField('Action', on_delete=models.CASCADE)

    def copy(self, expression):
        raise NotImplementedError

    @property
    def _expression(self):
        raise NotImplementedError

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.action} for {self._expression}"


class FieldExpressionAction(FieldExpressionActionBase):
    # the model expression that owns this action
    expression = models.ForeignKey(FieldExpression, on_delete=models.CASCADE)
    # the index of the action
    index = models.IntegerField(default=0)

    def copy(self, expression):
        field_expression_action = FieldExpressionAction.objects.get(pk=self.pk)
        field_expression_action.pk = None
        field_expression_action.expression = expression
        field_expression_action.action = self.action.copy(expression.field.model)
        field_expression_action.save()

        return field_expression_action

    @property
    def _expression(self):
        return self.expression

    class Meta:
        verbose_name_plural = "Field expression actions"


class DefaultFieldExpressionAction(FieldExpressionActionBase):
    # the model expression that owns this action
    expression = models.OneToOneField(FieldExpression, on_delete=models.CASCADE)

    def copy(self, expression):
        field_expression_action = DefaultFieldExpressionAction.objects.get(pk=self.pk)
        field_expression_action.pk = None
        field_expression_action.expression = expression
        field_expression_action.action = self.action.copy(expression.field.model)
        field_expression_action.save()

        return field_expression_action

    @property
    def _expression(self):
        return self.expression

    class Meta:
        verbose_name_plural = "Default field expression actions"
