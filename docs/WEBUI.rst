WEBUI 网页界面
=================

``Typhon`` 内置一个轻量的 WebUI（仅使用 Python 标准库），用于在浏览器中调用 :func:`~Typhon.bypassRCE` / :func:`~Typhon.bypassREAD`。

启动方式
--------

**方式一：命令行启动**

如果你通过 pip 安装了 ``typhonbreaker``，可以直接启动：

.. code-block:: bash

   typhonbreaker webui

默认监听 ``127.0.0.1:6240``，浏览器打开： ``http://127.0.0.1:6240`` 。

``webui`` 支持以下参数：

.. code-block:: bash

   typhonbreaker webui --host 0.0.0.0 --port 6240

.. warning::

   WebUI 默认绑定到 ``127.0.0.1``。如果你运行在服务器上，请自行做好访问控制/防火墙配置。

**方式二：Python API 启动（可注入当前变量空间）**

.. py:function:: Typhon.webui(host='127.0.0.1', port=6240, use_current_scope=True)

   启动 Typhon WebUI 服务器。

   .. py:attribute:: host

      绑定的主机地址，默认为 ``'127.0.0.1'``。

   .. py:attribute:: port

      监听的端口号，默认为 ``6240``。

   .. py:attribute:: use_current_scope

      若为 ``True``，则捕获调用方的 ``__main__`` 全局变量空间，并将其注入 WebUI
      作为默认的 ``local_scope``。

      这与在题目代码中内联 ``import Typhon`` 的效果等价——当 WebUI 中 "Local Scope"
      字段留空时，将自动使用此注入的变量空间，无需手动输入。

      此参数默认为 ``True``。

命令行方式无法获取当前 Python 进程的变量空间（因为没有 ``import Typhon`` 的过程）。
通过 Python API 调用 ``Typhon.webui(use_current_scope=True)``，可以在原始脚本内部
捕获当前 ``__main__`` 的全局变量，随后在 WebUI 中直接使用，这样就可以引入命名空间内题目自定义的变量。

**使用示例**：

.. code-block:: python

   import re
   import Typhon

   def safe_run(cmd):
       if re.match(r'.*import.*', cmd):
           return "WAF!"
       exec(cmd, {'__builtins__': {}})

   # 不再需要在 safe_run 内部 import Typhon 并调用 bypassRCE——
   # 直接用 webui 启动，注入当前全局空间，在浏览器中操作即可。
   Typhon.webui(use_current_scope=True)

.. note::

   ``use_current_scope=True`` 捕获的是 ``__main__`` 模块的全局变量空间，
   与命令行 ``typhonbreaker webui`` 的 "无 local_scope" 模式等价，但能自动
   携带当前脚本中已定义的变量（如 ``re``、``safe_run`` 等）。

   若题目的 ``exec`` 设置了受限命名空间（如 ``exec(cmd, {'__builtins__': {}})``），
   仍需在 WebUI 的 "Local Scope" 字段手动填写该受限字典——此时手动填写会覆盖注入的空间。

   当通过 ``Typhon.webui(use_current_scope=True)`` 启动 WebUI 时，页面顶部的
   "Local Scope" 输入框上方会显示一条绿色横幅，提示已注入调用方的变量空间，以及该空间中的公开变量名。此时留空 "Local Scope" 字段即可使用注入的空间。

   
Docker
------

本仓库提供用于构建 WebUI 镜像的 ``Dockerfile``，你可以用 compose 直接启动：

.. code-block:: bash

   docker compose up --build

