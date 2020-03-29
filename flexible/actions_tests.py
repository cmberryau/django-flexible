from django.test import TestCase
from django.db.utils import IntegrityError

from flexible.models import *
from flexible.choices import *
from flexible.expressions import *
from flexible.conditions import *
from flexible.actions import *
from flexible.tests_utils import create_mock_model, create_mock_model_instance


class ActionsTests(TestCase):
    def test_days_between_dates_action_evaluate_method(self):
        # model must be created first
        model = create_mock_model()
        self.assertIsNotNone(model)

        # find the highest field index
        highest_field_index = model.field_set.order_by('-index')[0].index

        # create the evaluated field and add it to the model
        evaluated_days_field = IntegerField.objects.create(model=model,
                                                           verbose_name='TestEvaluatedDaysField',
                                                           required=False,
                                                           evaluated=True,
                                                           index=highest_field_index+1)

        # create the field expression for the evaluated field
        expression = FieldExpression.objects.create(name='TestEvaluatedDaysField_FieldExpression',
                                                    field=evaluated_days_field)
        group = expression.create_group()
        group.add_condition(AlwaysTrueCondition.objects.create(model=model))
        expression.add_action(ReturnDaysBetweenDatesAction.objects.create(model=model,
                                                                          start=model.fields['testrequireddatefield'],
                                                                          end=model.fields['testdatefield']))

        # create a model instance
        instance, values = create_mock_model_instance(model)
        self.assertIsNotNone(instance)

        # get the expected delta days
        start = values['testrequireddatefield']
        end = values['testdatefield']

        self.assertIsNotNone(start)
        self.assertIsNotNone(end)

        expected_delta_days = (end - start).days

        # evaluate the actual delta days
        actual_delta_days = evaluated_days_field.evaluate(instance)
        self.assertEqual(expected_delta_days, actual_delta_days)
