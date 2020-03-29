from django.test import TestCase
from flexible.tests_utils import *


class FlexibleChoicesTestCase(TestCase):

    def test_text_field_choice(self):
        model = create_mock_model()
        model_2 = model.copy('second model')
        field = create_mock_field(model, TextField)
        field_2 = field.copy(model_2)
        choice = TextFieldChoice.objects.create(field=field, value='mock value')
        try:
            copied_choice = choice.copy(field_2)
        except Exception as e:
            self.fail(e)
        else:
            pass

        self.assertIsNotNone(copied_choice)
        self.assertNotEqual(choice, copied_choice)
        self.assertEqual(choice.value, copied_choice.value)

    def test_integer_field_choice(self):
        model = create_mock_model()
        model_2 = model.copy('second model')
        field = create_mock_field(model, IntegerField)
        field_2 = field.copy(model_2)
        choice = IntegerFieldChoice.objects.create(field=field, value=1)
        try:
            copied_choice = choice.copy(field_2)
        except Exception as e:
            self.fail(e)
        else:
            pass

        self.assertIsNotNone(copied_choice)
        self.assertNotEqual(choice, copied_choice)
        self.assertEqual(choice.value, copied_choice.value)

    def test_decimal_field_choice(self):
        model = create_mock_model()
        model_2 = model.copy('second model')
        field = create_mock_field(model, DecimalField)
        field_2 = field.copy(model_2)
        choice = DecimalFieldChoice.objects.create(field=field, value=2.0)
        try:
            copied_choice = choice.copy(field_2)
        except Exception as e:
            self.fail(e)
        else:
            pass

        self.assertIsNotNone(copied_choice)
        self.assertNotEqual(choice, copied_choice)
        self.assertEqual(choice.value, copied_choice.value)

    def test_duration_field_choice(self):
        model = create_mock_model()
        model_2 = model.copy('second model')
        field = create_mock_field(model, DurationField)
        field_2 = field.copy(model_2)
        choice = DurationFieldChoice.objects.create(field=field, value=datetime.timedelta.min)
        try:
            copied_choice = choice.copy(field_2)
        except Exception as e:
            self.fail(e)
        else:
            pass

        self.assertIsNotNone(copied_choice)
        self.assertNotEqual(choice, copied_choice)
        self.assertEqual(choice.value, copied_choice.value)

    def test_date_field_choice(self):
        model = create_mock_model()
        model_2 = model.copy('second model')
        field = create_mock_field(model, DateField)
        field_2 = field.copy(model_2)
        choice = DateFieldChoice.objects.create(field=field, value=datetime.date.today())
        try:
            copied_choice = choice.copy(field_2)
        except Exception as e:
            self.fail(e)
        else:
            pass

        self.assertIsNotNone(copied_choice)
        self.assertNotEqual(choice, copied_choice)
        self.assertEqual(choice.value, copied_choice.value)

    def test_email_field_choice(self):
        model = create_mock_model()
        model_2 = model.copy('second model')
        field = create_mock_field(model, EmailField)
        field_2 = field.copy(model_2)
        choice = EmailFieldChoice.objects.create(field=field, value='steve@apple.com')
        try:
            copied_choice = choice.copy(field_2)
        except Exception as e:
            self.fail(e)
        else:
            pass

        self.assertIsNotNone(copied_choice)
        self.assertNotEqual(choice, copied_choice)
        self.assertEqual(choice.value, copied_choice.value)
