import re
import sys
import inspect
import builtins

from .bypasser import *
from string import ascii_letters, digits
from types import FunctionType, ModuleType

prefix = ("USER_DEFINED_", "MODULE_", "EXCEPTION_", "BUILTINS_", "FILECONTENTS")
fixed_tag = [
    "BUILTINS_SET",
    "BUILTINS_SET_CHANGED",
    "UNKNOWN",
    "TYPE",
    "OBJECT",
    "GENERATOR",
    "EXCEPTION",
]


def get_name_and_object_from_tag(tag: str, tagged_scope: dict):
    """
    Get the name and object from a tag.

    :param tag: The tag to analyze
    :return: A tuple with the name and object
    """
    output = []
    for i in tagged_scope:
        if tagged_scope[i][1] == tag:
            output.append((i, tagged_scope[i][0]))
    return output


def find_object(object: object, tagged_scope: dict):
    """
    Find an object in a tagged scope.

    :param object: The object to find
    :param tagged_scope: The tagged scope to search in
    :return: name of the object, None if not found
    """
    from .Typhon import original_scope

    for i in tagged_scope:
        if eval(i, original_scope) == object:
            return i

    return None


def exec_with_returns(code: str, scope: dict):
    """
    Execute a code string with a given scope and return the value of
    the last expression.

    :param code: The code to execute
    :param scope: The scope to use for execution
    :return: The returned value of the code
    """
    scope["__return__"] = None
    lines = code.split("\n")
    if not lines:
        return None
    last_line = lines[-1]
    if ";" in last_line:
        statements = last_line.split(";")
        last_statement = statements[-1].strip()
        statements[-1] = f"__return__ = {last_statement}"
        lines[-1] = ";".join(statements)
    else:
        lines[-1] = f"__return__ = {last_line}"
    modified_code = "\n".join(lines)
    try:
        exec(modified_code, scope)
        return scope.get("__return__")
    except Exception as e:
        logger.debug(f"Error executing code when testing payload {code}: {e}")
        return None


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Merge dicts. Not using | for backwards compatibility.
    """
    if type(dict1) != dict:
        return dict2
    if type(dict2) != dict:
        return dict1
    return {**dict1, **dict2}


def tag_variables(variables, change_in_builtins) -> list:
    """
    Tag each item in a variable namespace according to its type

    :param variables: The variable namespace to analyze (typically globals() or locals())
    :param change_in_builtins: The list of var changed included in __builtins__
    :return: Dictionary with tagging information
    """
    tagged = {}
    builtins_set = set(dir(builtins))

    for name, obj in variables.items():
        if obj == object:
            tagged[name] = "OBJECT"
            continue
        if obj == type:
            tagged[name] = "TYPE"
            continue
        if obj.__class__ == (a for a in ()).__class__:
            tagged[name] = "GENERATOR"
            continue
        if obj == bytes:
            tagged[name] = "BYTES"
            continue
        # Check if it's a builtin object
        if name in builtins_set:
            tagged[name] = f"BUILTINS_{name}"
            continue
        if isinstance(obj, dict) and set(obj.keys()) == set(dir(builtins)):
            if change_in_builtins:
                tagged[name] = "BUILTINS_SET_CHANGED"
            else:
                tagged[name] = "BUILTINS_SET"
            # Actually, BUILTINS_SET should be BUILTINS_DICT......
            # But fuck it, no one cares.
            continue
        # Check if it's a user-defined function
        if isinstance(obj, FunctionType) and obj.__module__ != "builtins":
            # Check if it's a lambda function
            if obj.__name__ == "<lambda>":
                tagged[name] = "USER_DEFINED_LAMBDA"
            else:
                tagged[name] = "USER_DEFINED_FUNCTION"
            continue
        # Check if it's a module
        if isinstance(obj, ModuleType):
            tagged[name] = "MODULE_{}".format(obj.__name__.upper())
            continue
        # Check if it's an exception
        if obj == Exception:
            tagged[name] = "EXCEPTION"
        if issubclass(obj.__class__, BaseException):
            tagged[name] = "EXCEPTION_{}".format(obj.__name__.upper())
            continue
        # Check if it's a class
        if inspect.isclass(obj):
            tagged[name] = "USER_DEFINED_CLASS"
            continue
        # Check for user-defined variables
        try:
            if hasattr(obj, "__name__"):
                obj_name = obj.__name__
            elif hasattr(obj, "__class__"):
                obj_name = obj.__class__.__name__
            else:
                obj_name = str(obj)
            # Sanitize object name (keep only alphanumeric, replace others with _)
            obj_name = "".join(c if c.isalnum() else "_" for c in obj_name).upper()
            tagged[name] = "USER_DEFINED_{}".format(obj_name)
        except:
            tagged[name] = "UNKNOWN"  # If we can't tag it, it's unknown
    return tagged


def tag_scope(scope: dict, change_in_builtins: int) -> dict:
    """
    Tag each item in a scope (e.g. globals(), locals()) according to its type

    :param scope: The scope to analyze
    :param change_in_builtins: The list of var changed included in __builtins__
    :return: Dictionary with tagging information
    """
    return {
        k: [v, tag_variables({k: v}, change_in_builtins)[k]] for k, v in scope.items()
    }


def is_tag(string: str) -> bool:
    """
    Check if a string is a valid tag

    :param string: The string to check
    :return: True if the string is a valid tag, False otherwise
    """
    return string.startswith(prefix) or string in fixed_tag


def parse_payload_list(
    payload: List[list],
    char_blacklist: List[str],
    allow_unicode_bypass: bool,
    local_scope: dict,
    cmd=Union[str, None],
    bash_cmd=Union[str, None],
) -> list:
    """
    Parse a list of payloads (parse tags)

    :param payload: the payload to parse
    :param char_blacklist: the list of banned characters
    :param allow_unicode_bypass: if unicode bypasses are allowed.
    :param local_scope: the local scope to use for tag analysis
    :param cmd: the final RCE command to execute, default None
    :return: filtered list of payloads, with its tags e.g. ['TYPE.__base__', {'TYPE': 'int.__class__'}]
    """
    from .Typhon import generated_path, allowed_letters, allowed_int, find_object

    output = []
    allowed_builtin_obj = [
        i for i in ["[]", "()", "{}", "''", '""'] if i not in char_blacklist
    ]  # list, tuple, dict, string
    allowed_objects = [
        i
        for i in local_scope
        if local_scope[i][0].__class__ == type and i not in char_blacklist
    ]
    allowed_objects.sort(key=len)
    # builtin_obj.extend(allowed_digits)  # This line is only here to tell you that
    # digits do not work in some cases (like 1.__class__)

    for path in payload:
        tags = path[1]
        payload = path[0]
        if cmd:
            if "COMMAND" in payload:
                if bash_cmd:
                    payload = payload.replace("COMMAND", f"'{bash_cmd}'")
                else:
                    payload = payload.replace("COMMAND", f"'{cmd}'")
            if "CMD_FILE" in payload:
                payload = payload.replace(
                    "CMD_FILE", "'/bin/" + cmd.split(" ")[0] + "'"
                )
            if "UNFOLD_CMD_ARGS" in payload:
                if " " not in cmd:
                    payload = payload.replace("UNFOLD_CMD_ARGS", f"'{cmd}'")
                payload = payload.replace(
                    "UNFOLD_CMD_ARGS",
                    ",".join(["'" + i + "'" for i in cmd.split(" ")]),
                )
        if "RANDOMVARNAME" in payload:
            if allowed_letters:
                payload = payload.replace("RANDOMVARNAME", allowed_letters[0])
            # unicode bypass
            if allow_unicode_bypass:
                payload = payload.replace("RANDOMVARNAME", generate_unicode_char())
        if "RANDOMSTRING" in payload:
            if allowed_letters:
                payload = payload.replace(
                    "RANDOMSTRING", "'" + allowed_letters[0] + "'"
                )
            # unicode bypass
            if allow_unicode_bypass:
                payload = payload.replace(
                    "RANDOMSTRING", "'" + generate_unicode_char() + "'"
                )
        if "BUILTINOBJ" in payload:  # TODO
            # note: we assume that OBJ tag is in the beginning of the payload
            obj = payload.split(".")[0] + "." + payload.split(".")[1]
            if allowed_builtin_obj:
                payload = payload.replace("BUILTINOBJ", choice(allowed_builtin_obj))
            else:
                continue
        if "RANDOMINT" in payload:
            if allowed_int:
                payload = payload.replace("RANDOMINT", allowed_int[0])
            else:
                continue
        if "TRUE" in payload:
            for i in allowed_int:
                if eval(i).__bool__():
                    payload = payload.replace("TRUE", i)
            name = find_object(True, local_scope)
            if name:
                payload = payload.replace("TRUE", name)
            if "TRUE" in payload:
                continue
        if "BUILTINtype" in payload:
            if allowed_objects:
                tags["BUILTINtype"] = allowed_objects[0]
            else:
                continue
        if "GENERATOR" in payload:
            if "GENERATOR" in generated_path:
                tags["GENERATOR"] = generated_path["GENERATOR"]
            else:
                continue
        if "TYPE" in payload:
            if "TYPE" in generated_path:
                tags["TYPE"] = generated_path["TYPE"]
            else:
                continue
        if "OBJECT" in payload:
            if "OBJECT" in generated_path:
                tags["OBJECT"] = generated_path["OBJECT"]
            else:
                continue
        if "BUILTINS_SET" in payload:
            if "BUILTINS_SET" in generated_path:
                tags["BUILTINS_SET"] = generated_path["BUILTINS_SET"]
            else:
                continue
        if "MODULE_BUILTINS" in payload:
            if "MODULE_BUILTINS" in generated_path:
                tags["MODULE_BUILTINS"] = generated_path["MODULE_BUILTINS"]
            else:
                continue
        if len(path) == 3:
            output.append([payload, tags, path[2]])
        else:
            output.append([payload, tags])

    return output


def filter_path_list(path_list: list, tagged_scope: dict) -> List[list]:
    """
    return a filtered list of payloads based on the scope

    :param path_list: list of payloads to filter
    :param scope: the scope to filter by
    :return: filtered list of payloads, with its tags e.g. ['TYPE.__base__', {'TYPE': 'int.__class__'}]
    """

    def check_need(
        path: Union[str, list], tagged_scope: dict, need: str
    ) -> Union[str, None]:
        """
        Check if a path needs something in the scope

        :param path: the path to check
        :param scope: the scope to check in
        :return: the payload if the need is met, None otherwise
        """
        if isinstance(path, list):
            tags = path[1]
            path = path[0]
        else:
            tags = {}
        if need in sys.modules:  # need is a module
            need_module = sys.modules[need]
            module_dict = get_module_from_tagged_scope(tagged_scope)
            if need_module in module_dict.values():
                tags[need] = get_name_and_object_from_tag(
                    "MODULE_" + need.upper(), tagged_scope
                )[0][
                    0
                ]  # The module is already imported, we don't need to import it again
                return [path, tags]
            # TODO: check if module is already imported, if not, check if we can import modules
        elif need in dir(builtins):  # need is a builtin
            need_obj = __builtins__[need]
            output = []
            for i in tagged_scope:
                if tagged_scope[i][0] == need_obj:
                    output.append(i)
            if output:
                output.sort(key=len)
                return [path.replace(need, output[0]), tags]
            else:
                for i in tagged_scope:
                    if tagged_scope[i][1] == "BUILTINS_SET":
                        tags[need] = i + f"['{need}']"
                        return [path, tags]
                    if tagged_scope[i][1] == "MODULE_BUILTINS":
                        tags[need] = i + f".{need}"
                        return [path, tags]
        elif is_tag(need):  # need is a tag
            for i in tagged_scope:
                if tagged_scope[i][1] == need:
                    if need in path:
                        tags[need] = i
                    return [path, tags]
        else:  # need is a path
            pass  # TODO
        return None

    filtered_list = []
    for pathlist in path_list:
        path, need = pathlist[0], pathlist[1]
        try:
            reminder = pathlist[2]
        except IndexError:
            reminder = ""
        if need:  # we need something in this path
            if "," in need:  # we need multiple things in this path
                need = need.split(",")
                for i in need:
                    path = check_need(path, tagged_scope, i)
                    if path is None:
                        break
                if path:
                    if reminder != "":
                        path.append(reminder)
                    filtered_list.append(path)
            elif "|" in need:  # we need one of the things in this path
                need = need.split("|")
                for i in need:
                    path_ = check_need(path, tagged_scope, i)
                    if path_:
                        if reminder != "":
                            path_.append(reminder)
                        filtered_list.append(path_)
                        break
            else:  # we need one thing in this path
                path = check_need(path, tagged_scope, need)
                if path:
                    if reminder != "":
                        path.append(reminder)
                    filtered_list.append(path)
        else:  # we don't need anything in this path
            if reminder == "":
                filtered_list.append([path, {}])
            else:
                filtered_list.append([path, {}, reminder])

    return filtered_list


def is_blacklisted(payload, ast_check_enabled=True) -> bool:
    """
    Check if a payload is blacklisted

    :param payload: the payload to check
    :param ast_check_enabled: if the AST check is enabled
    :return: True if the payload is blacklisted, False otherwise
    """
    from .Typhon import banned_ast_, banned_chr_, banned_re_, max_length_, allowed_chr_

    ast_banned = False
    re_banned = False
    if max_length_ == None:
        length_check = False
        max_length = 0
    else:
        length_check = True
        max_length = max_length_
    if ast_check_enabled:
        try:
            ast_nodes = ast.walk(ast.parse(payload))
            for bAST in banned_ast_:
                if any(isinstance(node, bAST) for node in ast_nodes):
                    ast_banned = True
                    break
        except (SyntaxError, TypeError) as e:
            from .Typhon import logger

            logger.debug("Syntax error in payload when testing for AST: " + payload + ' ' + str(e))
            ast_banned = True
    if banned_re_:
        for b_re in banned_re_:
            if re.search(b_re, payload):
                re_banned = True
                break
    return (
        any(i in payload for i in banned_chr_)  # banned character check
        or (
            allowed_chr_ != [] and not all(i in allowed_chr_ for i in payload)
        )  # allowed character check
        or ast_banned  # AST check
        or re_banned  # regex check
        or (len(payload) > max_length and length_check)
    )  # max length check


def try_bypasses(
    pathlist,
    banned_chars,
    banned_AST,
    banned_re,
    max_length,
    allow_unicode_bypass,
    local_scope,
    cmd=None,
    bash_cmd=None,
    stop_after_first: bool = False,
) -> list:
    """
    Try to bypass each payload in the pathlist

    :param pathlist: list of payloads to try to bypass
    :param banned_chars: list of banned chars
    :param banned_AST: list of banned AST
    :param banned_re: banned regex
    :param max_length: max length of the payload
    :param allow_unicode_bypass: if unicode bypasses are allowed.
    :param local_scope: the local scope to use for tag analysis
    :param cmd: command to RCE (in the final step, otherwise None)
    :return: list of successful payloads
    """
    successful_payloads = []
    successful_payloads_with_reminder = []
    pathlist = parse_payload_list(
        pathlist, banned_chars, allow_unicode_bypass, local_scope, cmd, bash_cmd
    )
    Total = len(pathlist)
    for i, path in enumerate(pathlist):
        progress_bar(i + 1, Total)
        for _ in BypassGenerator(
            path, allow_unicode_bypass=allow_unicode_bypass, local_scope=local_scope
        ).generate_bypasses():
            if not is_blacklisted(_):
                if len(path) == 3:
                    from .Typhon import reminder

                    remind = path[2].replace("{}", _)
                    reminder[_] = remind
                    successful_payloads_with_reminder.append(_)
                else:
                    successful_payloads.append(_)
                if stop_after_first:
                    if pathlist:
                        sys.stdout.write("\n")
                    return [_]
    if pathlist:
        sys.stdout.write("\n")
    successful_payloads.sort(key=len)
    successful_payloads_with_reminder.sort(key=len)
    successful_payloads.extend(successful_payloads_with_reminder)

    return successful_payloads


def progress_bar(current, total, bar_length=60):
    """
    Progress bar function

    Note: sometime this may cause gliches in your console (somehow, idk).
    That's bad, but I don't want to rely on `tqdm` just for this simple feature.

    Not avaliable in debug mode. In debug mode, `total` is force to 0
    """
    if total == 0:
        return
    percent = float(current) * 100 / total
    arrow = "=" * int(percent / 100 * bar_length - 1) + ">"
    spaces = " " * (bar_length - len(arrow))

    sys.stdout.write(
        f"\rBypassing ({current}/{total}): [{arrow + spaces}] {percent:.1f}%"
    )
    sys.stdout.flush()


def bypasses_output(
    bypassed_payload: Union[str, list] = None, generated_path: list = []
):
    """
    Print a fancy output of the bypassed payload
    if bypassed_payload is set, it means we RCE successfully, the program ends.
    if generated_path is set, it means we have some progress but not RCE,
    the program ends with the those progress.

    :param bypassed_payload: the bypassed payload, if it's a list, it means we have
    to print all the generated payloads
    :param generated_path: the generated path
    :return: None
    """
    from .Typhon import achivements, reminder, log_level_

    if log_level_ == "CRITICAL":
        sys.stdout = sys.__stdout__
    print("\n")
    bypassed_path, printed_reminder = [], []
    if isinstance(bypassed_payload, str):
        bypassed_payload = [bypassed_payload]
    if not bypassed_payload is None:
        bypassed_path.extend(bypassed_payload)
    bypassed_path.extend(achivements.values())
    for i in bypassed_path:
        if isinstance(i, list):
            i = i[0]
        if i is None:
            continue
        for j in reminder:
            if j in i and j not in printed_reminder:
                printed_reminder.append(j)
                print("\033[33mWARNING [!] " + reminder[j] + "\033[0m")
    print("\n")
    print("-----------Progress-----------")
    print("\n")
    for i in achivements:
        payload_len = achivements[i][1]
        if payload_len > 1:
            print(
                "\033[34m" + i + "(" + str(payload_len) + " payloads found): \033[0m",
                end="",
            )
        else:  # only one payload or no payload found
            print(
                "\033[34m" + i + "(" + str(payload_len) + " payload found): \033[0m",
                end="",
            )
        best_payload = str(achivements[i][0])
        if "\n" in best_payload:
            print("\n" + best_payload)
        else:
            print(best_payload)
    print("\n")
    print("-----------Progress-----------")
    print("\n")
    if bypassed_payload:
        print("\033[36m+++++++++++Jail broken+++++++++++\033[0m")
        print("\n")
        for i in bypassed_payload:
            print(i)
            for j in reminder:
                if j in i:
                    print("\033[33mReminder: " + reminder[j] + "\033[0m")
            print("")
        print("")
        print("\033[36m+++++++++++Jail broken+++++++++++\033[0m")
        exit(0)
    if generated_path:
        return generated_path


def get_module_from_tagged_scope(tagged_scope: dict) -> dict:
    """
    Get the module from the tagged scope

    :param tagged_scope: the tagged scope
    :return: the module from the tagged scope
    e.g.: {'os': <module 'os' (built-in)>}
    """
    module_dict = {}
    for i in tagged_scope:
        if "MODULE_" in tagged_scope[i][1]:
            module_name = tagged_scope[i][1].split("_")[1].lower()
            module_dict[module_name] = tagged_scope[i][0]
    return module_dict
