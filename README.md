# Ariadne Extensions

Set of scripts and helper utilities to extend [Ariadne GraphQL library](https://github.com/mirumee/ariadne)

## Install

`pip install -e git+https://github.com/aleszoulek/ariadne-extensions.git#egg=ariadne-extensions`

## Features


### Federation support

Support for [Federation Specification](https://www.apollographql.com/docs/apollo-server/federation/federation-spec/)

#### Features

1. Generate federation schema types and directives (`_Any`, `_FieldSet`, ...)
1. Implements `{_service{sdl}}` query
1. Detects boundary types and generates `_Entities` union
1. Implements resolve reference helpers for boundary types queried over `{_entities}` query (`resolve_reference` and `resolve_references` decorators)

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
def resolve_user_reference(reference):
    user_id = reference.get('id')
    return get_user_by_id(user_id)

@user_type.field('name')
def resolve_billing_account(obj, *_, id):
    return f'{obj.first_name} {obj_last_name}'

manager.add_types(user_type, photo_type)
manager.add_types(snake_case_fallback_resolvers)

schema = manager.get_schema()

```
