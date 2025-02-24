from typing import Any, Dict, List, Optional, Union
import time
from aiflow.events import event_base

class MUIComponent:
    _sent_components = {}

    def __init__(
        self,
        type_name: str,
        module: str = "muiElements",
        props: Optional[Dict[str, Any]] = None,
        children: Optional[List[Union[str, "MUIComponent"]]] = None,
        builder: Optional[Any] = None
    ):
        self.type = "text" if module == "text" else type_name
        self.text_content = None
        self.module = module
        self.props = props or {}
        self.children = []
        self._builder = builder
        self._parent = None
        self.unique_id = self._builder.get_next_id() if self._builder else 0

        # Handle direct text content for Typography or other components
        if isinstance(type_name, (str, int, float)) and module == "text":
            self.text_content = str(type_name)
            self.type = "text"
        elif children and len(children) == 1 and isinstance(children[0], (str, int, float)):
            # If there's a single text child, treat it as direct content
            self.text_content = str(children[0])
            self.children = []
        else:
            # Process children normally
            if children:
                for child in children:
                    if isinstance(child, (str, int, float)):
                        text_component = {
                            "type": "text",
                            "content": str(child),
                            "id": f"text_{self.unique_id}_{len(self.children)}"
                        }
                        self.children.append(text_component)
                    else:
                        self.children.append(child)

    def __enter__(self):
        component_id = f"{self.type}_{self.unique_id}"
        
        if hasattr(self, '_is_prop'):
            return self

        # Process props to convert MUIComponents to dicts
        processed_props = {}
        for key, value in self.props.items():
            if isinstance(value, MUIComponent):
                value._parent = self
                processed_props[key] = value.to_dict()
            else:
                processed_props[key] = value

        # Create component data
        component_data = {
            "type": self.type,
            "id": component_id,
            "module": self.module,
            "props": processed_props,
            "parentId": f"{self._parent.type}_{self._parent.unique_id}" if self._parent else None,
            "children": []
        }

        # Add text content if present
        if self.text_content is not None:
            component_data["content"] = self.text_content
        
        # Process children
        if self.children:
            for idx, child in enumerate(self.children):
                if isinstance(child, dict) and child["type"] == "text":
                    text_child = {
                        "type": "text",
                        "id": f"text_{self.unique_id}_{idx}",
                        "content": child["content"],
                        "parentId": component_id
                    }
                    component_data["children"].append(text_child)
                elif isinstance(child, MUIComponent):
                    child._parent = self
                    child_id = f"{child.type}_{child.unique_id}"
                    component_data["children"].append({"id": child_id})

        # Send component update
        event_base.send_response_sync({
            "type": "component_update",
            "payload": {
                "component": component_data,
                "timestamp": time.time()
            }
        })

        if self._builder:
            self._builder._stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._builder and self._builder._stack:
            if len(self._builder._stack) > 1:
                current = self._builder._stack.pop()
                parent = self._builder._stack[-1]
                current._parent = parent
                if current not in parent.children:
                    parent.children.append(current)
            else:
                self._builder.root = self._builder._stack.pop()
        return False

    def to_dict(self) -> Dict[str, Any]:
        component_id = f"{self.type}_{self.unique_id}"
        
        processed_props = {}
        for key, value in self.props.items():
            if isinstance(value, MUIComponent):
                processed_props[key] = value.to_dict()
            else:
                processed_props[key] = value

        component_dict = {
            "type": self.type,
            "id": component_id,
            "module": self.module,
            "props": processed_props,
            "parentId": f"{self._parent.type}_{self._parent.unique_id}" if self._parent else None
        }

        # Include text content if present
        if self.text_content is not None:
            component_dict["content"] = self.text_content

        return component_dict
