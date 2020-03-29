import datetime
import random
import string
from decimal import Decimal


from flexible.models import *
from flexible.choices import *
from flexible.expressions import *
from flexible.conditions import *
from flexible.actions import *


def create_random_string(range_begin=0, range_end=1337):
    range_begin = max(range_begin, 0)
    range_end = max(range_end, 0)

    random_range = max(random.randint(range_begin, range_end), 1)
    return ''.join(random.choice(string.ascii_lowercase +
        string.ascii_uppercase + string.digits) for _ in range(random_range))


def create_mock_model():
    model = Model(name='ModelTest', ready=True)
    model.save()

    fields = [
        TextField(model=model, index=0, verbose_name='TestRequiredTextField', required=True),
        IntegerField(model=model, index=1, verbose_name='TestRequiredIntegerField', required=True),
        DecimalField(model=model, index=2, verbose_name='TestRequiredDecimalField', required=True),
        BooleanField(model=model, index=3, verbose_name='TestRequiredBooleanField', required=True),
        DateField(model=model, index=4, verbose_name='TestRequiredDateField', required=True),
        DurationField(model=model, index=5, verbose_name='TestRequiredDurationField', required=True),
        EmailField(model=model, index=6, verbose_name='TestRequiredEmailField', required=True),
        TextField(model=model, index=7, verbose_name='TestTextField', required=False),
        IntegerField(model=model, index=8, verbose_name='TestIntegerField', required=False),
        DecimalField(model=model, index=9, verbose_name='TestDecimalField', required=False),
        BooleanField(model=model, index=10, verbose_name='TestBooleanField', required=False),
        DateField(model=model, index=11, verbose_name='TestDateField', required=False),
        DurationField(model=model, index=12, verbose_name='TestDurationField', required=False),
        EmailField(model=model, index=13, verbose_name='TestEmailField', required=False),
        TextField(model=model, index=14, verbose_name='TestTextFieldWithMetrics', required=False, generate_metrics=True),
        IntegerField(model=model, index=15, verbose_name='TestIntegerFieldWithMetrics', required=False, generate_metrics=True),
        DecimalField(model=model, index=16, verbose_name='TestDecimalFieldWithMetrics', required=False, generate_metrics=True),
        BooleanField(model=model, index=17, verbose_name='TestBooleanFieldWithMetrics', required=False, generate_metrics=True),
        DateField(model=model, index=18, verbose_name='TestDateFieldWithMetrics', required=False, generate_metrics=True),
        DurationField(model=model, index=19, verbose_name='TestDurationFieldWithMetrics', required=False, generate_metrics=True),
        EmailField(model=model, index=20, verbose_name='TestEmailFieldWithMetrics', required=False, generate_metrics=True),
    ]

    for field in fields:
        field.save()

    evaluated_textfield = TextField.objects.create(model=model, index=21, verbose_name='TestEvaluatedTextField', required=False, evaluated=True)
    textfield_expression = FieldExpression.objects.create(name='testTextField_FieldExpression', field=evaluated_textfield)
    textfield_expression_group = textfield_expression.create_group()
    textfield_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    textfield_expression.add_action(ReturnStringAction.objects.create(model=model, value='testReturnString'))
    textfield_expression.add_default_action(ReturnStringAction.objects.create(model=model, value='testDefaultReturnString'))

    evaluated_integerfield = IntegerField.objects.create(model=model, index=22, verbose_name='TestEvaluatedIntegerField', required=False, evaluated=True)
    integerfield_expression = FieldExpression.objects.create(name='testIntegerField_FieldExpression', field=evaluated_integerfield)
    integerfield_expression_group = integerfield_expression.create_group()
    integerfield_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    integerfield_expression.add_action(ReturnIntegerAction.objects.create(model=model, value=1))
    integerfield_expression.add_default_action(ReturnIntegerAction.objects.create(model=model, value=-1))

    evaluated_decimalfield = DecimalField.objects.create(model=model, index=23, verbose_name='TestEvaluatedDecimalField', required=False, evaluated=True)
    decimalfield_expression = FieldExpression.objects.create(name='testDecimalField_FieldExpression', field=evaluated_decimalfield)
    decimalfield_expression_group = decimalfield_expression.create_group()
    decimalfield_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    decimalfield_expression.add_action(ReturnDecimalAction.objects.create(model=model, value=1.234))
    decimalfield_expression.add_default_action(ReturnDecimalAction.objects.create(model=model, value=-1.234))

    evaluated_booleanfield = BooleanField.objects.create(model=model, index=24, verbose_name='TestEvaluatedBooleanField', required=False, evaluated=True)
    booleanfield_expression = FieldExpression.objects.create(name='testBooleanField_FieldExpression', field=evaluated_booleanfield)
    booleanfield_expression_group = booleanfield_expression.create_group()
    booleanfield_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    booleanfield_expression.add_action(ReturnBooleanAction.objects.create(model=model, value=True))
    booleanfield_expression.add_default_action(ReturnBooleanAction.objects.create(model=model, value=False))

    evaluated_datefield = DateField.objects.create(model=model, index=25, verbose_name='TestEvaluatedDateField', required=False, evaluated=True)
    datefield_expression = FieldExpression.objects.create(name='testDateField_FieldExpression', field=evaluated_datefield)
    datefield_expression_group = datefield_expression.create_group()
    datefield_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    datefield_expression.add_action(ReturnDateAction.objects.create(model=model, value=datetime.datetime.today()))
    datefield_expression.add_default_action(ReturnDateAction.objects.create(model=model, value=datetime.datetime.today() + datetime.timedelta(days=1)))

    evaluated_durationfield = DurationField.objects.create(model=model, index=26, verbose_name='TestEvaluatedDurationField', required=False, evaluated=True)
    durationfield_expression = FieldExpression.objects.create(name='testDurationField_FieldExpression', field=evaluated_durationfield)
    durationfield_expression_group = durationfield_expression.create_group()
    durationfield_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    durationfield_expression.add_action(ReturnDurationAction.objects.create(model=model, value=datetime.timedelta(days=1)))
    durationfield_expression.add_default_action(ReturnDurationAction.objects.create(model=model, value=datetime.timedelta(days=-1)))

    evaluated_emailfield = EmailField.objects.create(model=model, index=27, verbose_name='TestEvaluatedEmailField', required=False, evaluated=True)
    emailfield_expression = FieldExpression.objects.create(name='testEmailField_FieldExpression', field=evaluated_emailfield)
    emailfield_expression_group = emailfield_expression.create_group()
    emailfield_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    emailfield_expression.add_action(ReturnEmailAction.objects.create(model=model, value="john@bloggs.com"))
    emailfield_expression.add_default_action(ReturnEmailAction.objects.create(model=model, value="jane@doe.com"))

    random_string = create_random_string(1, 230) + '_anti_palindrome'
    random_int = random.randint(-1337, 1337) + 1
    today = datetime.date.today()
    duration = datetime.timedelta(minutes=random.randint(15, 24 * 60))
    random_decimal = Decimal(random.random() + 1)

    field_choices = [
        TextFieldChoice(value=random_string[::-1], field=fields[0]),
        TextFieldChoice(value=random_string, field=fields[0]),
        IntegerFieldChoice(value=random_int, field=fields[1]),
        IntegerFieldChoice(value=random_int * 2, field=fields[1]),
        DecimalFieldChoice(value=random_decimal, field=fields[2]),
        DecimalFieldChoice(value=random_decimal * 2, field=fields[2]),
        DateFieldChoice(value=today, field=fields[4]),
        DateFieldChoice(value=today + datetime.timedelta(days=1), field=fields[4]),
        DurationFieldChoice(value=duration, field=fields[5]),
        DurationFieldChoice(value=duration + duration, field=fields[5]),
        EmailFieldChoice(value='john@apple.com', field=fields[6]),
        EmailFieldChoice(value='steve@apple.com', field=fields[6]),
    ]

    for field_choice in field_choices:
        field_choice.save()

    model_expression = ModelExpression.objects.create(name="testModelExpression", model=model)
    model_expression_group = model_expression.create_group()
    model_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    model_expression.add_action(ShowFieldAction.objects.create(model=model, field=fields[0]))
    model_expression.add_alternate_action(HideFieldAction.objects.create(model=model, field=fields[0]))

    # add a model description component
    ModelDescriptionComponent.objects.create(model=model, field=fields[0], index=0)

    return model


