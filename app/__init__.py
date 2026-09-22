import os
import sys

# Extend package __path__ to search backend/app submodules (config, database, models, api, services, etc.)
backend_app_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "app")
if os.path.exists(backend_app_dir) and backend_app_dir not in __path__:
    __path__.append(backend_app_dir)

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
