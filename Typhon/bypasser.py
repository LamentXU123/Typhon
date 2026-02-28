import ast
import base64
from .Typhon import logger
from copy import copy, deepcopy
from random import randint, choice
from functools import wraps, reduce
from string import ascii_letters, digits
from typing import Union, List, Optional


def remove_duplicate(List) -> list:
    """
    Remove duplicate items in list
    """
    return list(set(List))


def unescape_double_backslash(string) -> str:
    """
    Unescape double backslashes in a string

    :param string: the string to unescape
    :return: the unescaped string
    """
    return string.replace("\\\\", "\\")


def generate_unicode_char():
    """
    Generate a random Unicode character.

    Returns:
        str: A random Unicode character.
    """
    val = randint(0x4E00, 0x9FBF)
    return chr(val)


def flatten_add_chain(n: ast.AST):
    parts = []

    def collect(x):
        if isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add):
            collect(x.left)
            collect(x.right)
        else:
            parts.append(x)

    collect(n)
    return parts


def replace_redundant_char(string: str) -> str:
    """
    Replace redundant characters in a python repr.
    e.g. 1 + 1 -> 1+1
    """
    return string.replace(" + ", "+").replace(", ", ",").replace(": ", ":")


def general_bypasser(func):
    """
    Decorator for general bypassers.
    """
    func._is_bypasser = True

    @wraps(func)
    def check(self, payload):
        for i in payload[1]:
            if i == func.__name__:
                return None  # Do not do the same bypass
        try:
            return replace_redundant_char(func(self, payload[0]))
        except RecursionError:
            logger.debug(
                f"Bypasser {func.__name__} got recurrence error on {payload[0]}"
            )
            return None

    return check


def bypasser_not_work_with(bypasser_list: List[str]):
    """
    Decorator for bypassers which do not work with any other bypasser in the list.
    """

    def _(func):
        func._is_bypasser = True

        @wraps(func)
        def check(self, payload):
            for i in payload[1]:
                if i == func.__name__:
                    return None  # Do not do the same bypass
            for i in payload[1]:
                for j in bypasser_list:
                    if i == j:
                        return None  # Do not work with this
            try:
                return replace_redundant_char(func(self, payload[0]))
            except RecursionError:
                logger.debug(
                    f"Bypasser {func.__name__} got recurrence error on {payload[0]}"
                )
                return None

        return check

    return _


def recursion_protection(func):
    """
    Decorator for bypassers which may cause recursion error.
    """

    @wraps(func)
    def check(self, payload):
        try:
            output = func(self, payload[0])
            if isinstance(output, str):
                return replace_redundant_char(output)
            else:
                return output
        except RecursionError:
            logger.debug(
                f"Bypasser {func.__name__} got recurrence error on {payload[0]}"
            )
            return payload[0]

    return check


def bypasser_must_work_with(bypasser_list: List[str]):
    """
    Decorator for bypassers which must work with at least one bypasser in the list.
    """

    def _(func):
        func._is_bypasser = True

        @wraps(func)
        def check(self, payload):
            for i in payload[1]:
                if i == func.__name__:
                    return None  # Do not do the same bypass
            success = False
            for j in bypasser_list:
                for k in payload[1]:
                    if k == j:
                        success = True
                        break
                if success:
                    break
            if not success:
                return None  # Do not work without this
            try:
                return replace_redundant_char(func(self, payload[0]))
            except RecursionError:
                logger.debug(
                    f"Bypasser {func.__name__} got recurrence error on {payload[0]}"
                )
                return None

        return check

    return _


