Development version
-------------------

* Switch to github.
* Add support for mongo database:

 * Setting in ini file ``pyramid_rest.mongo`` considered true by default
 * ``MongoConnection`` is registered to registry
 * Two properties added to ``request``: ``mongo_connection`` and ``mongo_db``
 * Mongo connection gets uri from ``os.environ['MONGO_URI']``
 * Database name comes from ``os.environ['MONGO_DB_NAME']``
 * Any resource view with a ``model_class`` class attribute with value being
   a definition of a ``mongokit.Document`` can inherit
   ``pyramid_rest.mongo.DocumentView`` to inherit all default actions.

* Add custom renderer which adapts output format depending on accept headers,
  format supported are ``application/json`` & ``application/bson``


0.1.0
-----

* Rename ResourceUtility to ResourceConfigurator to make its role clearer.
* Force human-friendly names for route pattern variables and view callable
  parameters, e.g. /applications/{application_id}/users/{id} and
  show(context, request, application_id, id)
* Remove ability to configure resource separator in resource names: it's always
  '.'
* Singular resources via *add_singular_resource* directive or *singular=True*
  keyword argument on *Resource* or *resource_config*
* Moved example from tests directory to root directory: used in test and useful
  for documentation.


0.0.1
-----

* Collection resource only
* Imperative mode via *add_resource* directive
* Declarative mode via *Resource* class
* Declarative mode view *resource_config* decorator
