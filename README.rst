Pyramid REST
------------

* First draft of a pyramid rest proof of concept to be presented/discussed.
* Features included:

    * resource definition which configure routes/views;
    * resources are added to config introspector and related to their routes,views, sub-resource and parent resource;
    * end user defines REST methods (index, create, show, update, delete, new, edit);
    * by default:

      * HTTP 405 is returned for any method not provided;
      * permissions 'index, create, show, update, delete, new, edit' are associated to respective method;

* 3 ways to configure resource:

    #. Imperative using `config.add_resource`, it will associate class in views module to resource ::

        config.add_resource('applications')       # .views.applications:Applications
        config.add_resource('applications.users') # .views.applications_users:ApplicationsUsers

    #. Declarative using `Resource` class (cornice style)::

        app_users = Resource('applications.users')

        @app_users.index()
        def index(context, request):
            pass

        @app.show()
        def show(context, request, app_id):
            pass

    #. Declarative using `resource_config` decorator::

        @resource_config('applications.users')
        class AppUsers(object):

            def __init__(self, context, request):
                pass

            def index(self):
                return {}

            @method_config(renderer='example.mako')
            def edit(self, app_id):
                return {}


What next?
----------

#. Custom renderer which adapts response format depending on Accept header
#. Links
#. Validation
#. Pagination
#. Automatic resource definition of SQLAlchemy entities.
