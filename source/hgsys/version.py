VER_MAJOR: int = 0
VER_MINOR: int = 6
VER_PATCH: int = 0
VER_EXTRA: str = ""
VER_STRING: str = f"{VER_MAJOR}.{VER_MINOR}.{VER_PATCH}{VER_EXTRA}"

"""History
0.6.0:
    Rewrite as a Python package with MVVM separation
    (domain / repository / services / viewmodels / views).
"""
