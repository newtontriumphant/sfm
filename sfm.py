#!/usr/bin/env python3

from __future__ import annotations
import sys
import os
import re
import shutil
import signal
import subprocess
import platform
import mimetypes
import tempfile
import textwrap
from pathlib import Path

__version__ = "1.0.1"

if __name__ == "__main__":
    main()