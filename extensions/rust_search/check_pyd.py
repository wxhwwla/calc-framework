"""Check if the Rust .pyd loads correctly from a MEI directory."""

import sys

mei = sys.argv[1]
sys.path.insert(0, mei)

try:
    import rust_search

    print(f"OK: rust_search imported from {mei}")
    print(f"  functions: {[x for x in dir(rust_search) if not x.startswith('_')]}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
