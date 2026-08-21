from sqlalchemy import inspect as sa_inspect


def row_to_dict(obj):
    if obj is None:
        return None
    mapper = sa_inspect(obj).mapper
    return {attr.columns[0].name: getattr(obj, attr.key) for attr in mapper.column_attrs}


def rows_to_dicts(objs):
    return [row_to_dict(o) for o in objs]
