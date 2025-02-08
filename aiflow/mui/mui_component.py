from typing import Any, Dict, List, Optional, Union
import time
from aiflow.events import event_base

class MUIComponent:
    def __init__(
        self,
        type_name: str,
        module: str = "muiElements",
        props: Optional[Dict[str, Any]] = None,
        children: Optional[List[Union[str, "MUIComponent"]]] = None,
        builder: Optional[Any] = None  # Changed to Any to avoid circular import
    ):
        self.type = type_name
        self.module = module
        self.props = props or {}
        self.children = children or []
        self._builder = builder
        self._parent = None
        self.unique_id = self._builder.get_next_id() if self._builder else 0
        self._log_creation()

    def _log_creation(self):
        print(self.to_dict())

    def __enter__(self):
        if self._builder:
            self._builder._stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._builder:
            if len(self._builder._stack) > 1:
                # Handle nested components
                parent = self._builder._stack[-2]
                current = self._builder._stack.pop()
                current._parent = parent
                if current not in parent.children:
                    parent.children.append(current)
            else:
                # Handle root component
                self._builder.root = self._builder._stack.pop()
                component_data = self.to_dict()
                
                # Ensure consistent message format
                message = {
                    "type": "component_update",
                    "payload": {
                        "component": component_data,
                        "timestamp": time.time()
                    }
                }
                event_base.queue_message(message)
        return False

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "type": self.type,
            "id": f"{self.type}_{self.unique_id}",
            "module": self.module,
            "props": self.props,
            "children": [
                child.to_dict() if isinstance(child, MUIComponent) 
                else {"type": "text", "content": str(child)}
                for child in self.children
            ]
        }
        if self._parent:
            data["parentId"] = f"{self._parent.type}_{self._parent.unique_id}"
        return data
