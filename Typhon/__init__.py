# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0

from .Typhon import bypassRCE, bypassREAD, bypassMAIN, VERSION

__version__ = VERSION

__all__ = [
    "VERSION",
    "bypassRCE",
    "bypassREAD",
]