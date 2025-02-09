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
        builder: Optional[Any] = None
    ):
        if module == "text":
            self.type = "text"
            self.text_content = str(type_name)
        else:
            self.type = type_name
            self.text_content = None
            
        self.module = module
        self.props = props or {}
        self.children = children or []
        self._builder = builder
        self._parent = None
        self.unique_id = self._builder.get_next_id() if self._builder else 0

    def _component_creation(self):
        if self.type != "text" or not self._parent:
            print(f"init {self.to_dict()}")
            # Ensure consistent message format
            message = {
                "type": "component_update",
                "payload": {
                    "component": self.to_dict(),
                    "timestamp": time.time()
                }
            }
            
            event_base.send_response_sync(message)

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
                
        return False

    def to_dict(self) -> Dict[str, Any]:
        if self.type == "text":
            return {
                "type": "text",
                "id": f"text_{self.unique_id}",
                "content": self.text_content
            }
            
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
