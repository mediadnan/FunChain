import unittest

import typing as tp

from funchain.wrapper import (
    NOT_SPECIFIED,
    get_name,
    get_signature,
    pretty_annotation,
    Wrapper,
    funfact,
    chainable
)


class Divisible:
    __doc__ = """divisibility checker for test"""

    def __init__(self, dividend: int):
        self.dividend = dividend

    def __call__(self, arg: int) -> bool:
        return arg % self.dividend == 0


class TestGetFunctionSignature(unittest.TestCase):

    def test_no_annotation(self):
        self.assertEqual((NOT_SPECIFIED, NOT_SPECIFIED), get_signature(lambda x: x))

        def example(a):  ...
        self.assertEqual((NOT_SPECIFIED, NOT_SPECIFIED), get_signature(example))

        def example(a, /):  ...
        self.assertEqual((NOT_SPECIFIED, NOT_SPECIFIED), get_signature(example))

    def test_input_annotation_only(self):
        def example(a: int):  ...
        self.assertEqual((int, NOT_SPECIFIED), get_signature(example))

        def example(a: str):  ...
        self.assertEqual((str, NOT_SPECIFIED), get_signature(example))

        def example(a: tp.Optional[str]):  ...
        self.assertEqual((tp.Optional[str], NOT_SPECIFIED), get_signature(example))

        def example(a: tp.Tuple[str, ...]):  ...
        self.assertEqual((tp.Tuple[str, ...], NOT_SPECIFIED), get_signature(example))

        def example(a: bool):  ...
        self.assertEqual((bool, NOT_SPECIFIED), get_signature(example))

    def test_return_annotation_only(self):
        def example(a) -> int:  ...
        self.assertEqual((NOT_SPECIFIED, int), get_signature(example))

        def example(a) -> None:  ...
        self.assertEqual((NOT_SPECIFIED, None), get_signature(example))

        def example(a) -> tp.Union[bool, None]:  ...
        self.assertEqual((NOT_SPECIFIED, tp.Union[bool, None]), get_signature(example))

    def test_input_output_annotation(self):
        def example(b: bool) -> str: ...
        self.assertEqual((bool, str), get_signature(example))

        def example(b: tp.Tuple[str, str]) -> str: ...
        self.assertEqual((tp.Tuple[str, str], str), get_signature(example))

        self.assertEqual((int, bool), get_signature(Divisible(3)))

    def test_get_input_output_builtins(self):
        builtin_funcs = {
            str,
            int,
            float,
            abs,
            dict,
            list,
            set,
            frozenset,
            tuple,
            callable,
            complex,
            bool,
            zip,
            enumerate,
            round,
            type,
            bytes,
            ord,
            hex,
            hash,
            len,
            next,
            aiter,
            iter,
            id
        }
        for func in builtin_funcs:
            inp_out = get_signature(func)
            self.assertIsInstance(inp_out, tuple, f"{func!r} didn't return a tuple")
            self.assertEqual(2, len(inp_out), f"{func!r} return a tuple with {len(inp_out)} elements")

    def test_allowed_callables(self):
        class Example:
            def __call__(self, *args: int) -> bool: ...
        self.assertEqual((int, bool), get_signature(Example()))

        class Example:
            def __call__(self, arg: int) -> bool: ...
        self.assertEqual((int, bool), get_signature(Example()))

        class Example:
            @classmethod
            def __call__(cls, arg: int) -> bool: ...
        self.assertEqual((int, bool), get_signature(Example()))

        class Example:
            @staticmethod
            def __call__(arg: int) -> bool: ...
        self.assertEqual((int, bool), get_signature(Example()))

    def test_non_chainable_func(self):
        def example(): ...
        with self.assertRaises(ValueError,  msg="func with no args allowed!"):
            get_signature(example)

        def example(a, b): ...
        with self.assertRaises(ValueError,  msg="func with 2 required args allowed!"):
            get_signature(example)

        def example(a, b, c): ...
        with self.assertRaises(ValueError,  msg="func with 3 required args allowed!"):
            get_signature(example)

        def example(*, a=None, b=None): ...
        with self.assertRaises(ValueError,  msg="func with only 2 optional kwargs allowed!"):
            get_signature(example)

        def example(a=None, *, b): ...
        with self.assertRaises(ValueError,  msg="func with optional arg and required kwarg allowed"):
            get_signature(example)

    def test_non_chainable_callables(self):
        class Example:
            def __call__(self) -> tp.Any: ...
        with self.assertRaises(ValueError, msg="callable with no args allowed!"):
            get_signature(Example())

        class Example:
            def __call__(self, a, b) -> tp.Any: ...
        with self.assertRaises(ValueError,  msg="callable with 2 required args allowed!"):
            get_signature(Example())

        class Example:
            def __call__(self, a, b, c) -> tp.Any: ...
        with self.assertRaises(ValueError,  msg="callable with 3 required args allowed!"):
            get_signature(Example())

        class Example:
            def __call__(self, *, a=None, b=None) -> tp.Any: ...
        with self.assertRaises(ValueError,  msg="callable with only 2 optional kwargs allowed!"):
            get_signature(Example())

        class Example:
            def __call__(self, a=None, *, b) -> tp.Any: ...
        with self.assertRaises(ValueError,  msg="callable with optional arg and required kwarg allowed"):
            get_signature(Example())

    def test_return_type_warning(self):
        def example(a: bool) -> None: ...
        with self.assertWarns(UserWarning):
            get_signature(example)