class BypassGenerator:
    def __init__(
        self,
        payload: list,
        allow_unicode_bypass: bool,
        local_scope: dict,
        _allow_after_tagging_bypassers: bool = True,
        search_depth: Union[int, None] = None,
    ):
        """
        Initialize the bypass generator with a payload.

        :param payload: The Python expression/statement to be transformed
        :param allow_unicode_bypass: if unicode bypasses are allowed
        :param local_scope: tagged local scope

        The @after_tagging_bypasser note is only here to tell you that
        the bypasser is used after the recursion step.
        """
        from .utils import find_object, is_blacklisted
        from .Typhon import banned_ast_

        self.banned_ast = banned_ast_
        self.find_object = find_object
        self.is_blacklisted = is_blacklisted
        self.payload = payload[0]
        self.tags = payload[1]
        self.allow_unicode_bypass = allow_unicode_bypass
        self.local_scope = local_scope
        self.bypass_methods, self.after_tagging_bypassers = [], []
        self._allow_after_tagging_bypassers = _allow_after_tagging_bypassers
        if self.allow_unicode_bypass:
            charsets = [
                "𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵",
                "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩",
                "𝑎𝑏𝑐𝑑𝑒𝑓𝑔ℎ𝑖𝑗𝑘𝑙𝑚𝑛𝑜𝑝𝑞𝑟𝑠𝑡𝑢𝑣𝑤𝑥𝑦𝑧𝐴𝐵𝐶𝐷𝐸𝐹𝐺𝐻𝐼𝐽𝐾𝐿𝑀𝑁𝑂𝑃𝑄𝑅𝑆𝑇𝑈𝑉𝑊𝑋𝑌𝑍",
                "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡",
            ]
            charset = ""
            init = charsets[0]
            for index, i in enumerate(init):
                if self.is_blacklisted(i):
                    for sets in charsets:
                        subs = sets[index]
                        if not self.is_blacklisted(subs):
                            charset += subs
                            break
                else:
                    charset += i

            self.charset = charset
        if search_depth is None:
            from .Typhon import search_depth
        self.search_depth = search_depth
        for method_name in dir(self):
            method = getattr(self, method_name)
            if callable(method):
                if getattr(method, "_is_bypasser", False):
                    self.bypass_methods.append(method)

    def generate_bypasses(self):
        """
        Generate all possible bypass variants by applying each transformation method.

        Returns:
            list: List of unique transformed payloads
        """
        true_payload = copy(self.payload)
        for i in self.tags:
            true_payload = true_payload.replace(i, self.tags[i])
        if not self.is_blacklisted(true_payload):
            return [true_payload]  # in case of the challenge is so easy
        output = []
        bypassed = [self.payload]

        # Generate combinations of dmultiple bypasses
        combined = self.combine_bypasses(
            [self.payload, []], self.payload, self.search_depth
        )
        bypassed.extend(combined)
        bypassed = remove_duplicate(bypassed)  # Remove duplicates
        # bypassed.sort(key=len)
        for i in bypassed:
            for j in self.tags:
                unicode_tag_found = None
                if self.allow_unicode_bypass:
                    tag_unicode = self.unicode_bypasses(j, self.charset)
                    if tag_unicode in i:
                        unicode_tag_found = tag_unicode
                if (
                    j not in i
                    and not unicode_tag_found
                    and self._allow_after_tagging_bypassers
                ):
                    raise ValueError(f"Tag {j} not found in payload {i}")
                i = i.replace(j, self.tags[j])
                if unicode_tag_found:
                    i = i.replace(tag_unicode, self.tags[j])
            output.append(i)
        output = remove_duplicate(output)
        for i in output:
            if not self.is_blacklisted(i):
                return output  # in case of the challenge is easy
        tmp = copy(output)
        if self._allow_after_tagging_bypassers:
            for i in tmp:
                change_list = self.change_to_bin_hex_oct([i, {}])
                output.extend(change_list)
            for j in output:
                if not self.is_blacklisted(j):
                    return output  # in case of the challenge is easy
            tmp = copy(output)
            for i in tmp:
                if len(i) < 50:
                    if self.find_object(exec, self.local_scope):
                        output.extend(
                            BypassGenerator(
                                [self.repr_to_exec([i, {}]), {}],
                                self.allow_unicode_bypass,
                                self.local_scope,
                                _allow_after_tagging_bypassers=False,
                                search_depth=1,  # This will occupy too much CPU usage, so 1 depth
                            ).generate_bypasses()
                        )
                    if self.find_object(eval, self.local_scope):
                        output.extend(
                            BypassGenerator(
                                [self.repr_to_eval([i, {}]), {}],
                                self.allow_unicode_bypass,
                                self.local_scope,
                                _allow_after_tagging_bypassers=False,
                                search_depth=1,  # This will occupy too much CPU usage, so 1 depth
                            ).generate_bypasses()
                        )
        output = remove_duplicate(output)
        return output

    def combine_bypasses(
        self, payload: List[Union[str, list]], initial_payload: str, depth: int
    ):
        """
        Recursively combine multiple bypass methods for deeper obfuscation.

        Args:
            payload (list): Current list of [payload string, [bypass_method1, bypass_method2, ...]]
            depth (int): Recursion depth limit
            initial_payload (str): Initial payload

        Returns:
            list: Combined transformed payloads
        """
        if depth == 0:
            return [payload[0]]

        variants = []
        for method in self.bypass_methods:
            _ = []
            try:
                new_payload = method(payload)
            except SyntaxError:  # from AST parsing
                logger.debug(
                    f"Bypasser {method.__name__} failed to parse payload: {payload[0]}"
                )
                continue
            if (
                new_payload == payload[0]
                or new_payload is None
                or new_payload in variants
                or new_payload == initial_payload
            ):
                continue
            _ = deepcopy(payload)
            _[1].append(method.__name__)
            variants.append(new_payload)
            variants.extend(
                self.combine_bypasses([new_payload, _[1]], initial_payload, depth - 1)
            )
        return variants

    # @after_tagging_bypasser
    def change_to_bin_hex_oct(self, payload: list) -> list:
        """
        Convert numbers to binary, hex, and oct base.
        """
        return [
            self.numbers_to_binary_base(payload),
            self.numbers_to_hex_base(payload),
            self.numbers_to_oct_base(payload),
        ]

    @general_bypasser
    def encode_string_hex(self, payload):
        """
        Encode strings using hex escapes.
        'A' -> '\\x41'
        """

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str):
                    hex_str = "".join("\\" + f"x{ord(c):02x}" for c in node.value)
                    return ast.Constant(value=hex_str)
                return node

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return unescape_double_backslash(ast.unparse(new_tree))

    @bypasser_not_work_with(["transform_attribute_to_getattr_method"])
    def transform_attribute_to_getattr(self, payload: str) -> str:
        """
        'a.b' -> 'getattr(a, "b")'
        """

        name = self.find_object(getattr, self.local_scope)
        if name is None:
            return payload
        tree = ast.parse(payload, mode="eval")

        class Transformer(ast.NodeTransformer):
            def visit_Attribute(self, node):
                return ast.Call(
                    func=ast.Name(id=name, ctx=ast.Load()),
                    args=[self.visit(node.value), ast.Constant(value=node.attr)],
                    keywords=[],
                )

        transformer = Transformer()
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        return ast.unparse(transformed_tree)

    @general_bypasser
    def switch_quotes(self, payload: str) -> str:
        """
        Change " to ' and ' to "
        """
        output = ""
        for char in payload:
            if char == "'":
                output += '"'
            elif char == '"':
                output += "'"
            else:
                output += char
        return output

    @general_bypasser
    def encode_string_base64(self, payload):
        """
        Encode strings using base64 decoding.

        Args:
            payload (str): Input payload

        Returns:
            str: Transformed payload
        """

        base_64_name = self.find_object(base64, self.local_scope)
        if base_64_name is None:
            return payload

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str):
                    encoded = base64.b64encode(node.value.encode()).decode()
                    return ast.Call(
                        func=ast.Attribute(
                            value=ast.Call(
                                func=ast.Name(
                                    id=base_64_name + ".b64decode", ctx=ast.Load()
                                ),
                                args=[ast.Constant(value=encoded)],
                                keywords=[],
                            ),
                            attr="decode",
                            ctx=ast.Load(),
                        ),
                        args=[],
                        keywords=[],
                    )
                return node

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        return ast.unparse(new_tree)

    # @after_tagging_bypasser
    @recursion_protection
    def numbers_to_binary_base(self, payload: str) -> str:
        """
        Convert numbers to binary base (e.g., 42 → 0b101010).
        """
        placeholder = ""
        while placeholder in payload or placeholder == "":
            placeholder = str(randint(1000000, 9999999))

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, int):
                    return ast.Constant(
                        value=f"0b{placeholder}{bin(node.value)[2:]}{placeholder}"
                    )
                return node

        try:
            tree = ast.parse(payload, mode="eval")
            new_tree = Transformer().visit(tree)
            ast.fix_missing_locations(new_tree)
            return (
                ast.unparse(new_tree)
                .replace(f"'0b{placeholder}", "0b")
                .replace(f"{placeholder}'", "")
            )
        except (SyntaxError, AttributeError):
            return payload

    # @after_tagging_bypasser
    @recursion_protection
    def numbers_to_oct_base(self, payload: str) -> str:
        """
        Convert numbers to oct base.
        """
        placeholder = ""
        while placeholder in payload or placeholder == "":
            placeholder = str(randint(1000000, 9999999))

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, int):
                    return ast.Constant(
                        value=f"0o{placeholder}{oct(node.value)[2:]}{placeholder}"
                    )
                return node

        try:
            tree = ast.parse(payload, mode="eval")
            new_tree = Transformer().visit(tree)
            ast.fix_missing_locations(new_tree)
            return (
                ast.unparse(new_tree)
                .replace(f"'0o{placeholder}", "0o")
                .replace(f"{placeholder}'", "")
            )
        except (SyntaxError, AttributeError):
            return payload

    # @after_tagging_bypasser
    @recursion_protection
    def numbers_to_hex_base(self, payload: str) -> str:
        """
        Convert numbers to hex base.
        """
        placeholder = ""
        while placeholder in payload or placeholder == "":
            placeholder = str(randint(1000000, 9999999))

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, int):
                    return ast.Constant(
                        value=f"0x{placeholder}{hex(node.value)[2:]}{placeholder}"
                    )
                return node

        try:
            tree = ast.parse(payload, mode="eval")
            new_tree = Transformer().visit(tree)
            ast.fix_missing_locations(new_tree)
            return (
                ast.unparse(new_tree)
                .replace(f"'0x{placeholder}", "0x")
                .replace(f"{placeholder}'", "")
            )
        except (SyntaxError, AttributeError):
            return payload

    # deprecated
    # @general_bypasser
    # def obfuscate_func_call(self, payload: str) -> str:
    #     """
    #     Obfuscate function calls using lambda wrappers with support for multiple arguments.
    #     """
    #     from .Typhon import allowed_letters

    #     class Transformer(ast.NodeTransformer):
    #         def visit_Call(self, node):
    #             if isinstance(node.func, ast.Lambda):
    #                 return node
    #             num_args = len(node.args)
    #             try:
    #                 param_names = [
    #                     allowed_letters[i] for i in range(num_args + 1)
    #                 ]  # a, b, c, ...
    #             except IndexError:
    #                 return node  # Too many arguments
    #             lambda_args = [ast.arg(arg=name) for name in param_names]
    #             call_args = [
    #                 ast.Name(id=name, ctx=ast.Load()) for name in param_names[1:]
    #             ]
    #             lambda_func = ast.Lambda(
    #                 args=ast.arguments(
    #                     posonlyargs=[],
    #                     args=lambda_args,
    #                     kwonlyargs=[],
    #                     kw_defaults=[],
    #                     defaults=[],
    #                 ),
    #                 body=ast.Call(
    #                     func=ast.Name(id=param_names[0], ctx=ast.Load()),
    #                     args=call_args,
    #                     keywords=[],
    #                 ),
    #             )
    #             call_args_with_func = [node.func] + node.args

    #             return ast.Call(func=lambda_func, args=call_args_with_func, keywords=[])

    #     tree = ast.parse(payload, mode="eval")
    #     new_tree = Transformer().visit(tree)
    #     ast.fix_missing_locations(new_tree)
    #     return ast.unparse(new_tree)

    @bypasser_not_work_with(["string_reversing"])
    def string_slicing(self, payload: str) -> str:
        """
        Break strings into concatenated parts or use slicing.
        """

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str) and len(node.value) > 1:
                    # Split into character concatenation
                    parts = [ast.Constant(value=c) for c in node.value]
                    new_node = parts[0]
                    for part in parts[1:]:
                        new_node = ast.BinOp(left=new_node, op=ast.Add(), right=part)
                    return new_node
                return node

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    @bypasser_not_work_with(["string_slicing"])
    def string_reversing(self, payload):
        """
        Reverse string.
        """

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str) and len(node.value) > 1:
                    reversed_str = node.value[::-1]
                    slice_node = ast.Subscript(
                        value=ast.Constant(value=reversed_str),
                        slice=ast.Slice(
                            lower=None,
                            upper=None,
                            step=ast.UnaryOp(
                                op=ast.USub(), operand=ast.Constant(value=1)
                            ),
                        ),
                        ctx=ast.Load(),
                    )
                    return slice_node
                return node

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    @general_bypasser
    def list_to_getitem(self, payload: str) -> str:
        """
        list[0] -> list.__getitem__(0)
        """

        class Transformer(ast.NodeTransformer):
            def visit_Subscript(self, node):
                if isinstance(node.slice, ast.Slice):
                    slice_args = [
                        (
                            node.slice.lower
                            if node.slice.lower
                            else ast.Constant(value=None)
                        ),
                        (
                            node.slice.upper
                            if node.slice.upper
                            else ast.Constant(value=None)
                        ),
                    ]
                    slice_call = ast.Call(
                        func=ast.Name(id="slice", ctx=ast.Load()),
                        args=slice_args,
                        keywords=[],
                    )
                    slice_arg = slice_call
                elif isinstance(node.slice, ast.Tuple):
                    dims = []
                    for dim in node.slice.dims:
                        if isinstance(dim, ast.Slice):
                            slice_args = [
                                dim.lower if dim.lower else ast.Constant(value=None),
                                dim.upper if dim.upper else ast.Constant(value=None),
                            ]
                            dims.append(
                                ast.Call(
                                    func=ast.Name(id="slice", ctx=ast.Load()),
                                    args=slice_args,
                                    keywords=[],
                                )
                            )
                        else:
                            dims.append(self.visit(dim))
                    slice_arg = ast.Tuple(elts=dims, ctx=ast.Load())
                else:
                    slice_arg = self.visit(node.slice)
                return ast.Call(
                    func=ast.Attribute(
                        value=self.visit(node.value), attr="__getitem__", ctx=ast.Load()
                    ),
                    args=[slice_arg],
                    keywords=[],
                )

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        ret = ast.unparse(new_tree).replace(", ", ",")
        if "slice(None,None)" in ret:
            return payload
        return ret

    @general_bypasser
    def replace_semicolon_newlines(self, payload: str) -> str:
        """
        Replace semicolons with newlines.

        Note: Might cause bug when replacing ; inside strings (or whatever).
        If yes, please report it and I'll try to fix it (I'm lazyyyyy now).
        PR welcome.
        """
        return payload.replace(";", "\n")

    @bypasser_must_work_with(["string_slicing"])
    def string_to_str_join(self, payload: str) -> str:
        """
        Convert string to string join.
        'a' + 'b' -> ''.join(['a', 'b'])
        """

        def is_str_like(n: ast.AST) -> bool:
            return (
                isinstance(n, ast.Constant) and isinstance(n.value, str)
            ) or isinstance(n, ast.JoinedStr)

        class Transformer(ast.NodeTransformer):
            def visit_BinOp(self, node: ast.BinOp):
                if isinstance(node.op, ast.Add):
                    parts = flatten_add_chain(node)
                    if parts and all(is_str_like(p) for p in parts):
                        return ast.Call(
                            func=ast.Attribute(
                                value=ast.Constant(value=""),
                                attr="join",
                                ctx=ast.Load(),
                            ),
                            args=[ast.List(elts=parts, ctx=ast.Load())],
                            keywords=[],
                        )
                node.left = self.visit(node.left)
                node.right = self.visit(node.right)
                return node

        def _elem_src(n: ast.AST) -> str:
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                return repr(n.value)
            return ast.unparse(n)

        def _is_empty_str_join_call(n: ast.AST) -> bool:
            return (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Constant)
                and n.func.value.value == ""
                and n.func.attr == "join"
                and n.args
                and isinstance(n.args[0], ast.List)
            )

        def emit(n: ast.AST) -> str:
            if _is_empty_str_join_call(n):
                items = ",".join(_elem_src(e) for e in n.args[0].elts)
                return "''.join([" + items + "])"
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                return f"{emit(n.left)} + {emit(n.right)}"
            return ast.unparse(n)

        tree = ast.parse(payload, mode="eval")
        new_body = Transformer().visit(tree.body)
        ast.fix_missing_locations(new_body)
        return emit(new_body)

    @bypasser_must_work_with(["string_slicing"])
    def string_to_chr(self, payload: str) -> str:
        """
        'a'+'b'+'c' -> chr(97)+chr(98)+chr(99)'
        """

        name = self.find_object(chr, self.local_scope)
        if name is None:
            return payload

        def is_single_char_str_const(n: ast.AST) -> bool:
            return (
                isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and len(n.value) == 1
            )

        def rebuild_plus_chain(nodes):
            return reduce(lambda l, r: ast.BinOp(left=l, op=ast.Add(), right=r), nodes)

        def _is_named_list_call(n: ast.AST, name: str) -> bool:
            return (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id == name
                and n.args
                and isinstance(n.args[0], ast.List)
            )

        def _emit_min_list(lst: ast.List) -> str:
            items = []
            for e in lst.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, int):
                    items.append(str(e.value))
                else:
                    items.append(ast.unparse(e))
            return "[" + ",".join(items) + "]"

        def emit_min(n: ast.AST, name: str) -> str:
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                return emit_min(n.left) + "+" + emit_min(n.right)
            if _is_named_list_call(n, name):
                name = n.func.id
                arg0 = n.args[0]  # List
                return f"{name}(" + _emit_min_list(arg0) + ")"
            return ast.unparse(n)

        class Transformer(ast.NodeTransformer):
            def visit_BinOp(self, node: ast.BinOp):
                if isinstance(node.op, ast.Add):
                    parts = flatten_add_chain(node)
                    if parts and all(is_single_char_str_const(p) for p in parts):
                        calls = []
                        for p in parts:
                            code = ord(p.value)
                            call = ast.Call(
                                func=ast.Name(id=name, ctx=ast.Load()),
                                args=[ast.Constant(code)],
                                keywords=[],
                            )
                            calls.append(call)
                        return rebuild_plus_chain(calls)
                node.left = self.visit(node.left)
                node.right = self.visit(node.right)
                return node

        tree = ast.parse(payload, mode="eval")
        new_body = Transformer().visit(tree.body)
        ast.fix_missing_locations(new_body)
        return emit_min(new_body, name)

    @bypasser_must_work_with(["string_slicing"])
    def string_to_bytes_plus(self, payload: str) -> str:
        """
        'a'+'b'+'c' -> bytes([97])+bytes([98])+bytes([99])
        """

        name = self.find_object(bytes, self.local_scope)
        if name is None:
            return payload

        def is_single_char_str_const(n: ast.AST) -> bool:
            return (
                isinstance(n, ast.Constant)
                and isinstance(n.value, str)
                and len(n.value) == 1
            )

        def rebuild_plus_chain(nodes):
            return reduce(lambda l, r: ast.BinOp(left=l, op=ast.Add(), right=r), nodes)

        def _is_named_list_call(n: ast.AST, name: str) -> bool:
            return (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id == name
                and n.args
                and isinstance(n.args[0], ast.List)
            )

        def _emit_min_list(lst: ast.List) -> str:
            items = []
            for e in lst.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, int):
                    items.append(str(e.value))
                else:
                    items.append(ast.unparse(e))
            return "[" + ",".join(items) + "]"

        def emit_min(n: ast.AST, name: str) -> str:
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
                return emit_min(n.left) + "+" + emit_min(n.right)
            if _is_named_list_call(n, name):
                name = n.func.id
                arg0 = n.args[0]  # List
                return f"{name}(" + _emit_min_list(arg0) + ")"
            return ast.unparse(n)

        class Transformer(ast.NodeTransformer):
            def visit_BinOp(self, node: ast.BinOp):
                if isinstance(node.op, ast.Add):
                    parts = flatten_add_chain(node)
                    if parts and all(is_single_char_str_const(p) for p in parts):
                        calls = []
                        for p in parts:
                            code = ord(p.value)
                            call = ast.Call(
                                func=ast.Name(id=name, ctx=ast.Load()),
                                args=[
                                    ast.List(elts=[ast.Constant(code)], ctx=ast.Load())
                                ],
                                keywords=[],
                            )
                            calls.append(call)
                        return rebuild_plus_chain(calls)
                node.left = self.visit(node.left)
                node.right = self.visit(node.right)
                return node

        tree = ast.parse(payload, mode="eval")
        new_body = Transformer().visit(tree.body)
        ast.fix_missing_locations(new_body)
        return emit_min(new_body, name)

    @bypasser_must_work_with(["string_slicing"])
    def string_from_string_dict(self, payload: str) -> str:
        """
        There is a globals dict in Typhon, which contains all the string constants found in the scope.
        e.g. {'b': bytes.__doc__[0]}
        This bypasser replaces string constants with their corresponding values in the globals dict.
        'b' -> bytes.__doc__[0]
        """
        from .Typhon import string_dict

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str) and node.value in string_dict:
                    return ast.Name(id=string_dict[node.value])
                return node

        tree = ast.parse(payload, mode="eval")
        new_body = Transformer().visit(tree.body)
        ast.fix_missing_locations(new_body)
        return ast.unparse(new_body)

    @general_bypasser
    def string_to_bytes_comma(self, payload: str) -> str:
        """
        'abc' -> bytes([97, 98, 99])
        """

        name = self.find_object(bytes, self.local_scope)
        if name is None:
            return payload

        tree = ast.parse(payload)

        class PreservingStringTransformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str):
                    byte_values = [ord(char) for char in node.value]

                    return ast.Call(
                        func=ast.Name(id=name, ctx=ast.Load()),
                        args=[
                            ast.List(
                                elts=[
                                    ast.Constant(value=byte_val)
                                    for byte_val in byte_values
                                ],
                                ctx=ast.Load(),
                            )
                        ],
                        keywords=[],
                    )

                return node

        transformer = PreservingStringTransformer()
        modified_tree = transformer.visit(tree)
        ast.fix_missing_locations(modified_tree)
        return ast.unparse(modified_tree).replace(", ", ",")

    @bypasser_must_work_with(["string_to_bytes_plus", "string_to_bytes_comma"])
    def nested_bytes_decoder(self, payload: str) -> str:
        """
        bytes([97]) -> bytes([97]).decode()
        """
        tree = ast.parse(payload)

        class NestedBytesTransformer(ast.NodeTransformer):
            def visit_Call(self, node):
                node = self.generic_visit(node)

                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "bytes"
                    and len(node.args) == 1
                ):

                    arg = node.args[0]
                    if (
                        isinstance(arg, ast.List)
                        and len(arg.elts) > 0
                        and all(
                            isinstance(elt, ast.Constant) and isinstance(elt.value, int)
                            for elt in arg.elts
                        )
                    ):

                        return ast.Call(
                            func=ast.Attribute(
                                value=node, attr="decode", ctx=ast.Load()
                            ),
                            args=[],
                            keywords=[],
                        )

                return node

        transformer = NestedBytesTransformer()
        modified_tree = transformer.visit(tree)
        ast.fix_missing_locations(modified_tree)

        return ast.unparse(modified_tree)

    def unicode_bypasses(self, payload: str, unicode_charset: str) -> str:
        """
        Bypass unicode encoding and decoding.
        abcdefghijklmnopqrstuvwxyz -> 𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻 (unicode_charset)
        """
        # Create mappings: regular -> unicode
        char_map = {}

        for regular, unicode_char in zip(ascii_letters, unicode_charset):
            char_map[regular] = unicode_char

        class Transformer(ast.NodeTransformer):
            """AST Node Transformer to replace non-string characters with Unicode equivalents"""

            def replace_chars(self, s):
                """Replace characters in a string using the char_map"""
                return "".join([char_map[c] if c in char_map else c for c in s])

            def visit_Name(self, node):
                """Process variable/function names"""
                node.id = self.replace_chars(node.id)
                return self.generic_visit(node)

            def visit_Attribute(self, node):
                """Process attribute names (e.g., object.attribute)"""
                node.attr = self.replace_chars(node.attr)
                return self.generic_visit(node)

            def visit_FunctionDef(self, node):
                """Process function definitions (names only)"""
                node.name = self.replace_chars(node.name)
                return self.generic_visit(node)

            def visit_ClassDef(self, node):
                """Process class definitions (names only)"""
                node.name = self.replace_chars(node.name)
                return self.generic_visit(node)

        tree = ast.parse(payload, mode="eval")
        new_body = Transformer().visit(tree.body)
        ast.fix_missing_locations(new_body)
        return ast.unparse(new_body).replace("__", "_＿")

    @general_bypasser
    def unicode_replace(self, payload: str) -> str:
        if self.allow_unicode_bypass:
            payload = self.unicode_bypasses(payload, self.charset)
        return payload

    # @after_tagging_bypasser
    @recursion_protection
    def repr_to_exec(self, payload: str) -> str:
        """
        wraps the payload with exec()
        __import__('os').system('ls') -> exec("__import__('os').popen('ls').read()")
        """

        name = self.find_object(exec, self.local_scope)
        if name is None:
            return payload
        single_comma = payload.find("'")
        double_comma = payload.find('"')
        if single_comma > double_comma:
            quote = '"'
        elif double_comma > single_comma:
            quote = "'"
        else:
            quote = "'"
        return f"{name}({quote}{payload}{quote})"

    # @after_tagging_bypasser
    @recursion_protection
    def repr_to_eval(self, payload: str) -> str:
        """
        wraps the payload with exec()
        __import__('os').system('ls') -> eval("__import__('os').popen('ls').read()")
        """
        if ";" in payload or "\n" in payload:
            return payload

        name = self.find_object(eval, self.local_scope)
        if name is None:
            return payload
        single_comma = payload.find("'")
        double_comma = payload.find('"')
        if single_comma > double_comma:
            quote = '"'
        elif double_comma > single_comma:
            quote = "'"
        else:
            quote = "'"
        return f"{name}({quote}{payload}{quote})"

    @bypasser_must_work_with(["string_to_str_join"])
    def empty_string_to_str_object(self, payload: str) -> str:
        """
        "".join([]) -> chr().join([])
        """

        string_name = self.find_object(str, self.local_scope)
        if string_name is None:
            return payload

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str) and node.value == "":
                    return ast.Call(
                        func=ast.Name(id=string_name, ctx=ast.Load()),
                        args=[],
                        keywords=[],
                    )
                return node

            def visit_Expr(self, node):
                self.generic_visit(node)
                return node

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    @general_bypasser
    def dict_to_get(self, payload: str) -> str:
        """
        a['b'] -> a.get('b')
        """

        def _const_str_from_slice(slice_node):
            node = slice_node

            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                return node
            return None

        class Transformer(ast.NodeTransformer):
            def visit_Subscript(self, node: ast.Subscript):
                self.generic_visit(node)

                key_const = _const_str_from_slice(node.slice)
                if key_const is None:
                    return node

                return ast.Call(
                    func=ast.Attribute(value=node.value, attr="get", ctx=ast.Load()),
                    args=[key_const],
                    keywords=[],
                )

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    @general_bypasser
    def binop_to_method(self, payload: str) -> str:
        """
        a+b -> a.__add__(b)
        """

        class Transformer(ast.NodeTransformer):
            def visit_BinOp(self, node):
                method_map = {
                    ast.Add: "__add__",
                    ast.Sub: "__sub__",
                    ast.Mult: "__mul__",
                    ast.Div: "__truediv__",
                    ast.FloorDiv: "__floordiv__",
                    ast.Mod: "__mod__",
                    ast.Pow: "__pow__",
                    ast.LShift: "__lshift__",
                    ast.RShift: "__rshift__",
                    ast.BitOr: "__or__",
                    ast.BitXor: "__xor__",
                    ast.BitAnd: "__and__",
                    ast.MatMult: "__matmul__",
                }

                if type(node.op) in method_map:
                    method_name = method_map[type(node.op)]
                    return ast.Call(
                        func=ast.Attribute(
                            value=self.visit(node.left),
                            attr=method_name,
                            ctx=ast.Load(),
                        ),
                        args=[self.visit(node.right)],
                        keywords=[],
                    )

                return self.generic_visit(node)

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    @general_bypasser
    def string_to_dict_list(self, payload: str) -> str:
        """
        'whoami' → list(dict(whoami=1))[0]
        """

        from .Typhon import int_dict

        if int_dict == {}:
            return payload
        else:
            for i in int_dict:
                using_int = int_dict[i]
            if isinstance(using_int, str):
                try:
                    using_int = int(using_int)
                except ValueError:
                    pass

        dictname = self.find_object(dict, self.local_scope)
        if dictname is None:
            return payload
        listname = self.find_object(list, self.local_scope)
        if listname is None:
            return payload

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if not isinstance(node.value, str):
                    return node
                if not node.value:
                    return node
                if " " in node.value:
                    return node
                if any(
                    [
                        i
                        for i in ["-", '"', "'", ".", "/", "\\", ";", "\n"]
                        if i in node.value
                    ]
                ):
                    return node
                if all([i.isdigit() for i in node.value]):
                    return node
                if isinstance(node.value, str):
                    dict_keyword = ast.keyword(
                        arg=node.value, value=ast.Constant(value=using_int)
                    )

                    dict_call = ast.Call(
                        func=ast.Name(id=dictname, ctx=ast.Load()),
                        args=[],
                        keywords=[dict_keyword],
                    )
                    list_call = ast.Call(
                        func=ast.Name(id=listname, ctx=ast.Load()),
                        args=[dict_call],
                        keywords=[],
                    )
                    subscript = ast.Subscript(
                        value=list_call, slice=ast.Constant(value=0), ctx=ast.Load()
                    )

                    return subscript
                return node

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    @general_bypasser
    def empty_string_to_str(self, payload: str):
        """
        '' -> str()
        """
        if not ('""' in payload or "''" in payload):
            return payload
        str_name = self.find_object(str, self.local_scope)
        if str_name is None:
            return payload

        class Transformer(ast.NodeTransformer):
            def visit_Constant(self, node):
                if isinstance(node.value, str) and node.value == "":
                    return ast.Call(
                        func=ast.Name(id=str_name, ctx=ast.Load()),
                        args=[],
                        keywords=[],
                    )
                return node

        tree = ast.parse(payload, mode="eval")
        new_tree = Transformer().visit(tree)
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)

    @bypasser_not_work_with(["transform_attribute_to_getattr"])
    def transform_attribute_to_getattr_method(self, payload: str) -> str:
        """
        'a.b' -> 'a.__getattribute__("b")'
        """
        tree = ast.parse(payload, mode="eval")

        class Transformer(ast.NodeTransformer):
            def visit_Attribute(self, node):
                return ast.Call(
                    func=ast.Attribute(
                        value=self.visit(node.value),
                        attr="__getattribute__",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Constant(value=node.attr)],
                    keywords=[],
                )

        transformer = Transformer()
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        return ast.unparse(transformed_tree)

    @general_bypasser
    def func_add_call(self, payload: str):
        """
        a() -> a.__call__()

        only if less than three functions is called and have a
        length less than 30 characters should this bypasser work.
        """

        class CallCounter(ast.NodeVisitor):
            def __init__(self):
                self.count = 0

            def visit_Call(self, node):
                self.count += 1
                self.generic_visit(node)

        class CallToDunderCallTransformer(ast.NodeTransformer):
            def visit_Call(self, node):
                self.generic_visit(node)

                new_func = ast.Attribute(
                    value=node.func, attr="__call__", ctx=ast.Load()
                )
                new_node = ast.Call(
                    func=new_func, args=node.args, keywords=node.keywords
                )
                return ast.copy_location(new_node, node)

        def transform_expr_if_many_calls(expr_src: str, threshold: int = 3) -> str:
            if len(expr_src) > 30:
                return expr_src

            tree = ast.parse(expr_src, mode="eval")

            counter = CallCounter()
            counter.visit(tree)

            if counter.count >= threshold:
                return ast.unparse(tree)

            transformer = CallToDunderCallTransformer()
            new_tree = transformer.visit(tree)
            ast.fix_missing_locations(new_tree)
            return ast.unparse(new_tree)

        return transform_expr_if_many_calls(payload)


