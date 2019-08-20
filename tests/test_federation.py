from io import StringIO
from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest
import graphql
from ariadne import QueryType#, ObjectType

from ariadne_extensions.federation import FederatedManager, FederatedObjectType


SDL = """
type User @key(fields: "id") @extends {
    id: ID! @external
    photos: [Photo]!
}

type Photo {
    id: ID!
    url: String!
    description: String
}
"""
User = namedtuple("User", "id photos")
Info = namedtuple("Info", "schema")


@pytest.fixture(scope='function', name='federated_manager')
def federated_manager_():
    sdl = StringIO(SDL)
    mock_open = MagicMock(return_value=sdl)
    with patch('builtins.open', mock_open):
        query_type = QueryType()
        manager = FederatedManager(
            schema_sdl_file='/tmp/schema.graphql',
            query=query_type,
        )
        yield manager

@pytest.fixture(scope='function', name='federated_schema')
def federated_schema_(federated_manager):
    yield federated_manager.get_schema()


def test_manager_adds_federation_specs(federated_schema):

    assert graphql.print_schema(federated_schema) == """directive @external on FIELD_DEFINITION

directive @requires(fields: _FieldSet!) on FIELD_DEFINITION

directive @provides(fields: _FieldSet!) on FIELD_DEFINITION

directive @key(fields: _FieldSet!) on OBJECT | INTERFACE

directive @extends on OBJECT

type Photo {
  id: ID!
  url: String!
  description: String
}

type Query {
  _entities(representations: [_Any!]!): [_Entity]!
  _service: _Service!
}

type User {
  id: ID!
  photos: [Photo]!
}

scalar _Any

union _Entity = User

scalar _FieldSet

type _Service {
  sdl: String
}
"""


def test_service_sdl(federated_schema):
    assert federated_schema.query_type.fields['_service'].resolve() == {'sdl': SDL}


def test_resolve_reference(federated_manager):
    user_type = FederatedObjectType('User')

    @user_type.resolve_reference
    def resolve_user_reference(representation):
        user_id = representation.get('id')
        return User(id=user_id, photos=[])

    federated_manager.add_types(user_type)
    schema = federated_manager.get_schema()

    assert schema.query_type.fields['_entities'].resolve(
        None, Info(schema=schema), representations=[]
    ) == []
    assert schema.query_type.fields['_entities'].resolve(
        None,
        Info(schema=schema),
        representations=[
            {'__typename': 'User', 'id': 1},
            {'__typename': 'User', 'id': 2},
            {'__typename': 'False', 'id': 3},
        ]
    ) == [
        User(id=1, photos=[]),
        User(id=2, photos=[]),
    ]



def test_resolve_references(federated_manager):
    user_type = FederatedObjectType('User')

    @user_type.resolve_references
    def resolve_user_references(representations):
        return [User(id=r.get('id'), photos=[]) for r in representations]

    federated_manager.add_types(user_type)
    schema = federated_manager.get_schema()

    assert schema.query_type.fields['_entities'].resolve(
        None, Info(schema=schema), representations=[]
    ) == []
    assert schema.query_type.fields['_entities'].resolve(
        None,
        Info(schema=schema),
        representations=[
            {'__typename': 'User', 'id': 1},
            {'__typename': 'User', 'id': 2},
            {'__typename': 'False', 'id': 3},
        ]
    ) == [
        User(id=1, photos=[]),
        User(id=2, photos=[]),
    ]
