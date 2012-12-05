Pyramid REST
------------

* First draft of a pyramid extension to build RESTful web application.
* Features included:

    * resource definition which configure routes/views, i.e:

        * a resource 'application':

            * route [GET/POST] /applications
            * route [GET/DELETE/PUT] /applications/{application_id}
            * route GET /applications/{application_id}/new
            * route GET /applications/{application_id}/edit

        * a resource 'application.user':

            * route [GET/POST] /applications/{application_id}/users
            * route [GET/DELETE/PUT] /applications/{application_id}/users/{user_id}
            * route GET /applications/{application_id}/users/new
            * route GET /applications/{application_id}/users/edit

        * a singular resource 'application.user.score':

            * route [GET/PUT] /applications/{application_id}/users/{user_id}/score
            * route GET /applications/{application_id}/users/{user_id}/score/edit


    * resources are added to config introspector and related to their routes,views, sub-resource and parent resource;
    * end user defines REST methods (index, create, show, update, delete, new, edit);
    * by default:

      * HTTP 405 is returned for any method not provided;
      * permissions 'index, create, show, update, delete, new, edit' are associated to respective method;

* 3 ways to configure resource:

    #. Imperative using `config.add_resource`, it will associate class in views module to resource ::

        config.add_resource('application')       # .views.applications:ApplicationsView
        config.add_resource('application.user')  # .views.application_users:ApplicationUsersView

    #. Declarative using `Resource` class (cornice style)::

        app_users = Resource('application.user')

        @app_users.index()
        def index(context, request, application_id):
            pass

        @app_users.show()
        def show(context, request, application_id, id):
            pass


    #. Declarative using `resource_config` decorator::

        @resource_config('application.user')
        class AppUsers(object):

            def __init__(self, context, request):
                pass

            def index(self, application_id):
                return {}

            @method_config(renderer='example.mako')
            def edit(self, application_id, id):
                return {}


What next?
----------

#. Security
#. HTTP PATCH method: http://tools.ietf.org/html/rfc5789
#. Resource Scaffolding command;
#. Links;
#. Validation;
#. Pagination;
#. Automatic resource definition of SQLAlchemy entities;
#. Have a view parameter in add_resource to override view definition;


Code/Feedbacks
--------------

https://github.com/hadrien/pyramid_rest
