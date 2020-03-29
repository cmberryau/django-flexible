import datetime

from django import forms
from django.utils.translation import gettext as _
from django.utils.duration import duration_string


class DurationWidget(forms.MultiWidget):
    error_messages = {
        'overflow': _("OverflowError")
    }

    def __init__(self, attrs=None):
        _attrs = {
            'class': 'form-control',
            'type': 'number',
            'min': '0',
            'step': '1',
            'onchange': 'durationFieldOnValueChange(this);',
        }

        hours_attrs = {
            'placeholder': _('Hours')
        }

        if attrs is not None:
            hours_attrs.update(attrs)
        hours_attrs.update(_attrs)

        minutes_attrs = {
            'placeholder': _('Minutes')
        }

        if attrs is not None:
            minutes_attrs.update(attrs)
        minutes_attrs.update(_attrs)

        _widgets = (
            forms.TextInput(attrs=hours_attrs),
            forms.TextInput(attrs=minutes_attrs),
        )

        super().__init__(_widgets, attrs=None)

    def decompress(self, value):
        if type(value) is datetime.timedelta:
            # convert timedelta objects to strings using django's inbuilt method
            value = duration_string(value)

        if value == self.error_messages['overflow']:
            return [None, None]

        if value:
            dhms = value.replace(' ', ':').split(':')

            hours = int(dhms[-3])
            if int(hours) == 0:
                hours = None

            # try get days, may not be in split string
            try:
                # django style timedelta str
                days = int(dhms[-4])

                if int(days) != 0:
                    if hours is None:
                        hours = 0
                    hours = hours + days * 24
            except IndexError:
                pass

            minutes = int(dhms[-2])
            if int(minutes) == 0:
                minutes = None

            return [hours, minutes]
        return [None, None]

    def value_from_datadict(self, data, files, name):
        value_list = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)]
        try:
            hours_raw = value_list[0]
            minutes_raw = value_list[1]

            if hours_raw is None and minutes_raw is None:
                duration = None
            else:
                if not hours_raw or hours_raw is None:
                    hours = 0
                else:
                    hours = int(hours_raw)

                if not minutes_raw or minutes_raw is None:
                    minutes = 0
                else:
                    minutes = int(minutes_raw)

                duration = datetime.timedelta(
                    hours=hours,
                    minutes=minutes,
                )
        except ValueError:
            # empty strings are valid as none
            return ''
        except OverflowError:
            # returning any non empty string will raise invalid error in form
            return self.error_messages['overflow']
        else:
            return duration

    template_name = 'widgets/duration.html'
    supports_microseconds = False
