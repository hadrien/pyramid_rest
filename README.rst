Pyramid REST
------------

* First draft of a pyramid extension to build RESTful web application.
* Features included:

    * resource definition which configure routes/views, i.e:

        * a resource 'application':

            * route [GET/POST] /applications
            * route [GET/DELETE/PUT] /applications/{id0}
            * route GET /applications/{id0}/new
            * route GET /applications/{id0}/edit

        * a resource 'application.user':

            * route [GET/POST] /applications/{id0}/users
            * route [GET/DELETE/PUT] /applications/{id0}/users/{id1}
            * route GET /applications/{id0}/users/new
            * route GET /applications/{id0}/users/edit

        * a singular resource 'application.user.score':

            * route [GET/PUT] /applications/{id0}/users/{id1}/score
            * route GET /applications/{id0}/users/{id1}/score/edit


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
        def index(context, request):
            pass

        @app_users.show()
        def show(context, request, app_id):
            pass

    #. Declarative using `resource_config` decorator::

        @resource_config('application.user')
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

#. Singular name in resource;
#. Naming conventions:
   * resource name: application.user
   * view: .views.application_users:ApplicationUsersView
#. Full test coverage;
#. Url generation:
   * resource.get_url()
   * resource.get_path()
   * utility.resource_url()
   * utility.resource_path()
#. Support for non-collection resource;
#. Force identifier names.
#. Resource Scaffolding command;
#. Custom renderer which adapts response format depending on Accept header;
#. Links;
#. Validation;
#. Pagination;
#. Automatic resource definition of SQLAlchemy entities;
#. Have a view parameter in add_resource to override view definition;


Code/Feedbacks
--------------

https://bitbucket.org/hadrien/pyramid_rest
