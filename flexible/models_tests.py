from django.test import TestCase
from django.db.utils import IntegrityError

from flexible.models import *
from flexible.choices import *
from flexible.expressions import *
from flexible.conditions import *
from flexible.actions import *
from flexible.tests_utils import create_mock_model, create_mock_model_instance, create_mock_model_with_shared_action


class ModelTests(TestCase):
    def test_model_and_instance_creation(self):
        # model must be created first
        model = create_mock_model()
        self.assertIsNotNone(model)

        # create the instance next
        instance, values = create_mock_model_instance(model)
        self.assertIsNotNone(instance)

    # tests methods for querying model instances
    def test_model_instance_queries(self):
        # create a model
        model = create_mock_model()

        expected_model_field_count = 28
        expected_instance_field_count = 21

        # get the fields of the model
        model_fields = model.get_fields()
        model_field_count = len(model_fields)
        self.assertIsNotNone(model_fields)
        self.assertEqual(expected_model_field_count, model_field_count)

        # ensure no instances of the model exist
        model_instances = model.get_instances()
        self.assertIsNotNone(model_instances)
        self.assertEqual(0, len(model_instances))

        # create a model instance
        instance, values = create_mock_model_instance(model)

        # ensure one instance of the model exists
        model_instances = model.get_instances()
        self.assertIsNotNone(model_instances)
        self.assertEqual(1, len(model_instances))

        # validate the fields from the instance
        for i in range(0, len(model_instances)):
            self.assertIsNotNone(model_instances[i].fields)
            self.assertEqual(expected_instance_field_count, len(model_instances[i].fields))

            # validate the actual field instance values
            for key in model_instances[i].fields:
                self.assertEqual(values[key], model_instances[i].fields[key].value)

    # tests that the same field instances cannot be added twice to the same model instance
    def test_field_instance_added_twice(self):
        model = Model(name='ModelTest')
        model.save()

        field0 = TextField.objects.create(model=model, verbose_name='TestField', required=True)

        model_instance = model.create_instance()

        # create the first field instance
        field0.create_instance(model_instance=model_instance, value="YabbaDabba")

        try:
            # create the second field instance, should fail on save
            field0.create_instance(model_instance=model_instance, value="Oogabooga")
            self.fail("Should fail on save!")
        except IntegrityError:
            pass

    def test_model_copy_method(self):
        def test(model):
            model_count = Model.objects.all().count()
            model_expression_count = ModelExpression.objects.all().count()
            model_expression_condition_group_count = ModelExpressionConditionGroup.objects.all().count()
            model_expression_action_count = ModelExpressionAction.objects.all().count()
            alternative_model_expression_action_count = AlternateModelExpressionAction.objects.all().count()
            model_description_component_count = ModelDescriptionComponent.objects.all().count()

            field_count = Field.objects.all().count()
            text_field_choice_count = TextFieldChoice.objects.all().count()
            integer_field_choice_count = IntegerFieldChoice.objects.all().count()
            decimal_field_choice_count = DecimalFieldChoice.objects.all().count()
            date_field_choice_count = DateFieldChoice.objects.all().count()
            email_field_choice_count = EmailFieldChoice.objects.all().count()
            field_expression_count = FieldExpression.objects.all().count()
            field_expression_condition_group_count = FieldExpressionConditionGroup.objects.all().count()
            field_expression_action_count = FieldExpressionAction.objects.all().count()
            default_field_expression_action_count = DefaultFieldExpressionAction.objects.all().count()

            condition_count = Condition.objects.all().count()
            action_count = Action.objects.all().count()

            model_copy = model.copy()

            # check that all related db objects have doubled
            self.assertEqual(model_count * 2, Model.objects.all().count())
            self.assertEqual(model_expression_count * 2, ModelExpression.objects.all().count())
            self.assertEqual(model_expression_condition_group_count * 2,
                             ModelExpressionConditionGroup.objects.all().count())
            self.assertEqual(model_expression_action_count * 2, ModelExpressionAction.objects.all().count())
            self.assertEqual(alternative_model_expression_action_count * 2,
                             AlternateModelExpressionAction.objects.all().count())
            self.assertEqual(model_description_component_count * 2, ModelDescriptionComponent.objects.all().count())

            self.assertEqual(field_count * 2, Field.objects.all().count())
            self.assertEqual(text_field_choice_count * 2, TextFieldChoice.objects.all().count())
            # self.assertEqual(integer_field_choice_count * 2, IntegerFieldChoice.objects.all().count())
            # self.assertEqual(decimal_field_choice_count * 2, DecimalFieldChoice.objects.all().count())
            # self.assertEqual(date_field_choice_count * 2, DateFieldChoice.objects.all().count())
            # self.assertEqual(email_field_choice_count * 2, EmailFieldChoice.objects.all().count())
            self.assertEqual(field_expression_count * 2, FieldExpression.objects.all().count())
            self.assertEqual(field_expression_condition_group_count * 2,
                             FieldExpressionConditionGroup.objects.all().count())
            self.assertEqual(field_expression_action_count * 2, FieldExpressionAction.objects.all().count())
            self.assertEqual(default_field_expression_action_count * 2,
                             DefaultFieldExpressionAction.objects.all().count())

            self.assertEqual(condition_count * 2, Condition.objects.all().count())
            self.assertEqual(action_count * 2, Action.objects.all().count())

            # ensure that we made a copy and the pk differs
            self.assertIsNotNone(model_copy)
            self.assertNotEqual(model.pk, model_copy.pk)

            # ensure that we have the same number of fields
            fields = model.field_set.all()
            fields_copy = model_copy.field_set.all()
            self.assertGreater(fields.count(), 0)
            self.assertEqual(fields.count(), fields_copy.count())

            # ensure each field is copied
            for i in range(0, fields.count()):
                field = fields[i]
                field_copy = fields_copy[i]

                # ensure that the pk and models differ
                self.assertNotEqual(field.pk, field_copy.pk)
                self.assertNotEqual(field.model_id, field_copy.model_id)

                # ensure that the other attributes of the fields do not differ
                self.assertEqual(field.index, field_copy.index)
                self.assertEqual(field.name, field_copy.name)
                self.assertEqual(field.verbose_name, field_copy.verbose_name)
                self.assertEqual(field.required, field_copy.required)
                self.assertEqual(field.hidden, field_copy.hidden)
                self.assertEqual(field.description, field_copy.description)
                self.assertEqual(field.evaluated, field_copy.evaluated)
                self.assertEqual(field.generate_metrics, field_copy.generate_metrics)

                # check that fields reference correct models
                self.assertEqual(model.pk, field.model_id)
                self.assertEqual(model_copy.pk, field_copy.model_id)

                # ensure that the choices were copied
                if field.supports_choices:
                    self.assertEqual(len(field.choices), len(field_copy.choices))
                    for j in range(0, len(field.choices)):
                        choice = field.choices[j]
                        choice_copy = field_copy.choices[j]

                        # ensure that the pks and fields differ
                        self.assertNotEqual(choice.pk, choice_copy.pk)
                        self.assertNotEqual(choice.field_id, choice_copy.field_id)

                        # ensure that the other attributes do not differ
                        self.assertEqual(choice.index, choice_copy.index)
                        self.assertEqual(choice.value, choice_copy.value)

                        # check the choices reference the correct field
                        self.assertEqual(field.pk, choice.field_id)
                        self.assertEqual(field_copy.pk, choice_copy.field_id)

                # ensure that any field expression was copied
                try:
                    field_expression = field.fieldexpression
                except ObjectDoesNotExist:
                    field_expression = None

                try:
                    field_expression_copy = field_copy.fieldexpression
                    if field_expression is None:
                        self.fail("Original field has no expression, but field copy has expression")
                except ObjectDoesNotExist:
                    field_expression_copy = None
                    if field_expression is not None:
                        self.fail("Original field has expression, but field copy has no expression")

                if field_expression_copy is not None:
                    # ensure that the pks and fields differ
                    self.assertNotEqual(field_expression.pk, field_expression_copy.pk)
                    self.assertNotEqual(field_expression.field_id, field_expression_copy.field_id)

                    # ensure that the other attributes do not differ
                    self.assertEqual(field_expression.name, field_expression_copy.name)

                    # ensure that the expression references the correct field
                    self.assertEqual(field.pk, field_expression.field_id)
                    self.assertEqual(field_copy.pk, field_expression_copy.field_id)

                    # ensure that the field expression condition groups are copied
                    condition_groups = field_expression.fieldexpressionconditiongroup_set.all()
                    condition_groups_copy = field_expression_copy.fieldexpressionconditiongroup_set.all()
                    self.assertGreater(condition_groups.count(), 0)
                    self.assertEqual(condition_groups.count(), condition_groups_copy.count())

                    for j in range(0, condition_groups.count()):
                        condition_group = condition_groups[j]
                        condition_group_copy = condition_groups_copy[j]

                        # ensure that pk and expression differ
                        self.assertNotEqual(condition_group.pk, condition_group_copy.pk)
                        self.assertNotEqual(condition_group.expression_id, condition_group_copy.expression_id)

                        # ensure that other attributes do not differ
                        self.assertEqual(condition_group.operator, condition_group_copy.operator)
                        self.assertEqual(condition_group.index, condition_group_copy.index)
                        self.assertEqual(condition_group.nested, condition_group_copy.nested)

                        # ensure that condition group references the correct field expressions
                        self.assertEqual(field_expression.pk, condition_group.expression_id)
                        self.assertEqual(field_expression_copy.pk, condition_group_copy.expression_id)

                        # assert that conditions within condition groups are copied
                        conditions = condition_group.conditions
                        conditions_copy = condition_group_copy.conditions
                        self.assertEqual(conditions.count(), conditions_copy.count())
                        for k in range(0, conditions.count()):
                            condition = conditions[k]
                            condition_copy = conditions_copy[k]

                            # ensure that pk, group, condition and condition model differ
                            self.assertNotEqual(condition.pk, condition_copy.pk)
                            self.assertNotEqual(condition.group_id, condition_copy.group_id)
                            self.assertNotEqual(condition.condition_id, condition_copy.condition_id)
                            self.assertNotEqual(condition.condition.model, condition_copy.condition.model)

                            # ensure that the operator and index are the same
                            self.assertEqual(condition.operator, condition_copy.operator)
                            self.assertEqual(condition.index, condition_copy.index)

                            # ensure that the concrete condition is the correct type
                            self.assertTrue(isinstance(condition_copy.condition, condition.condition.__class__))

                            # ensure that the conditions reference the correct condition groups
                            self.assertEqual(condition_group.pk, condition.group_id)
                            self.assertEqual(condition_group_copy.pk, condition_copy.group_id)

                    # ensure that the field expression actions are copied
                    actions = field_expression.fieldexpressionaction_set.all()
                    actions_copy = field_expression_copy.fieldexpressionaction_set.all()
                    self.assertGreater(actions.count(), 0)
                    self.assertEqual(actions.count(), actions_copy.count())

                    for j in range(0, actions.count()):
                        action = actions[j]
                        action_copy = actions_copy[j]

                        # ensure that pk, expression, action and action model differ
                        self.assertNotEqual(action.pk, action_copy.pk)
                        self.assertNotEqual(action.expression_id, action_copy.expression_id)
                        self.assertNotEqual(action.action_id, action_copy.action_id)
                        self.assertNotEqual(action.action.model, action_copy.action.model)

                        # ensure that other attributes do not differ
                        self.assertEqual(action.index, action_copy.index)
                        self.assertTrue(isinstance(action_copy.action, action.action.__class__))

                        # ensure that the actions reference the correct field expression
                        self.assertEqual(field_expression.pk, action.expression_id)
                        self.assertEqual(field_expression_copy.pk, action_copy.expression_id)

                    # ensure that the field expression default action is copied
                    try:
                        default_action = field_expression.defaultfieldexpressionaction
                    except ObjectDoesNotExist:
                        default_action = None

                    try:
                        default_action_copy = field_expression_copy.defaultfieldexpressionaction
                        if default_action is None:
                            self.fail(
                                "Original expression has no default action, but expression copy has default action")

                        # ensure the the pk, expression, action and action model differ
                        self.assertNotEqual(default_action.pk, default_action_copy.pk)
                        self.assertNotEqual(default_action.expression_id, default_action_copy.expression_id)
                        self.assertNotEqual(default_action.action.pk, default_action_copy.action.pk)
                        self.assertNotEqual(default_action.action.model_id, default_action_copy.action.model_id)

                        # check that other attributes do not differ
                        self.assertTrue(isinstance(default_action.action, default_action_copy.action.__class__))

                        # ensure that the action references the correct field expression
                        self.assertEqual(field_expression.pk, default_action.expression_id)
                        self.assertEqual(field_expression_copy.pk, default_action_copy.expression_id)

                    except ObjectDoesNotExist:
                        if default_action is not None:
                            self.fail(
                                "Original expression has default action, but expression copy hsa no default action")

            # ensure model expressions are copied
            model_expressions = model.modelexpression_set.all().order_by('name')
            model_expressions_copy = model_copy.modelexpression_set.all().order_by('name')
            self.assertEqual(model_expressions.count(), model_expressions_copy.count())

            for i in range(0, model_expressions.count()):
                model_expression = model_expressions[i]
                model_expression_copy = model_expressions_copy[i]

                # ensure that the pk and model differs
                self.assertNotEqual(model_expression.pk, model_expression_copy.pk)
                self.assertNotEqual(model_expression.model_id, model_expression_copy.model_id)

                # ensure that the name is the same
                self.assertEqual(model_expression.name, model_expression_copy.name)

                # ensure that the model expression references the correct model
                self.assertEqual(model.pk, model_expression.model_id)
                self.assertEqual(model_copy.pk, model_expression_copy.model_id)

                # ensure that the model expression condition groups are copied
                condition_groups = model_expression.modelexpressionconditiongroup_set.all()
                condition_groups_copy = model_expression_copy.modelexpressionconditiongroup_set.all()
                self.assertGreater(condition_groups.count(), 0)
                self.assertEqual(condition_groups.count(), condition_groups_copy.count())

                for j in range(condition_groups.count()):
                    condition_group = condition_groups[j]
                    condition_group_copy = condition_groups_copy[j]

                    # ensure that the pk and expression differs
                    self.assertNotEqual(condition_group.pk, condition_group_copy.pk)
                    self.assertNotEqual(condition_group.expression_id, condition_group_copy.expression_id)

                    # ensure that the operator, index and nested attributes are the same
                    self.assertEqual(condition_group.operator, condition_group_copy.operator)
                    self.assertEqual(condition_group.index, condition_group_copy.index)
                    self.assertEqual(condition_group.nested, condition_group_copy.nested)

                    # ensure that the model expression condition group references the correct model expression
                    self.assertEqual(condition_group.expression_id, model_expression.pk)
                    self.assertEqual(condition_group_copy.expression_id, model_expression_copy.pk)

                    # ensure tht model conditions are copied
                    conditions = condition_group.modelexpressioncondition_set.all()
                    conditions_copy = condition_group_copy.modelexpressioncondition_set.all()
                    self.assertGreater(conditions.count(), 0)
                    self.assertEqual(conditions.count(), conditions_copy.count())

                    for k in range(0, conditions.count()):
                        condition = conditions[k]
                        condition_copy = conditions_copy[k]

                        # ensure that the pk and model are not the same
                        self.assertNotEqual(condition.pk, condition_copy.pk)
                        self.assertNotEqual(condition.group_id, condition_copy.group_id)
                        self.assertNotEqual(condition.condition_id, condition_copy.condition_id)

                        # ensure that the operator and index are the same
                        self.assertEqual(condition.operator, condition_copy.operator)
                        self.assertEqual(condition.index, condition_copy.index)

                        # ensure that then condition references the correct condition group
                        self.assertEqual(condition_group.pk, condition.group_id)
                        self.assertEqual(condition_group_copy.pk, condition_copy.group_id)

                        # ensure that the concrete condition's pk and model are not the same
                        self.assertNotEqual(condition.condition.pk, condition_copy.condition.pk)
                        self.assertNotEqual(condition.condition.model_id, condition_copy.condition.model_id)

                        # ensure that the concrete is the same type
                        self.assertTrue(isinstance(condition_copy.condition, condition.condition.__class__))

                # ensure that the model expression actions are copied
                actions = model_expression.modelexpressionaction_set.all()
                actions_copy = model_expression_copy.modelexpressionaction_set.all()
                self.assertGreater(actions.count(), 0)
                self.assertEqual(actions.count(), actions_copy.count())

                for j in range(0, actions.count()):
                    action = actions[j]
                    action_copy = actions_copy[j]

                    # ensure that the pk, expression and action are not the same
                    self.assertNotEqual(action.pk, action_copy.pk)
                    self.assertNotEqual(action.expression_id, action_copy.expression_id)
                    self.assertNotEqual(action.action_id, action_copy.action_id)

                    # ensure that the index is the same
                    self.assertEqual(action.index, action_copy.index)

                    # ensure that the action references the correct model expression
                    self.assertEqual(model_expression.pk, action.expression_id)
                    self.assertEqual(model_expression_copy.pk, action_copy.expression_id)

                    # ensure that the concrete action pk and model are not the same
                    self.assertNotEqual(action.action.pk, action_copy.action.pk)
                    self.assertNotEqual(action.action.model_id, action_copy.action.model_id)

                    # ensure that the concrete actions are the same type
                    self.assertTrue(isinstance(action_copy.action, action.action.__class__))

                # ensure that the model expression alternate actions are copied
                alternate_actions = model_expression.alternatemodelexpressionaction_set.all()
                alternate_actions_copy = model_expression_copy.alternatemodelexpressionaction_set.all()
                self.assertGreater(alternate_actions.count(), 0)
                self.assertEqual(alternate_actions.count(), alternate_actions_copy.count())

                for j in range(0, alternate_actions.count()):
                    alternate_action = alternate_actions[j]
                    alternate_action_copy = alternate_actions_copy[j]

                    # ensure that the pk, expression and action are not the same
                    self.assertNotEqual(alternate_action.pk, alternate_action_copy.pk)
                    self.assertNotEqual(alternate_action.expression_id, alternate_action_copy.expression_id)
                    self.assertNotEqual(alternate_action.action_id, alternate_action_copy.action_id)

                    # ensure that the index is the same
                    self.assertEqual(alternate_action.index, alternate_action_copy.index)

                    # ensure that the action references the correct model expression
                    self.assertEqual(model_expression.pk, alternate_action.expression_id)
                    self.assertEqual(model_expression_copy.pk, alternate_action_copy.expression_id)

                    # ensure that the concrete action pk and model are not the same
                    self.assertNotEqual(alternate_action.action.pk, alternate_action_copy.action.pk)
                    self.assertNotEqual(alternate_action.action.model_id, alternate_action_copy.action.model_id)

                    # ensure that the concrete actions are the same type
                    self.assertTrue(isinstance(alternate_action_copy.action, alternate_action.action.__class__))

            # ensure model description components are copied
            model_description_components = model.modeldescriptioncomponent_set.all()
            model_description_components_copy = model_copy.modeldescriptioncomponent_set.all()

            self.assertGreater(model_description_components.count(), 0)
            self.assertEqual(model_description_components.count(), model_description_components_copy.count())

            for i in range(0, model_description_components.count()):
                model_description_component = model_description_components[i]
                model_description_component_copy = model_description_components_copy[i]

                # ensure that pk and field differ between the model description components
                self.assertNotEqual(model_description_component.pk, model_description_component_copy.pk)
                self.assertNotEqual(model_description_component.model_id, model_description_component_copy.model_id)
                self.assertNotEqual(model_description_component.field_id, model_description_component_copy.field_id)

                # ensure that the index, field name and field type do not differ
                self.assertEqual(model_description_component.index, model_description_component_copy.index)
                self.assertEqual(model_description_component.field.name, model_description_component_copy.field.name)
                self.assertTrue(isinstance(model_description_component_copy.field,
                                           model_description_component.field.__class__))

                # ensure that the model description components reference the correct models
                self.assertEqual(model.pk, model_description_component.model_id)
                self.assertEqual(model_copy.pk, model_description_component_copy.model_id)

            # delete the model, otherwise the count number assertion would fail
            model.delete()
            model_copy.delete()

        # test a normal case, and a case where action and alt action has the same action obj
        test(create_mock_model())
        test(create_mock_model_with_shared_action())

    def test_true_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and a single group
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group = expression.create_group()
        # the action will return the given value
        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group.add_condition(AlwaysTrueCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)
        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_false_alternate_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and a single group
        expression = FieldExpression.objects.create(field=int_field, name='testExpression')
        group = expression.create_group()
        # the action will return the given value
        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action=action)
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_default_action(action=action)
        # always true condition will fire the action
        group.add_condition(condition=AlwaysFalseCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)
        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_false_no_alternate_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and a single group
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group = expression.create_group()
        # the action will return the given value
        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group.add_condition(AlwaysFalseCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)
        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)
        # test the field evaluation
        try:
            int_field.evaluate(obj=model_instance)
        except ObjectDoesNotExist:
            pass
        else:
            self.fail()

    def test_two_groups_0_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)

        expected_integer_value = 123

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group0.add_condition(AlwaysTrueCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_two_groups_1_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)

        expected_integer_value = 123

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_two_groups_alternate_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)

        expected_integer_value = 123

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=456, model=model)
        expression.add_action(action)
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value,
                                                    model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_two_groups_no_alternate_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)

        expected_integer_value = 123

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        try:
            int_field.evaluate(obj=model_instance)
        except ObjectDoesNotExist:
            pass
        else:
            self.fail()

    def test_three_groups_0_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)
        group2 = expression.create_group(index=2)

        expected_integer_value = 123

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group0.add_condition(AlwaysTrueCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=123, model=model)
        expression.add_action(action)
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=456, model=model)
        expression.add_action(action)
        group2.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=789, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_three_groups_1_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)
        group2 = expression.create_group(index=2)

        expected_integer_value = 123

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=456, model=model)
        expression.add_action(action)
        group2.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=789, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_three_groups_2_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)
        group2 = expression.create_group(index=2)

        expected_integer_value = 123

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=456, model=model)
        expression.add_action(action)
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        # always true condition will fire the action
        group2.add_condition(AlwaysTrueCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=789, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_three_groups_alternate_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)
        group2 = expression.create_group(index=2)

        expected_integer_value = 123

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=456, model=model)
        expression.add_action(action)
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=789, model=model)
        expression.add_action(action)
        group2.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_three_groups_no_alternate_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group1 = expression.create_group(index=1)
        group2 = expression.create_group(index=2)

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=456, model=model)
        expression.add_action(action)
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=789, model=model)
        expression.add_action(action)
        group2.add_condition(AlwaysFalseCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        try:
            int_field.evaluate(obj=model_instance)
        except ObjectDoesNotExist:
            pass
        else:
            self.fail()

    def test_nested_group_0_field_evaluation(self):
        """
        Tests (False or (True)) == True
        """
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group1 = group0.create_nested_group(model=model, index=1)
        # always true condition will fire the action
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_nested_group_1_field_evaluation(self):
        """
        Tests (False or (True or False)) == True
        """
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group1 = group0.create_nested_group(model=model, index=1)
        # always true condition will fire the action
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model), operator=Operator.OR())
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_nested_group_2_field_evaluation(self):
        """
        Tests (False or (True and True)) == True
        """
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group1 = group0.create_nested_group(model=model, index=1)
        # always true condition will fire the action
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model), operator=Operator.AND())
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model))

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_nested_group_3_field_evaluation(self):
        """
        Tests (False or (False)) == False
        """
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group1 = group0.create_nested_group(model=model, index=1)
        # always true condition will fire the action
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_nested_group_4_field_evaluation(self):
        """
        Tests (False or (False or True)) == False
        """
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group1 = group0.create_nested_group(model=model, index=1)
        # always true condition will fire the action
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.AND())
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_nested_group_5_field_evaluation(self):
        """
        Tests ((False or True) or (False or True)) == True
        """
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        group1 = group0.create_nested_group(model=model, index=1, operator=Operator.OR())
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model))

        group2 = group0.create_nested_group(model=model, index=1)
        group2.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group2.add_condition(AlwaysTrueCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_nested_group_6_field_evaluation(self):
        """
        Tests ((False or True) or (False and True)) == True
        """
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action)
        group1 = group0.create_nested_group(model=model, index=1, operator=Operator.OR())
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model))

        group2 = group0.create_nested_group(model=model, index=2)
        group2.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.AND())
        group2.add_condition(AlwaysTrueCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_nested_group_7_field_evaluation(self):
        """
        Tests ((False and True) or (False and True)) == False
        """
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group1 = group0.create_nested_group(model=model, index=1, operator=Operator.OR())
        group1.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.AND())
        group1.add_condition(AlwaysTrueCondition.objects.create(model=model))

        group2 = group0.create_nested_group(model=model, index=2)
        group2.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.AND())
        group2.add_condition(AlwaysTrueCondition.objects.create(model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        evaluated_int_field_value = int_field.evaluate(obj=model_instance)
        self.assertEqual(expected_integer_value, evaluated_int_field_value)

    def test_empty_group_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and one empty condition group
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        expression.create_group(index=0)

        # create an action
        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        try:
            int_field.evaluate(obj=model_instance)
            self.fail()
        except RuntimeError as e:
            self.assertEqual(str(e), ConditionGroup.error_messages['no_conditions'])

    def test_nested_empty_group_field_evaluation(self):
        # create a model, two fields (one evaluated)
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField', required=True,
                                              evaluated=False, model=model)
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)

        # create an expression and one group with one always true condition
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)
        group0.add_condition(AlwaysTrueCondition.objects.create(model=model), operator=Operator.OR())
        # create an empty nested group
        group1 = group0.create_nested_group(model=model)

        # create an action
        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()
        expected_text_value = 'NothingInteresting'
        text_field.create_instance(model_instance=model_instance, value=expected_text_value)

        # test the field instance
        text_field_instance = text_field.get_instance(model_instance=model_instance)
        self.assertEqual(expected_text_value, text_field_instance.value)

        # test the field evaluation
        try:
            int_field.evaluate(obj=model_instance)
            self.fail()
        except RuntimeError as e:
            self.assertEqual(str(e), ConditionGroup.error_messages['no_conditions'])

    def test_model_expression_js_method_one_group_one_condition_one_action(self):
        # create a model with three fields
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField',
                                              required=True,
                                              evaluated=False,
                                              model=model)
        int_field = IntegerField.objects.create(verbose_name='testIntegerField',
                                                required=False,
                                                model=model)

        # create an expression and one group
        expression = ModelExpression.objects.create(name='testExpression',
                                                    model=model)
        group = expression.create_group()

        # create and add a condition
        condition = TextFieldCondition.objects.create(field=text_field,
                                                      rhs='matchingValue',
                                                      condition=TextFieldCondition.CONDITION_MATCH,
                                                      model=model)
        group.add_condition(condition=condition)

        # create and add two actions
        action = ShowFieldAction.objects.create(field=int_field,
                                                model=model)
        expression.add_action(action=action)

        # create and add an alternate action
        alternate_action = HideFieldAction.objects.create(field=int_field,
                                                          model=model)
        expression.add_alternate_action(action=alternate_action)

        # test the expression js generation
        expression_js = expression.js()
        self.assertIsNotNone(expression_js)

        # test the model js generation
        model_js = model.js()
        self.assertIsNotNone(model_js)

    def test_model_expression_js_method_one_group_two_conditions_single_action(self):
        # create a model with three fields
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField',
                                              required=True,
                                              evaluated=False,
                                              model=model)
        int_field = IntegerField.objects.create(verbose_name='testIntegerField',
                                                required=False,
                                                model=model)

        # create an expression and one group
        expression = ModelExpression.objects.create(name='testExpression',
                                                    model=model)
        group = expression.create_group()

        # create and add a condition
        condition = TextFieldCondition.objects.create(field=text_field,
                                                      rhs='matchingValue',
                                                      condition=TextFieldCondition.CONDITION_MATCH,
                                                      model=model)
        group.add_condition(condition=condition, operator=Operator.OR(), index=0)

        # create and add another condition
        condition = TextFieldCondition.objects.create(field=text_field,
                                                      rhs='anotherMatchingValue',
                                                      condition=TextFieldCondition.CONDITION_MATCH,
                                                      model=model)
        group.add_condition(condition=condition, index=1)

        # create and add two actions
        action = ShowFieldAction.objects.create(field=int_field,
                                                model=model)
        expression.add_action(action=action)

        # create and add an alternate action
        alternate_action = HideFieldAction.objects.create(field=int_field,
                                                          model=model)
        expression.add_alternate_action(action=alternate_action)

        # test the expression js generation
        expression_js = expression.js()
        self.assertIsNotNone(expression_js)

        # test the model js generation
        model_js = model.js()
        aaa = action.js()
        self.assertIsNotNone(model_js)

    def test_model_expression_js_method_two_groups_one_condition_single_action(self):
        # create a model with three fields
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testTextField',
                                              required=True,
                                              evaluated=False,
                                              model=model)
        int_field = IntegerField.objects.create(verbose_name='testIntegerField',
                                                required=False,
                                                model=model)

        # create an expression and one group
        expression = ModelExpression.objects.create(name='testExpression',
                                                    model=model)
        group0 = expression.create_group(index=0, operator=Operator.OR())
        group1 = expression.create_group(index=1)

        # create and add a condition
        condition = TextFieldCondition.objects.create(field=text_field,
                                                      rhs='matchingValue',
                                                      condition=TextFieldCondition.CONDITION_MATCH,
                                                      model=model)
        group0.add_condition(condition=condition)

        # create and add another condition
        condition = TextFieldCondition.objects.create(field=text_field,
                                                      rhs='anotherMatchingValue',
                                                      condition=TextFieldCondition.CONDITION_MATCH,
                                                      model=model)
        group1.add_condition(condition=condition)

        # create and add two actions
        action = ShowFieldAction.objects.create(field=int_field,
                                                model=model)
        expression.add_action(action=action)

        # create and add an alternate action
        alternate_action = HideFieldAction.objects.create(field=int_field,
                                                          model=model)
        expression.add_alternate_action(action=alternate_action)

        # test the expression js generation
        expression_js = expression.js()
        self.assertIsNotNone(expression_js)

        # test the model js generation
        model_js = model.js()
        self.assertIsNotNone(model_js)

    def test_model_fieldset_id_invalid_html(self):
        model_name = 'testModel'
        model = Model.objects.create(name=model_name)
        self.assertEqual('fieldset_id_testmodel', model.fieldset_id)

        model_name = 'testModel\'s model'
        model = Model.objects.create(name=model_name)
        self.assertEqual('fieldset_id_testmodel\\\\&\\\\#x27\\\\;s_model', model.fieldset_id)

        model_name = '"testModel" model'
        model = Model.objects.create(name=model_name)
        self.assertEqual('fieldset_id_\\\\&quot\\\\;testmodel\\\\&quot\\\\;_model', model.fieldset_id)

        model_name = 'testModel & testModel model'
        model = Model.objects.create(name=model_name)
        self.assertEqual('fieldset_id_testmodel_\\\\&amp\\\\;_testmodel_model', model.fieldset_id)

    def test_field_div_id_invalid_html(self):
        model_name = 'testModel'
        model = Model.objects.create(name=model_name)

        field = TextField.objects.create(model=model, verbose_name='testTextField', required=False)
        self.assertEqual('div_id_testtextfield', field.div_id)
        field.delete()

        field = TextField.objects.create(model=model, verbose_name='testTextField\'s', required=False)
        self.assertEqual('div_id_testtextfields', field.div_id)
        field.delete()

        field = TextField.objects.create(model=model, verbose_name='testTextField"s', required=False)
        self.assertEqual('div_id_testtextfields', field.div_id)
        field.delete()

        field = TextField.objects.create(model=model, verbose_name='testTextField&', required=False)
        self.assertEqual('div_id_testtextfield', field.div_id)
        field.delete()

    def test_field_input_id_invalid_html(self):
        model_name = 'testModel'
        model = Model.objects.create(name=model_name)

        field = TextField.objects.create(model=model, verbose_name='testTextField', required=False)
        self.assertEqual('id_testtextfield', field.input_id)
        field.delete()

        field = TextField.objects.create(model=model, verbose_name='testTextField\'s', required=False)
        self.assertEqual('id_testtextfields', field.input_id)
        field.delete()

        field = TextField.objects.create(model=model, verbose_name='testTextField"s', required=False)
        self.assertEqual('id_testtextfields', field.input_id)
        field.delete()

        field = TextField.objects.create(model=model, verbose_name='testTextField&', required=False)
        self.assertEqual('id_testtextfield', field.input_id)
        field.delete()

    def test_model_instance_to_json_method(self):
        model = create_mock_model()
        instance = create_mock_model_instance(model)[0]
        values = dict()

        # get the value of both evaluated and non-evaluated fields  
        for field in model.get_fields():
            if field.evaluated:
                values[field.name] = field.to_json(field.evaluate(instance))
            else:
                values[field.name] = field.to_json(field.get_instance(instance).value)

        instance_json = instance.to_json()

        self.assertDictEqual(values, instance_json)
        self.assertIsNotNone(instance_json)

    def test_model_instance_to_csv_method(self):
        model = create_mock_model()
        instance = create_mock_model_instance(model)[0]
        values = dict()

        # get the value of both evaluated and non-evaluated fields  
        for field in model.get_fields():
            if field.evaluated:
                values[field.name] = str(field.to_json(field.evaluate(instance)))
            else:
                values[field.name] = str(field.to_json(field.get_instance(instance).value))

        instance_csv = instance.to_csv()
        instance_csv_values = instance_csv.strip().split(",")

        self.assertSetEqual(set(instance_csv_values), set(values.values()))
        self.assertIsNotNone(instance_csv)

    def test_model_condition_groups_cyclic_reference(self):
        model = Model.objects.create(name='testModel')
        int_field = IntegerField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)
        # create an expression and two groups
        expression = FieldExpression.objects.create(name='testExpression', field=int_field)
        group0 = expression.create_group(index=0)

        expected_integer_value = 123
        action = ReturnIntegerAction.objects.create(value=321, model=model)
        expression.add_action(action)
        group0.add_condition(AlwaysFalseCondition.objects.create(model=model), operator=Operator.OR())
        group1 = group0.create_nested_group(model=model, index=1)
        group1.add_condition(NestedFieldExpressionConditionGroup.objects.create(parent_group=group1, child_group=group0, model=model))

        action = ReturnIntegerAction.objects.create(value=expected_integer_value, model=model)
        expression.add_default_action(action=action)

        # create an instance of the model
        model_instance = model.create_instance()

        # test the field evaluation
        try:
            int_field.evaluate(obj=model_instance)
        except RuntimeError as e:
            if e.args[0] == 'Cyclic reference detected':
                pass
            else:
                self.fail()
        else:
            self.fail()

    def test_model_invalid_expression(self):
        model = Model.objects.create(name='testModel')
        text_field = TextField.objects.create(verbose_name='testEvaluatedIntegerField',
                                                required=False, evaluated=True, model=model)
        # create an expression and a condition group
        expression = ModelExpression.objects.create(name='testExpression', model=model)
        group = expression.create_group(index=0)
        action = ShowFieldAction.objects.create(field=text_field, model=model)
        expression.add_action(action)
        condition = TextFieldCondition.objects.create(field=text_field,
                                                      rhs='matchingValue',
                                                      condition=TextFieldCondition.CONDITION_MATCH,
                                                      model=model)
        group.add_condition(condition, operator=Operator.OR())

        # delete the field, the related lone condition will also be deleted
        text_field.delete()

        try:
            for model_expression in model.modelexpression_set.all():
                model_expression.js()
        except RuntimeError as e:
            # not expecting any runtime errors
            self.fail(e.args[0])

    def test_model_update_json_method(self):
        model = create_mock_model()
        instance = create_mock_model_instance(model)[0]
        instance.update_json()
        values = dict()

        # get evaluated field values
        for field in model.get_fields():
            if field.evaluated:
                values[field.name] = field.to_json(field.evaluate(instance))
            else:
                values[field.name] = field.to_json(field.get_instance(instance).value)

        # new json after update
        instance_json = instance.json

        self.assertDictEqual(values, instance_json)
        self.assertIsNotNone(instance.json)

    def test_model_update_json_empty_field_instance(self):
        model = create_mock_model()
        instance, values = create_mock_model_instance(model)
        instance.fields['testtextfield'].delete()

        instance.update_json()
        self.assertIsNotNone(instance.json)
        self.assertIsNone(instance.json['testtextfield'])

    def test_create_instance_from_values_method(self):
        model = create_mock_model()
        instance, values = create_mock_model_instance(model)

        raise NotImplementedError

    def test_model_equals_method(self):
        model = create_mock_model()
        instance_a, values_a = create_mock_model_instance(model)
        instance_b, values_b = create_mock_model_instance(model)

        self.assertEqual(instance_a.equals(instance_b), values_a == values_b)

    def test_model_instance_description_method(self):
        model = create_mock_model()
        instance, values = create_mock_model_instance(model)
        expected = str(values['testrequiredtextfield']) + ' '
        index = 1

        def test(field_name, expected, index):
            ModelDescriptionComponent.objects.create(model=model, field=model.fields[field_name], index=index)
            index += 1
            expected += str(values[field_name]) + ' '
            self.assertEqual(instance.description, expected)
            return expected, index

        expected, index = test('testtextfield', expected, index)
        expected, index = test('testdecimalfield', expected, index)
        expected, index = test('testdurationfield', expected, index)
        expected, index = test('testemailfield', expected, index)
