from drf_spectacular.utils import extend_schema, extend_schema_view


def tagged_viewset_schema(tag: str, extra: set = set()):
    actions = {"list", "retrieve", "create", "update", "partial_update", "destroy"}
    schema_kwargs = {
        action: extend_schema(tags=[tag])
        for action in actions.union(extra)
    }
    return extend_schema_view(**schema_kwargs)