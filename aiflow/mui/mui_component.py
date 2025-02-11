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
        # Skip if this component is used as a prop
        if hasattr(self, '_is_prop'):
            return

        component_data = self.to_dict(include_children=False)
        message = {
            "type": "component_update",
            "payload": {
                "component": component_data,
                "timestamp": time.time()
            }
        }
        event_base.send_response_sync(message)

        # Only process non-prop children
        for child in self.children:
            if isinstance(child, MUIComponent):
                if not hasattr(child, '_is_prop'):
                    child._component_creation()
            else:
                # Handle text nodes
                text_data = {
                    "type": "text",
                    "id": f"text_{self._builder.get_next_id()}",
                    "content": str(child),
                    "parentId": component_data["id"]
                }
                message = {
                    "type": "component_update",
                    "payload": {
                        "component": text_data,
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

    def to_dict(self, include_children=True) -> Dict[str, Any]:
        # Convert nested MUIComponents in props
        converted_props = {}
        for k, v in self.props.items():
            if isinstance(v, MUIComponent):
                # For prop components, set their parent to this component
                if hasattr(v, '_is_prop'):
                    v._parent = self
                converted_props[k] = v.to_dict()
            else:
                converted_props[k] = v

        if self.type == "text":
            data = {
                "type": "text",
                "id": f"text_{self.unique_id}",
                "content": self.text_content
            }
            if self._parent:
                data["parentId"] = f"{self._parent.type}_{self._parent.unique_id}"
            return data
            
        data = {
            "type": self.type,
            "id": f"{self.type}_{self.unique_id}",
            "module": self.module,
            "props": converted_props
        }
        
        if self._parent:
            data["parentId"] = f"{self._parent.type}_{self._parent.unique_id}"

        if include_children:
            data["children"] = [
                child.to_dict() if isinstance(child, MUIComponent)
                else {"type": "text", "content": str(child)}
                for child in self.children
            ]
        
        return data
