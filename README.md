# Ariadne Extensions

[![Build Status](https://travis-ci.org/pantheon-systems/ariadne-extensions.svg?branch=master)](https://travis-ci.org/pantheon-systems/ariadne-extensions)
[![Coverage Status](https://coveralls.io/repos/github/pantheon-systems/ariadne-extensions/badge.svg?branch=master)](https://coveralls.io/github/pantheon-systems/ariadne-extensions?branch=master)

Set of scripts and helper utilities to extend [Ariadne GraphQL library](https://github.com/mirumee/ariadne)

## Install

`pip install ariadne-extensions`

## Features


### Federation support

Support for [Federation Specification](https://www.apollographql.com/docs/apollo-server/federation/federation-spec/)

#### Features

1. Generate federation schema types and directives (`_Any`, `_FieldSet`, ...)
1. Implements `{_service{sdl}}` query
1. Detects boundary types and generates `_Entities` union
1. Implements resolve reference helpers for boundary types queried over `{_entities}` query (`resolve_reference` and `resolve_references` decorators)


#### Documentation

##### `ariadne_extensions.federation.FederatedManager`

`FederatedManager` is a class responsible for creating and executable schema that complies with Federation Specification. Similar to what `make_executable_schema` does with ordinary schema file.

Create a FederatedManager instance passing in path to your schema file and QueryType instance. Manager needs to query_type to register `_entities` and `_service` resolvers.

``` python
query_type = QueryType()
manager = federation.FederatedManager(
    schema_sdl_file='/some/path/schema.graphql',
    query=query_type,
)
```

Register any other `ObjectType`s and resolvers by either calling and `add_types` method, or by extending `manager.types` list.

``` python
photo_type = ObjectType('Photo')
thumbnail_type = ObjectType('Thumbnail')

manager.add_types(photo_type, thumbnail_type)
manager.types.append(snake_case_fallback_resolvers)
```

Finally, get a combiled schema. This compiled schema will extend types defined in '/some/path/schema.graphql' with directives, types and queries, that required by Federation Specification protocol.

``` python
schema = manager.get_schema()
```


##### `ariadne_extensions.federation.FederatedObjectType`

If you are using GraphQL Federation, your service schema probably implements some so called "boundary objects". That's where `FederatedObjectType` is useful.

`FederatedObjectType` implements `resolve_reference` and `resolve_references` decorator. Those are used to register functions, that will be called when a federation gateway calls `{_entities{}}` query.

Let's say `User` is a boundary type, with a single `id` key. You need to implement a function, that will accept a dictionary of keys (`{'id': ...} in our example`) and return a `User` instance.
FederatedManager will call this function for every `_entities([{__typename: 'User', id: ...}])` query.

``` python
user_type = federation.FederatedObjectType('User')

@user_type.resolve_reference
def resolve_user_reference(representation, obj, info):
    user_id = representation.get('id')
    return get_user_by_id(user_id)
```

`FederatedObjectType` extends Ariadne's `ObjectType`. You can still use the `field` decorator, `set_alias` method and others as in regular `ObjectType`, and others.

``` python
@user_type.field('name')
def resolve_billing_account(obj, *_, id):
    return f'{obj.first_name} {obj_last_name}'
```

Don't forget to add `user_type` to our manager.

``` python
manager.add_types(user_type)
```


#### Example

```
type User @key(fields: "id") @extends {
    id: ID! @external
    photos: [Photo]!
}

type Photo {
    id: ID!
    url: String!
    description: String
}
```

``` python
from os.path import dirname, join
from ariadne import QueryType, ObjectType, snake_case_fallback_resolvers

from ariadne_extensions import federation

query_type = QueryType()
manager = federation.FederatedManager(
    schema_sdl_file=join(dirname(__file__), 'schema.graphql'),
    query=query_type,
)

user_type = federation.FederatedObjectType('User')
photo_type = ObjectType('Photo')

@user_type.resolve_reference
def resolve_user_reference(representation, obj, info):
    user_id = representation.get('id')
    return get_user_by_id(user_id)

@user_type.field('name')
def resolve_billing_account(obj, *_, id):
    return f'{obj.first_name} {obj_last_name}'

manager.add_types(user_type, photo_type)
manager.add_types(snake_case_fallback_resolvers)

schema = manager.get_schema()

```
