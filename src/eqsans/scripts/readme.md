
>>> from django.template import Template, Context
>>> from django.conf import settings
>>> settings.configure()
>>> t = Template('My name is {{ my_name }}.')
>>> c = Context({'my_name': 'Daryl Spitzer'})
>>> t.render(c)
u'My name is Daryl Spitzer.'

https://docs.djangoproject.com/en/dev/ref/templates/api/#configuring-the-template-system-in-standalone-mode