def create_mock_model_with_shared_action():
    model = create_mock_model()
    fields = model.get_fields()

    model_expression = ModelExpression.objects.create(name="testModelExpression_2", model=model)
    model_expression_group = model_expression.create_group()
    model_expression_group.add_condition(AlwaysTrueCondition.objects.create(model=model))
    shared_action = ShowFieldAction.objects.create(model=model, field=fields[0])
    model_expression.add_action(shared_action)
    model_expression.add_alternate_action(shared_action)

    return model


def create_mock_model_instance(model, model_instance=None):
    if model_instance is None:
        model_instance = model.create_instance()

    fields = model.get_fields()
    values_dict = {
        fields[0].name: fields[0].choices[0].value,
        fields[1].name: fields[1].choices[0].value,
        fields[2].name: fields[2].choices[0].value,
        fields[3].name: bool(random.getrandbits(1)),
        fields[4].name: datetime.date.today(),
        fields[5].name: datetime.timedelta(minutes=random.randint(15, 24 * 60)),
        fields[6].name: fields[6].choices[0].value,
        fields[7].name: create_random_string(),
        fields[8].name: random.randint(-1337, 1337),
        fields[9].name: Decimal('5.678'),
        fields[10].name: bool(random.getrandbits(1)),
        fields[11].name: datetime.date.today() + datetime.timedelta(days=random.randint(1, 10)),
        fields[12].name: datetime.timedelta(minutes=random.randint(15, 24 * 60)),
        fields[13].name: 'bill@microsoft.com',
        fields[14].name: create_random_string(),
        fields[15].name: random.randint(-1337, 1337),
        fields[16].name: Decimal('9.876'),
        fields[17].name: bool(random.getrandbits(1)),
        fields[18].name: datetime.date.today() + datetime.timedelta(days=random.randint(1, 10)),
        fields[19].name: datetime.timedelta(minutes=random.randint(15, 24 * 60)),
        fields[20].name: 'steve@microsoft.com',
    }

    for field in fields:
        if not field.evaluated:
            field.create_instance(model_instance, values_dict[field.name])

    return model_instance, values_dict


def create_mock_field(model, field_type):
    if model.field_set.all().count() > 0:
        index = model.field_set.order_by('-index')[0].index + 1
    else:
        index = 0

    verbose_name = 'mock field name 001'
    description = 'mock desc 001'
    required = True

    field = field_type.objects.create(model=model, index=index, verbose_name=verbose_name,
                                      required=required, description=description)

    return field


def create_mock_choice(self, value):
    raise NotImplementedError


Field.create_mock_choice = create_mock_choice


def textfield_create_mock_choice(self, value):
    return TextFieldChoice.objects.create(field=self, value=value)


TextField.create_mock_choice = textfield_create_mock_choice
