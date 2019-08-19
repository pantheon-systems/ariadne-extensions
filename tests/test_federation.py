from unittest.mock import MagicMock, patch
from io import StringIO

import graphql
from ariadne import QueryType#, ObjectType

from ariadne_extensions.federation import FederatedManager#, FederatedObjectType



def test_manager_adds_federation_specs():
    query_type = QueryType()

    sdl = StringIO("""
    type User @key(fields: "id") @extends {
        id: ID! @external
        photos: [Photo]!
    }

    type Photo {
        id: ID!
        url: String!
        description: String
    }

    """)

    mock_open = MagicMock(return_value=sdl)
    with patch('builtins.open', mock_open):
        manager = FederatedManager(
            schema_sdl_file=sdl,
            query=query_type,
        )

        schema = manager.get_schema()

        assert graphql.print_schema(schema) == """directive @external on FIELD_DEFINITION

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
