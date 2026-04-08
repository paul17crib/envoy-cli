"""Remote environment provider abstraction for envoy-cli."""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional

from envoy.parser import parse_env_string, serialize_env


class RemoteProvider(ABC):
    """Abstract base class for remote env providers."""

    @abstractmethod
    def pull(self, env_name: str) -> dict:
        """Fetch env vars from the remote source."""
        ...

    @abstractmethod
    def push(self, env_name: str, env: dict) -> None:
        """Push env vars to the remote source."""
        ...


class FileRemoteProvider(RemoteProvider):
    """A simple file-based remote provider (useful for testing / shared dirs)."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def _path_for(self, env_name: str) -> str:
        return os.path.join(self.base_dir, f"{env_name}.env")

    def pull(self, env_name: str) -> dict:
        path = self._path_for(env_name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Remote env not found: {path}")
        with open(path) as f:
            return parse_env_string(f.read())

    def push(self, env_name: str, env: dict) -> None:
        os.makedirs(self.base_dir, exist_ok=True)
        path = self._path_for(env_name)
        with open(path, "w") as f:
            f.write(serialize_env(env))


class JSONRemoteProvider(RemoteProvider):
    """A JSON file-based remote provider (stores envs as JSON objects)."""

    def __init__(self, json_path: str):
        self.json_path = json_path

    def _load_store(self) -> dict:
        if not os.path.exists(self.json_path):
            return {}
        with open(self.json_path) as f:
            return json.load(f)

    def _save_store(self, store: dict) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.json_path)), exist_ok=True)
        with open(self.json_path, "w") as f:
            json.dump(store, f, indent=2)

    def pull(self, env_name: str) -> dict:
        store = self._load_store()
        if env_name not in store:
            raise KeyError(f"No remote env named {env_name!r}")
        return store[env_name]

    def push(self, env_name: str, env: dict) -> None:
        store = self._load_store()
        store[env_name] = env
        self._save_store(store)
