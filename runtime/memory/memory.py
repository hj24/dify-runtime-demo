import threading
from typing import Any, Dict

class GlobalMemory:
    def __init__(self, initial_data: Dict[str, Any] = None):
        self._data = initial_data or {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            # Support dot notation for nested access (simplified)
            keys = key.split('.')
            value = self._data
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return None
            return value

    def set(self, key: str, value: Any):
        with self._lock:
            self._data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return self._data.copy()
