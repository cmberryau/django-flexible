from django.db import transaction

from flexible.forms import *
from flexible.models_tests import *
from flexible.tests_utils import *
# from accounts.tests_utils import create_anon_request


# class FlexibleFormsTestCase(TestCase):
#     def test_model_instance_form_new_instance_valid_input(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         model_instance = create_mock_model_instance(model)[0]

#         request.POST = model_instance.to_post_dict()

#         form = ModelInstanceForm(model, instance=None, data=request.POST)

#         self.assertTrue(form.is_valid())
#         self.assertIsNotNone(form.save())

#     def test_model_instance_form_new_instance_invalid_input(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         model_instance = create_mock_model_instance(model)[0]

#         # invalid input
#         request.POST = model_instance.to_post_dict()
#         request.POST['testrequiredtextfield'] = ''

#         form = ModelInstanceForm(model, instance=None, data=request.POST)

#         self.assertFalse(form.is_valid())
#         self.assertIsNotNone(form.save())
#         # saving will still work, as if the field is empty,
#         # it deletes the instance not updating it

#     def test_model_instance_form_existing_instance_valid_input(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         model_instance = create_mock_model_instance(model)[0]

#         request.POST = model_instance.to_post_dict()

#         form = ModelInstanceForm(model, instance=model_instance, data=request.POST)

#         self.assertTrue(form.is_valid())
#         self.assertIsNotNone(form.save())

#     def test_model_instance_form_existing_instance_invalid_input(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         model_instance = create_mock_model_instance(model)[0]

#         # invalid input
#         request.POST = model_instance.to_post_dict()
#         request.POST['testrequiredtextfield'] = ''

#         form = ModelInstanceForm(model, instance=model_instance, data=request.POST)

#         self.assertFalse(form.is_valid())
#         self.assertIsNotNone(form.save())
#         # saving will still work, as if the field is empty,
#         # it deletes the instance not updating it

#     def test_model_instance_form_field_instance_not_exist(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         model_instance = create_mock_model_instance(model)[0]
#         request.POST = model_instance.to_post_dict()
#         request.POST['testrequiredtextfield'] = ''
#         form = ModelInstanceForm(model, instance=model_instance, data=request.POST)
#         form.is_valid()
#         form.save()
#         # at this stage, testrequiredtextfield field instance for this model does not exist,
#         # because it was deleted by updating its value to empty via form

#         # now change it to something, then the form will create a new field instance
#         request.POST = model_instance.to_post_dict()
#         form = ModelInstanceForm(model, instance=model_instance, data=request.POST)
#         self.assertTrue(form.is_valid())
#         self.assertIsNotNone(form.save())

#     def test_model_instance_form_negative_duration(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         model_instance = create_mock_model_instance(model)[0]

#         request.POST = model_instance.to_post_dict()
#         request.POST['testrequireddurationfield_0'] = -100
#         request.POST['testrequireddurationfield_1'] = -100

#         form = ModelInstanceForm(model, instance=None, data=request.POST)

#         self.assertFalse(form.is_valid())
#         error_list = form.errors.as_data()['__all__']
#         # if more than 1 error, then something is wrong
#         if len(error_list) != 1:
#             self.fail()
#         # check the error code
#         else:
#             if error_list[0].code != 'negative_numbers':
#                 self.fail()

#     def test_model_instance_form_duration_overflow(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         model_instance = create_mock_model_instance(model)[0]

#         request.POST = model_instance.to_post_dict()
#         request.POST['testrequireddurationfield_0'] = 999999999999999999999999999999999999999999999999
#         request.POST['testrequireddurationfield_1'] = 999999999999999999999999999999999999999999999999

#         form = ModelInstanceForm(model, instance=None, data=request.POST)

#         self.assertFalse(form.is_valid())
#         error_list = form.errors.as_data()['testrequireddurationfield']
#         # if more than 1 error, then something is wrong
#         if len(error_list) != 1:
#             self.fail()
#         # check the error code
#         else:
#             if error_list[0].code != 'invalid':
#                 self.fail()

#     def test_model_instance_form_decimal_overflow(self):
#         def test(decimal, expected_validity):
#             request = create_anon_request('/')
#             model = create_mock_model()
#             model_instance = create_mock_model_instance(model)[0]

#             request.POST = model_instance.to_post_dict()
#             # override the field instance value
#             request.POST['testdecimalfield'] = decimal

#             form = ModelInstanceForm(model, instance=None, data=request.POST)

#             if expected_validity:
#                 self.assertTrue(form.is_valid())
#                 self.assertIsNotNone(form.save())
#             else:
#                 self.assertFalse(form.is_valid())
#                 error_list = form.errors.as_data()['__all__']
#                 # if more than 1 error, then something is wrong
#                 if len(error_list) != 1:
#                     self.fail()
#                 # check the error code
#                 else:
#                     if error_list[0].code != 'exceeded_digits':
#                         self.fail()

#         # test several cases to make sure this works
#         test(999999999999999999999999999999999999999999999999999999999999, False)
#         test(9999999.999999999, False)
#         test(9999999.9999, False)
#         test(9999999.999, True)
#         test(1234567, True)
#         test(1234567.12345678, True)
#         test(12345678.12345678, False)
#         test(12345678, False)
#         test(None, True)

