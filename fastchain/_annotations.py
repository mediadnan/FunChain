import typing as tp
import types
from sys import version_info


NOT_SPECIFIED = object()

_special_form = getattr(tp, '_SpecialForm')
_generic_types = getattr(tp, '_GenericAlias')

if version_info.minor >= 9:
    _generic_types = _generic_types, getattr(types, 'GenericAlias')
    _special_form = _special_form, getattr(tp, '_SpecialGenericAlias')


def pretty_annotation(obj, sep: str = ', ') -> str:
    """prettifies annotations"""
    if obj is NOT_SPECIFIED:
        return '?'

    elif isinstance(obj, _special_form):
        origin = tp.get_origin(obj)
        if origin is None:
            return getattr(obj, '_name')
        return pretty_annotation(origin)

    elif obj is Ellipsis:
        return '...'

    elif isinstance(obj, (list, tuple)):
        return sep.join(map(pretty_annotation, obj))

    elif type(None) is obj:
        return repr(None)

    elif isinstance(obj, _generic_types):
        origin = tp.get_origin(obj)
        args = tp.get_args(obj)
        name = getattr(origin, '_name', getattr(origin, '__name__', None))

        if name in {'Union', 'Optional'}:
            return pretty_annotation(args, ' | ')

        elif name == 'Callable':
            return f'({pretty_annotation(args[0])}) -> {pretty_annotation(args[1])}'

        elif args:
            return f'{pretty_annotation(origin)}[{pretty_annotation(args)}]'

        return pretty_annotation(origin)

    elif isinstance(obj, tp.ForwardRef):
        return pretty_annotation(eval(getattr(obj, '__forward_arg__')))

    elif isinstance(obj, type):
        return getattr(obj, '__name__')

    return str(obj)
