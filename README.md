# django-flexible

Flexible model package for django. Tested to work with django 2.2.11.

Provides support for the following field types:

- Text
- Integer
- Decimal
- Boolean
- Date
- Duration
- Email

Provides support for:

- Choices
- Required
- Evaluated fields (field value is determined by other field values)
- Testing conditions against individual field values and whole model instances
- Executing actions based on field values, easily extended

Requires PostgreSQL as the database backend (will drop requirement eventually)

## Installation

1.

```
pip install django-flexible
```


2.

Add the following to your INSTALLED_APPS

```
'polymorphic',
'crispy_forms',
'flexible'
```

## Examples

### Creating a model

```
from flexible.models import Model, TextField


# create a blank model
model = Model(name='Example model', ready=True)
model.save()

# add a text field to the model
text_field = TextField.objects.create(model=model, index=0, verbose_name='TestRequiredTextField', required=True)
```

### Creating a model instance

```
model_instance = model.create_instance()

text_field.create_instance(model_instance, 'Test value')
```