class TestPrettyAnnotation(unittest.TestCase):

    def test_unspecified(self):
        self.assertEqual('?', pretty_annotation(NOT_SPECIFIED))

    def test_unions(self):
        self.assertEqual('str | None', pretty_annotation(tp.Optional[str]))
        self.assertEqual('str | int', pretty_annotation(tp.Union[str, int]))
        self.assertEqual('str | int | bool', pretty_annotation(tp.Union[str, int, bool]))

    def test_callables(self):
        self.assertEqual('(...) -> bool', pretty_annotation(tp.Callable[..., bool]))
        self.assertEqual('() -> bool', pretty_annotation(tp.Callable[[], bool]))
        self.assertEqual('(int, ...) -> bool', pretty_annotation(tp.Callable[[int, ...], bool]))

    def test_generic_types(self):
        self.assertEqual('list', pretty_annotation(tp.List))
        self.assertEqual('list', pretty_annotation(list))
        self.assertEqual('list[str]', pretty_annotation(tp.List[str]))
        self.assertEqual('list[str]', pretty_annotation(list[str]))

        self.assertEqual('tuple', pretty_annotation(tp.Tuple))
        self.assertEqual('tuple', pretty_annotation(tuple))
        self.assertEqual('tuple[str, ...]', pretty_annotation(tp.Tuple[str, ...]))
        self.assertEqual('tuple[str, ...]', pretty_annotation(tuple[str, ...]))

        self.assertEqual('dict', pretty_annotation(tp.Dict))
        self.assertEqual('dict', pretty_annotation(dict))
        self.assertEqual('dict[str, dict[int, set[bool]]]', pretty_annotation(tp.Dict[str, tp.Dict[int, tp.Set[bool]]]))
        self.assertEqual('dict[str, dict[int, set[bool]]]', pretty_annotation(dict[str, dict[int, set[bool]]]))

    def test_special_forms(self):
        self.assertEqual('Any', pretty_annotation(tp.Any))
        self.assertEqual('Iterable', pretty_annotation(tp.Iterable))
        self.assertEqual('Iterator', pretty_annotation(tp.Iterator))
        self.assertEqual('Mapping', pretty_annotation(tp.Mapping))
        self.assertEqual('Generator', pretty_annotation(tp.Generator))
        self.assertEqual('Coroutine', pretty_annotation(tp.Coroutine))


