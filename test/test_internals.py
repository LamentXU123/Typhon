import sys  # noqa

sys.path.append("..")  # noqa

# test script for Typhon package
import unittest

from unittest.mock import patch
from io import StringIO
from contextlib import redirect_stdout


class TestTyphonRCE(unittest.TestCase):
    def tearDown(self):
        print(f"✓ Testcase '{self._testMethodName}' done.")

    def test_bypassRCE(self):
        with patch("builtins.quit") as mock_quit:
            mock_quit.side_effect = SystemExit("Test")
            import Typhon

            with self.assertRaises(SystemExit):
                Typhon.bypassRCE(
                    cmd="",
                )
            del Typhon
            mock_quit.assert_called_with(1)
        with redirect_stdout(StringIO()) as f:
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import string
                import Typhon
                import ast
        with redirect_stdout(StringIO()) as f:
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import string
                import Typhon
                import ast

                with self.assertRaises(RuntimeError):
                    Typhon.bypassRCE(
                        cmd="whoami",
                        interactive=False,
                        allowed_chr=string.printable,
                        allow_unicode_bypass=True,
                        banned_ast=[ast.Import],
                        local_scope={},
                    )
                del Typhon
                mock_exit.assert_called_with(0)
        with redirect_stdout(StringIO()) as f:
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import string
                import Typhon
                import ast

                with self.assertRaises(RuntimeError):
                    Typhon.bypassRCE(
                        cmd="whoami",
                        interactive=False,
                        banned_chr=["'", '"', "i", "b", "__doc__"],
                        allow_unicode_bypass=True,
                        banned_ast=[ast.Import],
                        local_scope={},
                    )
                del Typhon
                mock_exit.assert_called_with(0)
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import string
                import Typhon

                with self.assertRaises(RuntimeError):
                    Typhon.bypassRCE(
                        cmd="whoami",
                        interactive=False,
                        allow_unicode_bypass=True,
                        local_scope={},
                    )
                del Typhon
                mock_exit.assert_called_with(0)
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import string
                import Typhon

                with self.assertRaises(RuntimeError):
                    Typhon.bypassRCE(
                        cmd="cat /tmp/flag.txt",
                        banned_chr=[".", "_", "[", "]", "'", '"'],
                    )
                del Typhon
                mock_exit.assert_called_with(0)
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import string
                import Typhon

                with self.assertRaises(RuntimeError):
                    Typhon.bypassRCE(
                        cmd="whoami",
                        interactive=True,
                        banned_chr=["help", "breakpoint", "input"],
                        banned_re=r".*import.*",
                    )
                del Typhon
                mock_exit.assert_called_with(0)
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import Typhon

                with self.assertRaises(RuntimeError):
                    Typhon.bypassRCE(
                        cmd="cat /flag",
                        local_scope={"__builtins__": None},
                        banned_chr=[
                            "__loader__",
                            "__import__",
                            "os",
                            "[:",
                            "\\x",
                            "+",
                            "join",
                        ],
                        interactive=True,
                        recursion_limit=200,
                        depth=5,
                    )
                del Typhon
                mock_exit.assert_called_with(0)


class TestTyphonREAD(unittest.TestCase):
    def tearDown(self):
        print(f"✓ Testcase '{self._testMethodName}' done.")

    def test_bypassREAD(self):
        with redirect_stdout(StringIO()) as f:
            with patch("builtins.quit") as mock_quit:
                mock_quit.side_effect = SystemExit("Test")
                import Typhon

                with self.assertRaises(SystemExit):
                    Typhon.bypassREAD(filepath="", RCE_method="")
                del Typhon
                mock_quit.assert_called_with(1)
        with redirect_stdout(StringIO()) as f:
            with patch("builtins.quit") as mock_quit:
                mock_quit.side_effect = SystemExit("Test")
                import Typhon

                with self.assertRaises(SystemExit):
                    Typhon.bypassREAD(filepath="flag", RCE_method="none")
                del Typhon
                mock_quit.assert_called_with(1)
        with redirect_stdout(StringIO()) as f:
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import Typhon

                with self.assertRaises(RuntimeError):
                    Typhon.bypassREAD(filepath="/flag", RCE_method="exec")
                del Typhon
                mock_exit.assert_called_with(0)
        with redirect_stdout(StringIO()) as f:
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import Typhon

                with self.assertRaises(RuntimeError):
                    Typhon.bypassREAD(
                        "/flag",
                        RCE_method="eval",
                        allow_unicode_bypass=True,
                        is_allow_exception_leak=True,
                        local_scope={"lit": list, "dic": dict, "__builtins__": None},
                        banned_chr="𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵𝓪𝓫𝓬𝓭𝓮𝓯𝓰bcdefgjklnpqrstuvxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                    )
                del Typhon
                mock_exit.assert_called_with(0)
        with redirect_stdout(StringIO()) as f:
            with patch("builtins.exit") as mock_exit:
                mock_exit.side_effect = RuntimeError("Test")
                import Typhon

                with self.assertRaises(RuntimeError):
                    Typhon.bypassREAD(
                        "/flag",
                        RCE_method="exec",
                        allow_unicode_bypass=True,
                        is_allow_exception_leak=True,
                        local_scope={"lit": list, "dic": dict, "__builtins__": None},
                        banned_chr="𝒶𝒷𝒸𝒹ℯ𝒻ℊ𝒽𝒾𝒿𝓀𝓁𝓂𝓃ℴ𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜ℬ𝒞𝒟ℰℱ𝒢ℋℐ𝒥𝒦ℒℳ𝒩𝒪𝒫𝒬ℛ𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵𝓪𝓫𝓬𝓭𝓮𝓯𝓰bcdefgjklnpqrstuvxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                    )
                del Typhon
                mock_exit.assert_called_with(0)
