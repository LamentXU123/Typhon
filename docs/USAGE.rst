USAGE 用户指南
===============

此页为 ``Typhon`` 项目的使用说明。

.. toctree::
    :maxdepth: 2

绕过函数
--------

``Typhon`` 安装完成后，您可以使用如下终点函数进行绕过：

.. py:function:: bypassRCE(cmd, local_scope: dict = None, banned_chr: list = [], allowed_chr: list = [], banned_ast: list = [], banned_re: list = [],max_length: int = None,allow_unicode_bypass: bool = False, print_all_payload: bool = False,interactive: bool = True,depth: int = 5,recursion_limit: int = 200,log_level: str = "INFO",)

    .. py:attribute:: cmd

        要执行的Linux shell命令。

        ``Typhon`` 会通过内置的 ``BashBypasser`` 对 ``cmd`` 进行等效变形（如： ``cat /flag`` 变为 ``cat$IFS$9/flag``）。因此，
        请使用原始的命令，而非等效变形后的命令。

        例如： 使用 ``cmd = "cat /flag"`` 而不是 ``cmd = "cat$IFS$9/flag"``。
    .. py:attribute:: local_scope

        执行命令时的本地作用域。即为执行环境时 ``globals`` 变量的值。

        假如，当前的执行环境为 ``exec(code, {'__builtins__': None'})``,
        则该变量应被设置为 ``{'__builtins__': None}``。

        .. caution::

            若没有指定命名空间，则 ``Typhon`` 会通过栈帧获取 ``import Typhon`` 这一行的全局变量空间。 *因此，在这种情况下，请将导入语句放在要执行的命令的上一行。*

            要做：

            .. code-block:: python

                def safe_run(cmd):
                    import Typhon
                    Typhon.bypassRCE(cmd,
                    banned_chr=['builtins', 'os', 'exec', 'import'])

                safe_run('cat /f*')


            不要做：

            .. code-block:: python

                import Typhon

                def safe_run(cmd):
                    Typhon.bypassRCE(cmd,
                    banned_chr=['builtins', 'os', 'exec', 'import'])

                safe_run('cat /f*')


        大多数沙箱不会设置执行函数的 ``locals`` 属性（即 ``exec`` 和 ``eval`` 函数的第三个变量）。
        但若有，从 `exec的文档 <https://docs.python.org/3/library/functions.html#exec>`_ 中我们可以得知，当执行空间中既存在
        ``locals`` 又存在 ``globals`` 时，``locals`` 变量将会覆盖 ``globals`` 变量。因此，我们将 ``local_scope`` 设置为
        ``globals`` 和 ``locals`` 的交集即可（若有重复元素，则以 ``locals`` 为准）。

    .. py:attribute:: banned_chr

        禁止使用的字符列表。

        本参数也可以接受一个字符串，请注意，此时字符串的每一个字符都将被视为禁止字符。

        例如： ``banned_chr = "abc"`` 等价于 ``banned_chr = ["a", "b", "c"]``。

    .. py:attribute:: allowed_chr

        允许使用的字符列表。

        本参数也可以接受一个字符串，请注意，此时字符串的每一个字符都将被视为允许字符。

        例如： ``allowed_chr = "abc"`` 等价于 ``allowed_chr = ["a", "b", "c"]``。

        .. warning::

            请勿将本参数与 :py:attr:`banned_chr` 参数同时使用。

    .. py:attribute:: banned_ast

        禁止使用的语法树节点列表。

        例如： ``banned_ast = [ast.Attribute]`` 表示禁止使用 `ast.Attribute <https://docs.python.org/3/library/ast.html#ast.Attribute>`_ 节点。
    
    .. py:attribute:: banned_re

        禁止使用的正则表达式列表。

        如果只有单个禁止的正则表达式，可以直接传入该正则表达式的字符串。

    .. py:attribute:: max_length

        最大长度限制。

    .. py:attribute:: allow_unicode_bypass

        是否允许使用 Unicode 绕过。若为 ``True``，则 ``Typhon`` 会尝试使用 Unicode 字符来绕过沙箱（如： ``__𝓲𝓶𝓹𝓸𝓻𝓽__``）。

        本参数默认为 ``False``。

    .. py:attribute:: print_all_payload

        是否打印所有有效载荷。若为 ``True``，则 ``Typhon`` 会打印所有有效载荷，而非仅打印第一个有效载荷。

        本参数默认为 ``False``。

    .. py:attribute:: interactive

        沙箱环境是否为交互式模式。换句话说，是否允许 ``stdin``，或是否允许用户再执行完命令后再次输入。
        当 ``interactive`` 为 ``True`` 时，``Typhon`` 会尝试使用 ``help()``， ``breakpoint`` 攻击沙箱。

        这个参数在面对一些 web 沙箱题目时非常有用。具体可见例题： `0xgame 2025 week3 <https://typhon.lamentxu.top/zh-cn/latest/EXAMPLE.html#xgame-2025-1-2>`_

        本参数默认为 ``True``。

    .. py:attribute:: depth

        最大递归深度。
        
        .. tip::

            当 ``Typhon`` 无法绕过一个沙箱时，可以尝试增大此值。

    .. py:attribute:: recursion_limit

        最大递归次数限制。

        .. tip::

            当 ``Typhon`` 无法绕过一个沙箱时，可以尝试增大此值。

    .. py:attribute:: log_level

        日志级别。

        可选值： ``"DEBUG"``、 ``"INFO"``、 ``"QUIET"`` 。

        ``"DEBUG"`` 日志级别会打印出沙箱的详细信息，包括每个步骤的执行时间、返回值、异常信息等。
        ``"INFO"`` 日志级别会打印出沙箱的简要信息，包括每个步骤的执行时间、返回值等。
        ``"QUIET"`` 日志级别会关闭所有日志输出。

.. function:: bypassREAD(filepath, RCE_method, is_allow_exception_leak: bool = True, local_scope: dict = None, banned_chr: list = [], allowed_chr: list = [], banned_ast: list = [], banned_re: list = [], max_length: int = None, allow_unicode_bypass: bool = False, print_all_payload: bool = False, interactive: bool = True, depth: int = 5, recursion_limit: int = 200, log_level: str = "INFO",)

    此函数的使用方法与 :py:func:`bypassRCE` 相似。其功能为绕过沙箱读取特定文件。

    .. py:attribute:: filepath

        要读取的文件的绝对路径或相对路径。
    
    .. py:attribute:: RCE_method

        读取文件时使用的 RCE 方法。仅能为 ``"exec"`` 或 ``"eval"``。
        
    .. note::

        由于文件读取需要关心回显问题（与 RCE 问题不同）， ``Typhon`` 将需要沙箱的 RCE 函数以做 payload 的调整。
        我们默认：
            - "exec" 模式：我们关心回显问题
            - "eval" 模式：我们不关心回显问题

        实战详见 `Typhon-Sample Pyjail 2 <https://typhon.lamentxu.top/zh-cn/latest/EXAMPLE.html#typhon-sample-pyjail-2>`_
    
    .. py:attribute:: is_allow_exception_leak

        靶机中是否可以泄露报错信息。此参数仅在 :py:attr:`~bypassREAD.RCE_method` 为 ``"exec"`` 时有效。
    
    其余参数与 :py:func:`bypassRCE` 相同。

.. function:: webui(host='127.0.0.1', port=6240, use_current_scope=False)

    启动 Typhon WebUI 服务器（阻塞调用）。

    .. py:attribute:: host

        绑定的主机地址，默认为 ``'127.0.0.1'``。

    .. py:attribute:: port

        监听的端口号，默认为 ``6240``。

    .. py:attribute:: use_current_scope

        若为 ``True``，则捕获调用方的 ``__main__`` 全局变量空间，并将其注入 WebUI
        作为默认 ``local_scope``。

        当 WebUI 的 "Local Scope" 字段留空时，将自动使用此变量空间，与内联
        ``import Typhon`` 的效果等价。详见 :doc:`WEBUI`。

