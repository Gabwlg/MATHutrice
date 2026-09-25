import os

# mathutrice.database builds its engine from DATABASE_URL at import time, and
# the app is designed to refuse to start without it (see docs/smoke-test.md).
# Tests that don't care which database backs it still trigger that import
# transitively, so give it a value before anything under mathutrice/ loads.
os.environ.setdefault("DATABASE_URL", "sqlite://")
