from drf_spectacular.utils import extend_schema, extend_schema_view


def tagged_viewset_schema(tag: str, extra: set | None = None):
    actions = ["list", "retrieve", "create", "update", "partial_update", "destroy"]
    if extra:
        for i in extra:
            actions.append(i)
    schema_kwargs = {action: extend_schema(tags=[tag]) for action in actions}
    return extend_schema_view(**schema_kwargs)