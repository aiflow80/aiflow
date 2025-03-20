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
        # Create icon component
        icon = MUIComponent(icon_name, module="muiIcons", props={}, builder=self._builder)
        
        # Override __call__ to capture props
        original_call = icon.__call__
        
        def enhanced_call(*args, **kwargs):
            # Update props if provided
            if kwargs:
                for key, value in kwargs.items():
                    icon.props[key] = value
                    
            # Call original method
            return original_call(*args, **kwargs)
            
        # Replace __call__ method
        icon.__call__ = enhanced_call
        
        return icon

class MUIBuilder:
    def __init__(self):
        self._stack: List[MUIComponent] = []
        self._roots: List[MUIComponent] = []
        self._icons = MUIIcons(self)
        self._id_counter = 1
        self.icon = MUIIconAccess(self)
        self._component_sequence = []
        self._components = []
        self._order_counter = 0
        self._current_parent_id = 0
        self._component_hierarchy = {}
        self._current_parent = None

    def get_next_id(self) -> int:
        """Get next sequential ID starting from 0 (or 1)"""
        current_id = self._id_counter
        self._id_counter += 1
        return current_id

    @property
    def icons(self):
        return self._icons

    def _process_args(self, args: tuple) -> List[MUIComponent]:
        """Convert arguments to components or text components"""
        processed = []
        for arg in args:
            if isinstance(arg, (str, int, float)):
                text_component = MUIComponent(str(arg), module="text", builder=self)
                processed.append(text_component)
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
                value._prop_key = key  # Store the prop key for special component identification
                if self._stack:
                    value._parent = self._stack[-1]
                    value._parent_id = f"{self._stack[-1].type}_{self._stack[-1].unique_id}"
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
                break

    def _component_exists_in_array(self, comp: Dict[str, Any], array: List[Dict[str, Any]]) -> bool:
        """Check if a component with the same ID already exists in the array"""
        if not comp or not array:
            return False
            
        comp_id = comp.get('id')
        return any(item.get('id') == comp_id for item in array)

    def _build_complete_component_structure(self, component_dict: Dict[str, Any], props: Dict[str, Any]) -> None:
        """Build a complete nested structure of the component including all props"""
        if "children" not in component_dict:
            component_dict["children"] = []
        
        # Identify special component props
        special_component_props = {}
        component_type = component_dict.get("type")
        if component_type in MUIComponent._special_component_props:
            special_prop_keys = MUIComponent._special_component_props[component_type]
        else:
            special_prop_keys = []
            
        # Store the prop keys that contain MUI components - we'll track these to avoid duplication
        mui_component_props = {}
            
        for key, value in props.items():
            if isinstance(value, MUIComponent):
                prop_dict = value.to_dict()
                prop_dict["parentId"] = component_dict["id"]
                
                # Store component ID by prop key to track it
                mui_component_props[key] = prop_dict["id"]
                
                # Special handling for components with special props
                # If this is a special prop, include it in props instead of children
                is_special_prop = key in special_prop_keys
                
                # Only add to children if it's not a special prop
                if not is_special_prop and not self._component_exists_in_array(prop_dict, component_dict["children"]):
                    component_dict["children"].append(prop_dict)
                
                if value.text_content is not None:
                    text_id = f"text_{value.unique_id}"
                    if "children" not in prop_dict:
                        prop_dict["children"] = []
                    
                    text_component = {
                        "type": "text",
                        "id": text_id,
                        "content": value.text_content,
                        "parentId": prop_dict["id"]
                    }
                    
                    # Only add text component if it doesn't already exist
                    if not self._component_exists_in_array(text_component, prop_dict["children"]):
                        prop_dict["children"].append(text_component)
                    
                    prop_dict["content"] = value.text_content
                
                if hasattr(value, 'props') and value.props:
                    self._build_complete_component_structure(prop_dict, value.props)
                
                if hasattr(value, 'children') and value.children:
                    if "children" not in prop_dict:
                        prop_dict["children"] = []
                    
                    for child in value.children:
                        if isinstance(child, MUIComponent):
                            child_dict = child.to_dict()
                            child_dict["parentId"] = prop_dict["id"]
                            
                            # Only add if it doesn't already exist
                            if not self._component_exists_in_array(child_dict, prop_dict["children"]):
                                prop_dict["children"].append(child_dict)
                        elif isinstance(child, dict) and child.get("type") == "text":
                            child["parentId"] = prop_dict["id"]
                            
                            # Only add if it doesn't already exist
                            if not self._component_exists_in_array(child, prop_dict["children"]):
                                prop_dict["children"].append(child)

        # For special component props, ensure they're in the props instead of children
        if special_prop_keys:
            for key in special_prop_keys:
                if key in props and isinstance(props[key], MUIComponent):
                    component_dict["props"][key] = props[key].to_dict()
        
        # Remove MUI component objects from props that are not special
        # We'll keep only primitive values, non-MUI objects, and special props
        filtered_props = {}
        for key, value in props.items():
            if not isinstance(value, MUIComponent) or key in special_prop_keys:
                if isinstance(value, MUIComponent) and key in special_prop_keys:
                    # For special props, use the processed component dict
                    filtered_props[key] = value.to_dict()
                else:
                    filtered_props[key] = value
        
        # Update the props in the component dictionary
        component_dict["props"] = filtered_props

    def _update_parent_ids(self, component: MUIComponent) -> None:
        """
        Recursively update parent IDs for a component and all its children
        to ensure the component hierarchy is correctly represented.
        """
        # Find the component in our components list
        component_id = f"{component.type}_{component.unique_id}"
        component_dict = None
        
        for comp in self._components:
            if comp.get('id') == component_id:
                component_dict = comp
                break
        
        if not component_dict:
            return
            
        # Update parent IDs for all children
        if hasattr(component, 'children') and component.children:
            for child in component.children:
                if isinstance(child, MUIComponent):
                    child_id = f"{child.type}_{child.unique_id}"
                    
                    # Update parent ID in the child's stored dictionary
                    self._update_child_parent_id(child_id, component_id)
                    
                    # Recursively update the child's children
                    self._update_parent_ids(child)
    
    def _update_child_parent_id(self, child_id: str, parent_id: str) -> None:
        """Update the parentId for a specific component in the components list"""
        # First look in main components list
        for comp in self._components:
            if comp.get('id') == child_id:
                comp['parentId'] = parent_id
                
                # Also update in children arrays of all components
                self._update_parent_id_in_children(self._components, child_id, parent_id)
                return
    
    def _update_parent_id_in_children(self, components_list: List[Dict[str, Any]], 
                                     child_id: str, parent_id: str) -> None:
        """Recursively search through component children to update parentId"""
        for comp in components_list:
            if comp.get('children'):
                for child in comp.get('children'):
                    if child.get('id') == child_id:
                        child['parentId'] = parent_id
                    
                    # Continue recursion if this child has children
                    if child.get('children'):
                        self._update_parent_id_in_children(child.get('children'), child_id, parent_id)

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
            component._parent_id = current_parent_id
        
        # Process props that are components
        for key, prop_value in processed_props.items():
            if isinstance(prop_value, MUIComponent):
                prop_value._parent = component
                prop_value._parent_id = f"{component.type}_{component.unique_id}"
                prop_value._is_prop_component = True
                prop_value._prop_key = key
        
        # Create component info
        component_info = {
            'id': self._order_counter,
            'component': component.name,
            'order': self._order_counter,
            'props_updated': False,
            'props': processed_props,
            'parent_id': current_parent_id,
            'children': []
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

        # Create component dict
        component_dict = component.to_dict()

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

        # Process prop components
        self._build_complete_component_structure(component_dict, processed_props)

        # Add tracking for __call__ parent changes
        component._original_add_child = component.add_child
        
        def wrapped_add_child(child):
            # Call the original method first
            component._original_add_child(child)
            
            # Now update the component dicts to reflect the new parent relationship
            child_id = f"{child.type}_{child.unique_id}"
            parent_id = f"{component.type}_{component.unique_id}"
            
            # Check if child exists in components list and preserve its props
            child_found = False
            child_props = {}
            
            for comp in self._components:
                if comp.get('id') == child_id:
                    child_found = True
                    if 'props' in comp:
                        child_props = comp.get('props', {})
                    comp['parentId'] = parent_id
                    break
            
            # If child not found, add it with correct parent
            if not child_found:
                child_dict = child.to_dict()
                child_dict['parentId'] = parent_id
                self._components.append(child_dict)
            
            # Send the updated child through event system
            for comp in self._components:
                if comp.get('id') == child_id:
                    # Ensure props are preserved
                    if not comp.get('props') and hasattr(child, 'props'):
                        comp['props'] = child.props
                    
                    event_base.send_response_sync({
                        "type": "component_update",
                        "payload": {
                            "component": comp,
                            "timestamp": time.time()
                        }
                    })
                    print(f"wrapped comp {comp['id'], comp['parentId']} send to sequence.")
                    break
        
        # Replace the add_child method with our wrapped version
        component.add_child = wrapped_add_child

        # Check for unupdated props before appending
        if not [item for item in self._component_sequence if not item['props_updated']]:
            self._components.append(component_dict)
            event_base.send_response_sync({
                "type": "component_update",
                "payload": {
                    "component": component_dict,
                    "timestamp": time.time()
                }
            })

            print(f"Component {component_dict['id'], component_dict['parentId']} send to sequence.")

        return component
    
    def __getattr__(self, element: str):
        if not element.startswith('__'):
            self._order_counter += 1
            component_name = f"{element}_{self._order_counter}"
            
            current_parent = None if not self._stack else f"{self._stack[-1].type}_{self._stack[-1].unique_id}"
            self._component_sequence.append({
                'id': self._order_counter,
                'type': element,
                'component': component_name,
                'order': self._order_counter,
                'props_updated': False,
                'props': {},
                'parent_id': None if not self._stack else self._stack[-1].unique_id,
                'children': []
            })

        def component_creator(*args, **props):
            return self.create_component(element, *args, **props)
            
        return component_creator
