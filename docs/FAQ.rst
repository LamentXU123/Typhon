FAQ 常见问题
==================

如何使用 ``help()`` RCE
---------------------------

有时 ``Typhon`` 会返回 ``help`` 函数作为payload。在linux中，假如我们能进入python help的交互式界面，我们可以输入：

.. code-block:: bash

    help> os

随后再输入 ``!sh`` 即可获得shell。

.. warning::
    
    由于实现方式不同，此方法只对linux环境有效。如果你想用其他的函数，如 ``breakpoint()``，请将对应绕过函数的 :py:attr:`~bypassRCE.print_all_payload` 变量设置为 ``True``。

如何使用 ``breakpoint()`` RCE
-----------------------------

有时 ``Typhon`` 会返回 ``breakpoint`` 函数作为payload。在linux中，假如我们能进入python help的交互式界面，我们可以输入：

.. code-block:: bash

    >>> breakpoint()
    1
    > <python-input-1>(1)<module>()
    (Pdb) __import__('os').system('') # 你要输入的命令

这样就可以进行RCE（当然你也可以替换成其他命令）。 ``pdb.set_trace()`` 同理。

一定要使用与题目相同的环境吗
-------------------------------

Pyjail中存在一些通过索引寻找对应object的gadgets（如继承链）。继承链的利用随着索引变化很大。因此，请务必确保 ``Typhon`` 的运行环境与题目相同。

.. note::

    **无法保证？**

    大多数题目都不会给出对应的python版本。因此， **Typhon会在使用涉及版本的gadgets时做出提示** 。  

    .. image:: https://picui.ogmua.cn/s1/2026/03/13/69b3f7ca70973.webp

    这种情况下往往需要CTF选手自己去找题目环境中该gadgets需要的索引值。在选择时， ``Typhon`` 会尽量避免使用此类payload。

如果题目的 ``exec`` 和 ``eval`` 没有限制命名空间怎么办
---------------------------------------------------------------------------------------------------

假设题目没有限制命名空间，则不必填写 :py:attr:`~bypassRCE.local_scope` 参数。Typhon会自动使用 ``import Typhon`` 时的当前命名空间进行绕过。

这个payload我用不了能不能换一个
-------------------------------------------------------------------------------------------------------

你可以在参数中将 :py:attr:`~ bypassRCE.print_all_payload` 设置为 ``True`` ， ``Typhon`` 就会打印其生成的所有payload。

同时，请注意输出中的 ``reminder`` ，它会提示你该题目需要的环境。请确保题目中的环境符合 ``reminder`` 所描述的情况。

这个WEB题好像没开放stdin，我 ``exec(input())`` 没用怎么办？
--------------------------------------------------------------------------------------------------------

你可以在参数中将 :py:attr:`~bypassRCE.interactive` 设置为 ``False`` ，Typhon就会禁止使用所有涉及 ``stdin`` 的payload。

最后输出的payload没回显怎么办
-------------------------------------------------------------------------------------------

对于 :py:func:`bypassRCE` ，我们认为： **只要命令得到了执行，就是RCE成功。** 至于回显问题，你可以选择反弹shell，时间盲注，或者：添加 ``print_all_payload=True`` 参数，查看所有payload，其中可能含有能够成功回显的payload。

跑得好慢怎么办
---------------------

对于复杂度高的题目，由于采用了局部最优的递归策略， ``Typhon`` 可能要用时 5 分钟左右，请耐心等待。

如果你想提升性能，可以尝试：

- 设置较低的 :py:attr:`~bypassRCE.recursion_limit` 值，如设置为100。

- 设置较低的 :py:attr:`~bypassRCE.depth` 值，如设置为3。