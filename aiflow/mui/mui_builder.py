from typing import List, Dict, Any, Set
from aiflow.mui.mui_component import MUIComponent
from aiflow.mui.mui_icons import MUIIcons

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
        self._id_counter = 0
        self.icon = MUIIconAccess(self)
        self._component_sequence = []  # List to track component creation and props
        self._components = []
        self._order_counter = 0
        self._current_parent_id = 0

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
                value._skip_update = True  # Add flag to skip direct updates
            processed[key] = value
        return processed

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
        
        # Find and update all matching components that haven't been updated
        for comp_info in self._component_sequence:
            if (comp_info['component'].startswith(f"{element}_") and 
                not comp_info.get('props_updated', False)):
                # Update props based on element type
                merged_props = {**props}
                comp_info['props'] = merged_props
                comp_info['props_updated'] = True
                comp_info['children'] = processed_children
                
                # Add text content if it exists in children  <-- ONLY NEW LINE
                if processed_children and len(processed_children) == 1 and isinstance(processed_children[0], MUIComponent) and processed_children[0].type == "text":
                    comp_info['content'] = processed_children[0].text_content
                
                # Set parent relationship
                if self._stack:
                    parent_component = next(
                        (item for item in self._component_sequence 
                         if item['component'] == self._stack[-1].name),
                        None
                    )
                    if parent_component:
                        comp_info['parent_id'] = parent_component.get('id')
                break

        # Create component dict
        component_dict = component.to_dict()
        
        # Add text content if it exists in children
        if processed_children and len(processed_children) == 1:
            first_child = processed_children[0]
            if isinstance(first_child, MUIComponent) and first_child.type == "text":
                component_dict["props"]["type"] = "text"
                component_dict["props"]["content"] = first_child.text_content

        non_updated = [comp for comp in self._component_sequence 
            if not comp.get('props_updated', False)]
        
        if len(non_updated) == 0:
            component_dict = component.to_dict()
            # Just add text content if present in first child
            if processed_children and len(processed_children) == 1:
                first_child = processed_children[0]
                if isinstance(first_child, MUIComponent) and first_child.type == "text":
                    prop = {"type": 'text', "content": first_child.text_content }
                    component_dict["props"] = prop
            self._components.append(component_dict)
        
        return component

    def __getattr__(self, element: str):
        if not element.startswith('__'):
            self._order_counter += 1
            component_name = f"{element}_{self._order_counter}"
            print(component_name)

            component_info = {
                'id': self._order_counter,
                'component': component_name,
                'order': self._order_counter,
                'props_updated': False,
                'props': {},
                'parent_id': None if not self._stack else self._stack[-1].unique_id
            }
            self._component_sequence.append(component_info)

        def component_creator(*args, **props):
            return self.create_component(element, *args, **props)
            
        return component_creator
