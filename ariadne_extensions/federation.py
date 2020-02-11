# pylint: disable=line-too-long, too-many-arguments
import functools
from inspect import signature
from collections import defaultdict

from graphql import ObjectTypeDefinitionNode, parse

from ariadne import ObjectType, UnionType, make_executable_schema


FEDERATION_SPECS_TEMPLATE = """
directive @external on FIELD_DEFINITION
directive @requires(fields: _FieldSet!) on FIELD_DEFINITION
directive @provides(fields: _FieldSet!) on FIELD_DEFINITION
directive @key(fields: _FieldSet!) on OBJECT | INTERFACE
directive @extends on OBJECT

scalar _Any
scalar _FieldSet

# a union of all types that use the @key directive
{entity_union}

{extend_type}type Query {{
  {entity_query}
  _service: _Service!
}}

type _Service {{
    sdl: String
}}
"""


def _convert_resolver(func):
    """Registered resolve_reference function should take obj and info objects.
    This handles old function and converts them to a new signature, if needed."""
    sig = signature(func).parameters
    if "obj" in sig and "info" in sig:
        return func

    @functools.wraps(func)
    def wrapper(representation, obj=None, info=None):
        return func(representation)

    return wrapper


class FederatedObjectType(ObjectType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reference_resolver = None

    def resolve_reference(self, resolver):
        resolver = _convert_resolver(resolver)

        @functools.wraps(resolver)
        def wrapper(params, obj, info):
            return [resolver(p, obj=obj, info=info) for p in params]

        self._reference_resolver = wrapper
        return resolver

    def resolve_references(self, resolver):
        resolver = _convert_resolver(resolver)
        self._reference_resolver = resolver
        return resolver

    def bind_to_schema(self, schema):
        super().bind_to_schema(schema)
        if self._reference_resolver:
            graphql_type = schema.type_map.get(self.name)
            graphql_type.reference_resolver = self._reference_resolver


class FederatedManager:
    def __init__(self, schema_sdl_file, query):

        self.sdl = open(schema_sdl_file).read()
        self.ast_schema = parse(self.sdl)

        self.query = query
        self.types = [query]

        self.federated_types = self._get_federated_types()

    def add_types(self, *types):
        self.types += types

    def get_schema(self):
        self.query.field("_service")(self._query_service_resolver)
        if self.federated_types:
            entity_type = UnionType("_Entity")
            self.types.append(entity_type)

            entity_type.type_resolver(self._entity_type_resolver)
            self.query.field("_entities")(self._entities_resolver)

        return make_executable_schema(self._get_federated_sdl(), self.types)

    def _get_federated_types(self):
        federated_types = []
        for definition in self.ast_schema.definitions:
            if not isinstance(definition, ObjectTypeDefinitionNode):
                continue
            for directive in definition.directives:
                if directive.name.value == "key":
                    federated_types.append(definition.name.value)
        return federated_types

    def _has_query_type(self):
        for definition in self.ast_schema.definitions:
            if (
                isinstance(definition, ObjectTypeDefinitionNode)
                and definition.name.value == "Query"
            ):
                return True
        return False

    def _get_federated_sdl(self):
        if self.federated_types:
            federation_specs = FEDERATION_SPECS_TEMPLATE.format(
                entity_query="_entities(representations: [_Any!]!): [_Entity]!",
                extend_type="extend " if self._has_query_type() else "",
                entity_union="union _Entity = {0}".format(
                    " | ".join(self.federated_types)
                ),
            )
        else:
            federation_specs = FEDERATION_SPECS_TEMPLATE.format(
                entity_query="",
                extend_type="extend " if self._has_query_type() else "",
                entity_union="",
            )

        return f"""
            {federation_specs}
            {self.sdl}
        """

    def _entity_type_resolver(self, obj, *_):
        if hasattr(obj, "AriadneMeta") and hasattr(obj.AriadneMeta, "entity_name"):
            return obj.AriadneMeta.entity_name
        return obj.__class__.__name__

    def _entities_resolver(self, obj, info, representations):
        type_ids = defaultdict(list)
        ret = []

        for representation in representations:
            type_name = representation.pop("__typename")
            type_ids[type_name].append(representation)

        for type_name, params in type_ids.items():
            graphql_type = info.schema.type_map.get(type_name)
            reference_resolver = getattr(graphql_type, "reference_resolver", None)
            if reference_resolver:
                ret += reference_resolver(params, obj=obj, info=info)

        return ret

    def _query_service_resolver(self, *_):
        return {"sdl": self.sdl}