class BashBypassGenerator:
    """
    Bypasser only for RCE bash commands.
    'cat /flag' -> 'cat$IFS$9/flag'
    """

    def blank_to_ifs_index(self, payload: str) -> str:
        """
        ' ' -> $IFS$9
        """
        return payload.replace(" ", "$IFS$9")

    def black_to_ifs_blanket(self, payload: str) -> str:
        """
        'cat /flag' -> 'cat${IFS}/flag'
        """
        return payload.replace(" ", "${IFS}")

    # the below are modified from program bashfuck
    # https://github.com/ProbiusOfficial/bashFuck
    # Copyright @ ProbiusOfficial, 2025

    def get_oct(
        self, c
    ):  # 将字符的ASCII值转换为二进制字符串，然后将其转换为八进制，去掉前缀“0o”
        return (oct(ord(c)))[2:]

    def nomal_otc(self, cmd):  # 注意,该方法无法执行带参数命令,如:ls -l
        if " " not in cmd:
            payload = ""
            for c in cmd:
                payload += "\\" + self.get_oct(c)
            return payload
        # else return None in this func

    def common_otc(self, cmd):
        payload = ""
        for c in cmd:
            if c == " ":
                payload += " "
            else:
                payload += "\\" + self.get_oct(c)
        payload += ""
        return payload

    def bashfuck_x(self, cmd, form):
        bash_str = ""
        for c in cmd:
            bash_str += f"\\\\$(($((1<<1))#{bin(int(self.get_oct(c)))[2:]}))"
        payload_bit = bash_str
        payload_zero = bash_str.replace("1", "${##}")  # 用 ${##} 来替换 1
        payload_c = bash_str.replace("1", "${##}").replace(
            "0", "${#}"
        )  # 用 ${#} 来替换 0
        if form == "bit":
            payload_bit = "$0<<<$0\\<\\<\\<\\$\\'" + payload_bit + "\\'"
            return payload_bit
        elif form == "zero":
            payload_zero = "$0<<<$0\\<\\<\\<\\$\\'" + payload_zero + "\\'"
            return payload_zero
        elif form == "c":
            payload_c = "${!#}<<<${!#}\\<\\<\\<\\$\\'" + payload_c + "\\'"
            return payload_c

    def bashfuck_y(self, cmd):
        oct_list = [  # 构造数字 0-7 以便于后续八进制形式的构造
            "$(())",  # 0
            "$((~$(($((~$(())))$((~$(())))))))",  # 1
            "$((~$(($((~$(())))$((~$(())))$((~$(())))))))",  # 2
            "$((~$(($((~$(())))$((~$(())))$((~$(())))$((~$(())))))))",  # 3
            "$((~$(($((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))))))",  # 4
            "$((~$(($((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))))))",  # 5
            "$((~$(($((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))))))",  # 6
            "$((~$(($((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))$((~$(())))))))",  # 7
        ]
        bashFuck = ""
        bashFuck += "__=$(())"  # set __ to 0
        bashFuck += "&&"  # splicing
        bashFuck += "${!__}<<<${!__}\\<\\<\\<\\$\\'"  # got 'sh'

        for c in cmd:
            bashFuck += "\\\\"
            for i in self.get_oct(c):
                bashFuck += oct_list[int(i)]

        bashFuck += "\\'"

        return bashFuck

    def interactive(self):
        from .Typhon import interactive_

        if interactive_:
            return "$0"
        else:
            return None

    def Generate(self, cmd):
        yield cmd
        yield self.interactive()
        yield self.nomal_otc(cmd)
        yield self.blank_to_ifs_index(cmd)
        yield self.black_to_ifs_blanket(cmd)
        yield self.common_otc(cmd)
        # yield self.bashfuck_x(cmd, 'bit')
        # yield self.bashfuck_x(cmd, 'zero')
        # yield self.bashfuck_x(cmd, 'c')
        # yield self.bashfuck_y(cmd)
