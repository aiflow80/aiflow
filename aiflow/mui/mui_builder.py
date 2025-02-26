import time
from typing import List, Dict, Any, Set
from aiflow.mui.mui_component import MUIComponent
from aiflow.mui.mui_icons import MUIIcons
from aiflow.events import event_base

class MUIIconAccess:
    """Provides direct access to MUI icons without parentheses"""
    def __init__(self, builder):
        self._builder = builder

    def __getattr__(self, icon_name: str) -> MUIComponent:
        return MUIComponent(icon_name, module="muiIcons", builder=self._builder)

class MUIBuilder:
    def __init__(self):
        self._stack: List[MUIComponent] = []
        self._roots: List[MUIComponent] = []
        self._icons = MUIIcons(self)
        self._id_counter = 1
        self.icon = MUIIconAccess(self)
        self._component_sequence = []  # List to track component creation and props
        self._components = []
        self._order_counter = 0
        self._current_parent_id = 0
        self._component_hierarchy = {}  # Track parent-child relationships
        self._current_parent = None

    def get_next_id(self) -> int:
        """Get next sequential ID starting from 0 (or 1)"""
        current_id = self._id_counter
        self._id_counter += 1
        return current_id  # Returns 0, 1, 2... (or 1, 2, 3... if initialized to 1)

    @property
    def icons(self):
        return self._icons

    def _process_args(self, args: tuple) -> List[MUIComponent]:
        """Convert arguments to components or text components"""
        processed = []
        for arg in args:
            if isinstance(arg, (str, int, float)):
                processed.append(MUIComponent(str(arg), module="text", builder=self))
            elif isinstance(arg, MUIComponent) and not hasattr(arg, '_is_prop'):
                processed.append(arg)
        return processed

    def _process_props(self, props: dict) -> dict:
        """Process and mark prop components"""
        processed = {}
        for key, value in props.items():
            if isinstance(value, MUIComponent):
                value._is_prop = True
                value._skip_update = True
                # Track the component that will contain this prop
                if self._stack:
                    value._parent = self._stack[-1]
            processed[key] = value
        return processed

    def _update_component_sequence(self, component_type: str, component_dict: dict, processed_props: dict, 
                                processed_children: list, current_parent_id: str) -> None:

        for item in self._component_sequence:
            if item['type'] == component_type and item['props_updated'] == False:
                item.update({
                    'props_updated': True,
                    'props': processed_props,
                    'children': [child.to_dict() for child in processed_children],
                    'component_id': component_dict["id"],
                    'parent_id': current_parent_id,
                    'text_content': component_dict.get("content"),
                    'order': self._order_counter
                })

    def create_component(self, element: str, *args, **props) -> MUIComponent:
        processed_props = self._process_props(props)
        processed_children = self._process_args(args)
        
        component = MUIComponent(
            element, 
            module="muiElements", 
            props=processed_props,
            children=processed_children,
            builder=self
        )
        component.name = f"{element}_{self._order_counter}"

        # Set parent relationship
        current_parent_id = None
        if self._stack:
            parent = self._stack[-1]
            current_parent_id = f"{parent.type}_{parent.unique_id}"
            component._parent = parent

        # Process props that are components to set correct parent
        for prop_value in processed_props.values():
            if isinstance(prop_value, MUIComponent):
                prop_value._parent = component

        # Create component info with children key
        component_info = {
            'id': self._order_counter,
            'component': component.name,
            'order': self._order_counter,
            'props_updated': False,
            'props': processed_props,
            'parent_id': current_parent_id,
            'children': []  # Initialize empty children list
        }

        # Update parent's children if exists
        if current_parent_id and self._stack:
            parent_info = next(
                (item for item in self._component_sequence 
                 if item['component'] == self._stack[-1].name),
                None
            )
            if parent_info:
                if 'children' not in parent_info:
                    parent_info['children'] = []
                parent_info['children'].append(component_info)

        # Create component dict and handle children
        component_dict = component.to_dict()
        
        # Update component dict for prop components
        for key, value in processed_props.items():
            if isinstance(value, MUIComponent):
                value_dict = value.to_dict()
                value_dict["parentId"] = component_dict["id"]

        if processed_children and len(processed_children) == 1:
            first_child = processed_children[0]
            if isinstance(first_child, MUIComponent) and first_child.type == "text":
                component_dict["content"] = first_child.text_content

        if current_parent_id:
            component_dict["parentId"] = current_parent_id

        # Update component sequence
        self._update_component_sequence(
            component.type, 
            component_dict, 
            processed_props, 
            processed_children, 
            current_parent_id
        )

        # Check for unupdated props before appending
        non_updated = [item for item in self._component_sequence if not item['props_updated']]
        if len(non_updated) == 0:
            self._components.append(component_dict)

            event_base.send_response_sync({
                "type": "component_update",
                "payload": {
                    "component": component_dict,
                    "timestamp": time.time()
                }
            })

        return component

    def __getattr__(self, element: str):
        if not element.startswith('__'):
            self._order_counter += 1
            component_name = f"{element}_{self._order_counter}"
            print(component_name)
            
            component_info = {
                'id': self._order_counter,
                'type': element,
                'component': component_name,
                'order': self._order_counter,
                'props_updated': False,
                'props': {},
                'parent_id': None if not self._stack else self._stack[-1].unique_id,
                'children': []  # Initialize empty children list
            }
            self._component_sequence.append(component_info)

        def component_creator(*args, **props):
            return self.create_component(element, *args, **props)
            
        return component_creator
