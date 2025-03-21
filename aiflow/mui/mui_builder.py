import time
import logging
from typing import List, Dict, Any, Set, Optional, Union, Callable, TypeVar

from aiflow.mui.mui_component import MUIComponent
from aiflow.mui.mui_icons import MUIIcons
from aiflow.events import event_base

# Set up logging
logger = logging.getLogger(__name__)

T = TypeVar('T', bound=MUIComponent)

class MUIIconAccess:
    """Provides direct access to MUI icons without parentheses"""
    def __init__(self, builder):
        self._builder = builder

    def __getattr__(self, icon_name: str) -> MUIComponent:
        # Create icon component
        icon = MUIComponent(icon_name, module="muiIcons", props={}, builder=self._builder)
        
        # Create enhanced call method to capture props
        def enhanced_call(*args, **kwargs):
            # Update props if provided
            if kwargs:
                icon.props.update(kwargs)
            return icon.__call__(*args, **kwargs)
            
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
                processed.append(MUIComponent(str(arg), module="text", builder=self))
            elif isinstance(arg, MUIComponent) and not hasattr(arg, '_is_prop'):
                processed.append(arg)
        return processed

    def _process_props(self, props: dict) -> dict:
        """Process and mark prop components"""
        processed = {}
        for key, value in props.items():
            if isinstance(value, MUIComponent):
                # Mark as property component
                value._is_prop = True
                value._skip_update = True
                value._prop_key = key
                
                # Set parent relationship if available
                if self._stack:
                    value._parent = self._stack[-1]
                    value._parent_id = self._get_component_id(self._stack[-1])
            processed[key] = value
        return processed

    def _get_component_id(self, component: MUIComponent) -> str:
        """Get standardized component ID"""
        return f"{component.type}_{component.unique_id}"

    def _update_component_sequence(self, component_type: str, component_dict: dict, 
                                  processed_props: dict, processed_children: list, 
                                  current_parent_id: str) -> None:
        """Update component in the sequence tracking"""
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
        
        # Track MUI component props
        mui_component_props = {}
            
        # Process each prop
        for key, value in props.items():
            if isinstance(value, MUIComponent):
                self._process_component_prop(component_dict, key, value, mui_component_props)
        
        # Process special props
        self._process_special_props(component_dict, props)

    def _process_component_prop(self, component_dict: Dict[str, Any], key: str, 
                               value: MUIComponent, mui_component_props: Dict[str, str]) -> None:
        """Process a component that's being used as a prop"""
        prop_dict = value.to_dict()
        prop_dict["parentId"] = component_dict["id"]
        
        # Store component ID by prop key
        mui_component_props[key] = prop_dict["id"]
        
        # Determine if this is a special prop component
        is_special_prop = hasattr(value, '_is_prop_component') and value._is_prop_component
        
        # Only add to children if it's not a special prop
        if not is_special_prop and not self._component_exists_in_array(prop_dict, component_dict["children"]):
            component_dict["children"].append(prop_dict)
        
        # Handle text content
        self._handle_text_content(prop_dict, value)
        
        # Handle nested props
        if hasattr(value, 'props') and value.props:
            self._build_complete_component_structure(prop_dict, value.props)
        
        # Handle children
        self._handle_prop_children(prop_dict, value)

    def _handle_text_content(self, prop_dict: Dict[str, Any], component: MUIComponent) -> None:
        """Handle text content for a component"""
        if component.text_content is not None:
            text_id = f"text_{component.unique_id}"
            if "children" not in prop_dict:
                prop_dict["children"] = []
            
            text_component = {
                "type": "text",
                "id": text_id,
                "content": component.text_content,
                "parentId": prop_dict["id"]
            }
            
            # Only add text component if it doesn't already exist
            if not self._component_exists_in_array(text_component, prop_dict["children"]):
                prop_dict["children"].append(text_component)
            
            prop_dict["content"] = component.text_content

    def _handle_prop_children(self, prop_dict: Dict[str, Any], component: MUIComponent) -> None:
        """Handle children of a component prop"""
        if hasattr(component, 'children') and component.children:
            if "children" not in prop_dict:
                prop_dict["children"] = []
            
            for child in component.children:
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

    def _process_special_props(self, component_dict: Dict[str, Any], props: Dict[str, Any]) -> None:
        """Process special prop components and update the component's props"""
        filtered_props = {}
        for key, value in props.items():
            if not isinstance(value, MUIComponent) or (hasattr(value, '_is_prop_component') and value._is_prop_component):
                if isinstance(value, MUIComponent) and hasattr(value, '_is_prop_component') and value._is_prop_component:
                    # For special props, use the processed component dict
                    filtered_props[key] = value.to_dict()
                else:
                    filtered_props[key] = value
        
        # Update the props in the component dictionary
        component_dict["props"] = filtered_props

    def _update_parent_ids(self, component: MUIComponent) -> None:
        """Recursively update parent IDs for component hierarchy"""
        component_id = self._get_component_id(component)
        component_dict = next((c for c in self._components if c.get('id') == component_id), None)
        
        if not component_dict:
            return
            
        # Update parent IDs for all children
        if hasattr(component, 'children') and component.children:
            for child in component.children:
                if isinstance(child, MUIComponent):
                    child_id = self._get_component_id(child)
                    self._update_child_parent_id(child_id, component_id)
                    self._update_parent_ids(child)
    
    def _update_child_parent_id(self, child_id: str, parent_id: str) -> None:
        """Update parentId for a component in the component tree"""
        # Update in main components list
        for comp in self._components:
            if comp.get('id') == child_id:
                comp['parentId'] = parent_id
                # Update in children arrays
                self._update_parent_id_in_children(self._components, child_id, parent_id)
                return
    
    def _update_parent_id_in_children(self, components_list: List[Dict[str, Any]], 
                                     child_id: str, parent_id: str) -> None:
        """Recursively update parentId in component children"""
        for comp in components_list:
            if comp.get('children'):
                for child in comp.get('children'):
                    if child.get('id') == child_id:
                        child['parentId'] = parent_id
                    
                    # Recursive update
                    if child.get('children'):
                        self._update_parent_id_in_children(child.get('children'), child_id, parent_id)

    def _create_wrapped_add_child(self, component: MUIComponent) -> Callable[[MUIComponent], None]:
        """Create a wrapped add_child method for a component"""
        original_add_child = component.add_child
        
        def wrapped_add_child(child: MUIComponent) -> None:
            # Call original method
            original_add_child(child)
            
            # Update component relationships
            child_id = self._get_component_id(child)
            parent_id = self._get_component_id(component)
            
            # Update or add child in components list
            child_found = self._update_existing_child(child_id, parent_id, child)
            
            if not child_found:
                self._add_new_child(child, parent_id)
            
            # Send update event
            self._send_component_update(child_id)
        
        return wrapped_add_child

    def _update_existing_child(self, child_id: str, parent_id: str, child: MUIComponent) -> bool:
        """Update existing child in components list"""
        for comp in self._components:
            if comp.get('id') == child_id:
                if 'props' in comp and hasattr(child, 'props'):
                    # Preserve existing props
                    pass
                comp['parentId'] = parent_id
                return True
        return False
    
    def _add_new_child(self, child: MUIComponent, parent_id: str) -> None:
        """Add new child to components list"""
        child_dict = child.to_dict()
        child_dict['parentId'] = parent_id
        self._components.append(child_dict)
    
    def _send_component_update(self, component_id: str) -> None:
        """Send component update event"""
        for comp in self._components:
            if comp.get('id') == component_id:
                # Ensure props are preserved
                if not comp.get('props') and hasattr(comp, 'props'):
                    comp['props'] = comp.props
                
                event_base.send_response_sync({
                    "type": "component_update",
                    "payload": {
                        "component": comp,
                        "timestamp": time.time()
                    }
                })
                # logger.debug(f"Component {comp['id']} with parent {comp.get('parentId')} sent to sequence")
                break

    def create_component(self, element: str, *args, **props) -> MUIComponent:
        """Create a Material UI component with the given properties and children"""
        # Process props and children
        processed_props = self._process_props(props)
        processed_children = self._process_args(args)
        
        # Create the component
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
            current_parent_id = self._get_component_id(parent)
            component._parent = parent
            component._parent_id = current_parent_id
        
        # Process prop components
        for key, prop_value in processed_props.items():
            if isinstance(prop_value, MUIComponent):
                prop_value._parent = component
                prop_value._parent_id = self._get_component_id(component)
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

        # Update parent's children
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

        # Build component dict
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

        # Create wrapped add_child method
        component.add_child = self._create_wrapped_add_child(component)

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
            logger.debug(f"Component {component_dict['id']} with parent {component_dict.get('parentId')} sent to sequence")

        return component
    
    def __getattr__(self, element: str):
        """Dynamic component factory method"""
        if not element.startswith('__'):
            self._order_counter += 1
            component_name = f"{element}_{self._order_counter}"
            
            current_parent = None if not self._stack else self._get_component_id(self._stack[-1])
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
