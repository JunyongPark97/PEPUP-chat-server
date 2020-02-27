from rest_framework import serializers


class NullToBlankCharField(serializers.CharField):
    def __init__(self, **kwargs):
        keys = [('allow_blank', True), ('required', False)]
        for key, default_value in keys:
            if key in  kwargs:
                raise Exception('Keyword argument "{}" is redundant for NullToBlankCharField'.format(key))
            kwargs.update({key: default_value})
        super(NullToBlankCharField, self).__init__(**kwargs)

    def run_validation(self, data=serializers.empty):
        if data == '' or data is None:
            return ''
        return super(NullToBlankCharField, self).run_validation(data)