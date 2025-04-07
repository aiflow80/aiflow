from typing import Any, Dict, List, Optional, Union
from aiflow.flow.events import event_base

class MUIComponent:
    _sent_components = {}
    # Remove static configuration and make it dynamic
    
    def __init__(
        self,
        type_name: str,
        module: str = "muiElements",
        props: Optional[Dict[str, Any]] = None,
        children: Optional[List[Union[str, "MUIComponent"]]] = None,
        builder: Optional[Any] = None
    ):
        # Core component properties
        self.type = "text" if module == "text" else type_name
        self.module = module
        self.props = props or {}
        self.children = []
        self.text_content = None
        
        # Relationship tracking
        self._builder = builder
        self._parent = None
        self._parent_id = None
        self.unique_id = self._builder.get_next_id() if self._builder else 0
        self._child_components = []
        self._is_prop_component = False
        self._prop_parent = None
        self._special_props = {}  # Track special component props

        # Handle text content or process children
        if module == "text":
            self.text_content = str(type_name)
        elif children:
            self._process_children_dynamically(children)

    def __call__(self, *args, **kwargs):
        """
        Makes the component callable to add children to it.
        This allows syntax like: mui.Avatar(...)(mui.IconButton(...))
        And with keyword arguments: mui.Avatar(...)(mui.IconButton(...), sx={...})
        """
        # Process keyword arguments as additional props
        if kwargs:
            for key, value in kwargs.items():
                self.props[key] = value
        
        # Process positional arguments as children
        for arg in args:
            if isinstance(arg, (str, int, float)):
                # Handle text content
                self.text_content = str(arg)
            elif isinstance(arg, MUIComponent):
                # Add component as child
                self.add_child(arg)
                
        return self

    def _process_children_dynamically(self, children):
        """Dynamically process children and detect what should be props vs actual children"""
        regular_children = []
        
        for child in children:
            if isinstance(child, (str, int, float)):
                regular_children.append(child)
            elif isinstance(child, MUIComponent):
                # Check if this child has a prop key - if so, treat it as a prop
                if hasattr(child, '_prop_key'):
                    self.props[child._prop_key] = child
                    child._parent = self
                    child._parent_id = f"{self.type}_{self.unique_id}"
                    child._is_prop_component = True
                    self._special_props[child._prop_key] = child
                else:
                    regular_children.append(child)
            else:
                regular_children.append(child)
        
        # Process remaining regular children
        if len(regular_children) == 1 and isinstance(regular_children[0], (str, int, float)):
            self.text_content = str(regular_children[0])
        else:
            self._process_children(regular_children)

    def _process_children(self, children):
        for idx, child in enumerate(children):
            if isinstance(child, (str, int, float)):
                text_id = f"text_{self.unique_id}_{len(self.children)}"
                self.children.append({
                    "type": "text",
                    "content": str(child),
                    "id": text_id
                })
            else:
                child._parent = self
                child._parent_id = f"{self.type}_{self.unique_id}"
                self.children.append(child)

    def _process_props(self) -> Dict[str, Any]:
        processed_props = {}
        for key, value in self.props.items():
            if isinstance(value, MUIComponent):
                value._parent = self
                value._parent_id = f"{self.type}_{self.unique_id}"
                value._is_prop_component = True
                value._prop_key = key  # Store the prop key for special component identification
                
                processed_props[key] = value.to_dict()
            else:
                processed_props[key] = value
        return processed_props

    def __enter__(self):
        if not hasattr(self, '_is_prop'):
            if self._builder:
                self._builder._stack.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._builder and self._builder._stack:
            if len(self._builder._stack) > 1:
                current = self._builder._stack.pop()
                parent = self._builder._stack[-1]
                current._parent = parent
                current._parent_id = f"{parent.type}_{parent.unique_id}"
                if current not in parent.children:
                    parent.children.append(current)
            else:
                self._builder.root = self._builder._stack.pop()
        return False

    def add_child(self, child: "MUIComponent") -> None:
        # Check if this child should be a prop instead (dynamic check)
        if hasattr(child, '_prop_key'):
            self.props[child._prop_key] = child
            child._parent = self
            child._parent_id = f"{self.type}_{self.unique_id}"
            child._is_prop_component = True
            self._special_props[child._prop_key] = child
            return
                
        # Regular child handling
        child._parent = self
        child._parent_id = f"{self.type}_{self.unique_id}"
        self._child_components.append(child)
        if child not in self.children:
            self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        component_id = f"{self.type}_{self.unique_id}"
        parent_id = None
        
        if self._parent:
            parent_id = f"{self._parent.type}_{self._parent.unique_id}"
            
        data = {
            "type": self.type,
            "id": component_id,
            "module": self.module,
            "props": self._process_props(),
            "parentId": parent_id,
        }
        
        if self.text_content is not None:
            data["content"] = self.text_content
            
        # Only include actual children, not props
        children_to_include = []
        for child in self.children:
            # Skip children that are actually props
            if isinstance(child, MUIComponent) and hasattr(child, '_prop_key') and child._is_prop_component:
                continue
                
            children_to_include.append(child)
            
        if children_to_include:
            data["children"] = []
            for child in children_to_include:
                if isinstance(child, dict) and child["type"] == "text":
                    child_data = {
                        "type": "text",
                        "id": child["id"],
                        "content": child["content"],
                        "parentId": component_id
                    }
                    data["children"].append(child_data)
                elif isinstance(child, MUIComponent):
                    child_dict = child.to_dict()
                    child_dict["parentId"] = component_id
                    data["children"].append(child_dict)
            
        return data
