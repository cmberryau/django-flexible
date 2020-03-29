from django.test import TestCase
from django.db import transaction

from flexible.expressions import *
from flexible.tests_utils import *


class FlexibleConditionsTestCase(TestCase):
    def test_create_model_expression_condition_group(self):
        model = create_mock_model()
        expression = ModelExpression.objects.create(name='demo expression', model=model)
        ModelExpressionConditionGroup.objects.create(expression=expression)

    def test_model_expression_condition_group_js_no_condition(self):
        model = create_mock_model()
        expression = ModelExpression.objects.create(name='demo expression', model=model)
        model_expression_condition_group = ModelExpressionConditionGroup.objects.create(expression=expression)
        try:
            model_expression_condition_group.js()
        except RuntimeError as e:
            self.assertEqual(e.args[0], ModelExpressionConditionGroup.error_messages['no_conditions'])
        else:
            self.fail()

    def test_model_expression_condition_group_js_no_condition(self):
        model = create_mock_model()
        expression = ModelExpression.objects.create(name='demo expression', model=model)
        model_expression_condition_group = ModelExpressionConditionGroup.objects.create(expression=expression)
        try:
            model_expression_condition_group.js()
        except RuntimeError as e:
            self.assertEqual(e.args[0], ModelExpressionConditionGroup.error_messages['no_conditions'])
        else:
            self.fail()

    def test_model_expression_condition_group_create_nested_group(self):
        model = create_mock_model()
        expression = ModelExpression.objects.create(name='demo expression', model=model)
        model_expression_condition_group = ModelExpressionConditionGroup.objects.create(expression=expression)
        model_expression_condition_group.create_nested_group(model)

    def test_nested_model_expression_condition_group_evaluate_and_js(self):
        model = create_mock_model()
        model_instance = create_mock_model_instance(model)[0]
        expression = ModelExpression.objects.create(name='demo expression', model=model)
        expression.save()
        condition_group_1 = ModelExpressionConditionGroup.objects.create(expression=expression)
        condition_group_1.save()
        condition_1 = AlwaysTrueCondition(model=model)
        condition_1.save()
        condition_group_1.add_condition(condition_1)
        condition_group_2 = ModelExpressionConditionGroup.objects.create(expression=expression)
        condition_group_2.save()
        condition_2 = AlwaysFalseCondition(model=model)
        condition_2.save()
        condition_group_2.add_condition(condition_2)
        nested_group = NestedModelExpressionConditionGroup.objects.create(model=model,
                                                                          parent_group=condition_group_1,
                                                                          child_group=condition_group_2)
        try:
            with transaction.atomic():
                nested_group.evaluate(model_instance)
        except RuntimeError as e:
            self.fail(e.args[0])
        else:
            pass

    def test_text_field_condition_evaluate_and_js_and_copy(self):
        model = create_mock_model()
        model_instance = create_mock_model_instance(model)[0]
        field = model.get_fields()[0]

        condition = TextFieldCondition.objects.create(model=model, field=field, rhs='rhs')
        condition.save()
        try:
            condition.evaluate(obj=model_instance)
            condition.js()
            condition.copy(model)
        except RuntimeError as e:
            self.fail(e.args[0])
        else:
            pass

    def test_boolean_field_condition_evaluate_and_js_and_copy(self):
        model = create_mock_model()
        model_instance = create_mock_model_instance(model)[0]
        field = model.get_fields()[3]

        condition = BooleanFieldCondition.objects.create(model=model, field=field, rhs=True)
        condition.save()
        try:
            condition.evaluate(obj=model_instance)
            condition.js()
            condition.copy(model)
        except RuntimeError as e:
            self.fail(e.args[0])
        else:
            pass
