import importlib
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def init_routers(app: FastAPI) -> None:
    """Dynamically discover and register all module routers."""
    modules_path = Path(__file__).parent.parent / "modules"

    if not modules_path.exists():
        return

    for module_dir in modules_path.iterdir():
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue

        routes_dir = module_dir / "routes"
        if not routes_dir.exists():
            continue

        for route_file in routes_dir.glob("*_routes.py"):
            module_name = route_file.stem
            import_path = f"app.modules.{module_dir.name}.routes.{module_name}"

            try:
                module = importlib.import_module(import_path)
                if hasattr(module, "router"):
                    prefix = f"/api/v1/{module_dir.name.replace('_', '-')}"
                    app.include_router(module.router, prefix=prefix)
            except ImportError as e:
                print(f"Failed to import {import_path}: {e}")


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