class TestGetName(unittest.TestCase):
    def test_explicit_title(self):
        def func(): ...
        self.assertEqual('abc', get_name(func, 'abc'))
        self.assertEqual('test', get_name(func, 'test'))
        self.assertRaises(TypeError, get_name, func, None)
        self.assertRaises(TypeError, get_name, func, object())
        self.assertRaises(ValueError, get_name, func, '')

    def test_implicit_title_func(self):
        def func(): ...

        def hof():
            def _func(): ...
            return _func

        self.assert_('func' in get_name(func))
        self.assert_('lambda' in get_name(lambda x: x))
        self.assert_('hof' in get_name(hof))

    def test_implicit_title_callable(self):
        class Obj1:
            def __call__(self, *args, **kwargs): ...
        self.assert_('Obj1' in get_name(Obj1()))

    def test_implicit_title_builtins(self):
        self.assert_('float' in get_name(float))
        self.assert_('dict' in get_name(dict))
        self.assert_('abs' in get_name(abs))
        self.assert_('round' in get_name(round))
        self.assert_('callable' in get_name(callable))


class TestChainableDecorator(unittest.TestCase):
    def test_as_wrapper(self):
        def func_(a: int) -> int:
            return 2 * a
        func = chainable(func_)
        self.assertIsInstance(func, Wrapper)
        self.assert_("func_" in func.name)
        self.assertIs(func.default, None)
        self.assertIs(func.function, func_)
        self.assertEqual(10, func(5))

    def test_as_decorator(self):
        @chainable()
        def func(a: int) -> int:
            return 2 * a
        self.assertIsInstance(func, Wrapper)
        self.assert_("func" in func.name)
        self.assertIs(func.default, None)
        self.assertEqual(10, func(5))

    def test_explicit_title_default(self):
        @chainable(title='test')
        def func(a: int) -> int: ...
        self.assertEqual('test', func.name)
        self.assertEqual(None, func.default)

        @chainable(default='test')
        def func(a: int) -> int: ...
        self.assert_('func' in func.name)
        self.assertEqual('test', func.default)

        default = object()
        @chainable(title='test', default=default)
        def func(a: int) -> int: ...
        self.assertEqual('test', func.name)
        self.assertIs(func.default, default)


class TestFunFact(unittest.TestCase):
    def test_for_generator_func(self):
        @funfact
        def generator(*args, **kwargs):
            def func(arg): ...
            return func
        self.assertIsInstance(generator(), Wrapper)
        self.assertEqual(generator.__qualname__, generator().name)
        self.assertEqual(None, generator().default)
        self.assertEqual('test', generator(title='test').name)
        obj = object()
        self.assertEqual(obj, generator(default=obj).default)

    def test_for_generator_class(self):
        @funfact
        class Generator:
            def __init__(*args, **kwargs): ...
            def __call__(self, arg): ...
        self.assertIsInstance(Generator(), Wrapper)
        self.assertEqual(Generator.__qualname__, Generator().name)
        self.assertEqual(None, Generator().default)
        self.assertEqual('test', Generator(title='test').name)
        obj = object()
        self.assertEqual(obj, Generator(default=obj).default)


class TestWrapper(unittest.TestCase):
    def test_refuse_non_callables(self):
        non_callables = (
            None,
            str(),
            int(),
            float(),
            dict(),
            set(),
            list(),
            tuple(),
            object()
        )
        for obj in non_callables:
            self.assertRaises(TypeError, Wrapper, obj, title='test')

    def test_allowed_callables(self):
        def example(a): ...
        Wrapper(example)

        def example(a=None): ...
        Wrapper(example)

        def example(a, b=None, c=None): ...
        Wrapper(example)

        class Example:
            def __call__(self, arg): ...
        Wrapper(Example())

        class Example:
            @staticmethod
            def __call__(arg): ...
        Wrapper(Example())

        class Example:
            @classmethod
            def __call__(cls, arg): ...
        Wrapper(Example())

    def test_docstring(self):
        def function(text: str) -> tp.List[str]:
            """splits by '.'"""
            return text.split('.')
        wrapper = Wrapper(function)
        self.assertEqual("splits by '.'", wrapper.__doc__)


if __name__ == '__main__':
    unittest.main()