#     def test_field_form_new_field_valid_input(self):
#         def test(field_type):
#             request = create_anon_request('/')
#             model = Model(name='ModelTest', ready=True)
#             model.save()
#             field = None

#             request.POST = {
#                 'field_type': field_type,
#                 'field_name': 'test1',
#                 'field_required': None,
#                 'field_description': 'test desc',
#             }

#             form = FieldForm(request, model, field=field, data=request.POST)

#             self.assertTrue(form.is_valid())
#             self.assertIsNotNone(form.save())

#         test('text')
#         test('integer')
#         test('decimal')
#         test('boolean')
#         test('date')
#         test('duration')
#         test('email')

#     def test_field_form_new_field_invalid_input(self):
#         def test(field_type):
#             request = create_anon_request('/')
#             model = create_mock_model()
#             field = None

#             request.POST = {
#                 'field_type': field_type,
#                 'field_name': '',
#                 'field_required': True,
#                 'field_description': 'test desc',
#             }

#             form = FieldForm(request, model, field=field, data=request.POST)

#             self.assertFalse(form.is_valid())
#             try:
#                 with transaction.atomic():
#                     form.save()
#             except IntegrityError:
#                 pass

#             else:
#                 self.fail()

#         test('text')
#         test('integer')
#         test('decimal')
#         test('boolean')
#         test('date')
#         test('duration')
#         test('email')

#     def test_field_form_update_field_valid_input(self):
#         def test(field_type):
#             request = create_anon_request('/')
#             model = create_mock_model()
#             field = create_mock_field(model, TextField)

#             request.POST = {
#                 'field_type': field_type,
#                 'field_name': 'test1',
#                 'field_required': False,
#                 'field_description': 'test desc',
#             }

#             form = FieldForm(request, model, field=field, data=request.POST)

#             self.assertTrue(form.is_valid())
#             self.assertIsNotNone(form.save())

#         test('text')
#         test('integer')
#         test('decimal')
#         test('boolean')
#         test('date')
#         test('duration')
#         test('email')

#     def test_field_form_update_field_invalid_input(self):
#         def test(field_type):
#             request = create_anon_request('/')
#             model = create_mock_model()
#             field = create_mock_field(model, TextField)

#             request.POST = {
#                 'field_type': field_type,
#                 'field_name': '',
#                 'field_required': False,
#                 'field_description': 'test desc',
#             }

#             form = FieldForm(request, model, field=field, data=request.POST)

#             self.assertFalse(form.is_valid())
#             try:
#                 with transaction.atomic():
#                     form.save()
#             except IntegrityError:
#                 pass
#             else:
#                 self.fail()

#         test('text')
#         test('integer')
#         test('decimal')
#         test('boolean')
#         test('date')
#         test('duration')
#         test('email')

#     def test_field_form_duplicate_name(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         field = None

#         request.POST = {
#             'field_type': 'decimal',
#             'field_name': 'test1',
#             'field_required': True,
#             'field_description': 'test desc',
#         }

#         form = FieldForm(request, model, field=field, data=request.POST)

#         if form.is_valid():
#             form.save()

#         form = FieldForm(request, model, field=field, data=request.POST)
#         self.assertFalse(form.is_valid())
#         try:
#             form.save()
#         except IntegrityError:
#             pass
#         else:
#             self.fail()

#     def test_field_choice_form_new_choice(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         field = create_mock_field(model, TextField)

#         request.POST = {
#             field.name: 'test choice'
#         }

#         form = FieldChoiceForm(request, field, data=request.POST)

#         self.assertTrue(form.is_valid())
#         self.assertIsNotNone(form.save())

#     def test_field_choice_form_unsupported(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         field = create_mock_field(model, DecimalField)

#         request.POST = {
#             field.name: 'test choice'
#         }

#         try:
#             FieldChoiceForm(request, field, data=request.POST)
#         except RuntimeError:
#             pass
#         else:
#             self.fail()

#     def test_field_choice_form_update_choice(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         field = create_mock_field(model, TextField)
#         choice_value = 'test choice'
#         choice = field.create_mock_choice(value=choice_value)

#         request.POST = {
#             field.name: choice_value
#         }

#         form = FieldChoiceForm(request, field, choice=choice, data=request.POST)

#         self.assertTrue(form.is_valid())
#         self.assertIsNotNone(form.save())

#     def test_field_choice_form_empty_choice(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         field = create_mock_field(model, TextField)
#         choice_value = 'test choice'
#         choice = field.create_mock_choice(value=choice_value)

#         request.POST = {
#             field.name: ''
#         }

#         form = FieldChoiceForm(request, field, choice=choice, data=request.POST)

#         try:
#             form.is_valid()
#         except RuntimeError:
#             pass
#         else:
#             self.fail()

#         try:
#             form.save()
#         except IntegrityError:
#             pass
#         else:
#             self.fail()

#     def test_field_choice_form_duplicate_choice(self):
#         request = create_anon_request('/')
#         model = create_mock_model()
#         field = create_mock_field(model, TextField)

#         request.POST = {
#             field.name: 'test choice'
#         }

#         form = FieldChoiceForm(request, field, data=request.POST)

#         if form.is_valid():
#             form.save()

#         form = FieldChoiceForm(request, field, data=request.POST)

#         self.assertFalse(form.is_valid())
#         try:
#             form.save()
#         except IntegrityError:
#             pass
#         else:
#             self.fail()
