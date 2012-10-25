# -*- coding: utf-8 -*-
from docutils.parsers.rst.directives import unchanged
from sphinx.util.compat import Directive, nodes

from pyramid.config import Configurator

def setup(app):
    app.add_directive('rest_resource', ResourceDirective)


def convert_to_list(argument):
    """Convert a comma separated list into a list of python values"""
    if argument is None:
        return []
    else:
        return [i.strip() for i in argument.split(',')]

def convert_to_list_required(argument):
    if argument is None:
        raise ValueError('argument required but none supplied')
    return convert_to_list(argument)





class ResourceDirective(Directive):

    has_content = True
    option_spec = {
        'modules': convert_to_list_required,
        }
    domain = 'pyramid_rest'


    def __init__(self, *args, **kwargs):
        super(ResourceDirective, self).__init__(*args, **kwargs)
        self.env = self.state.document.settings.env
        self.config = Configurator(settings=None)
        self.config.include('pyramid_rest')

    def run(self):
        self.scan()
        return []

    def scan(self):
        for module in self.options.get('modules'):
            self.config.scan(module)
        self.config.commit()
