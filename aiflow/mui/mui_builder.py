from typing import List, Dict, Any
from .mui_component import MUIComponent
from .mui_icons import MUIIcons

class MUIIconAccess:
    def __init__(self, builder):
        self._builder = builder

    def __getattr__(self, element):
        # Return an MUIComponent without needing parentheses
        return MUIComponent(element, module="muiIcons", builder=self._builder)

class MUIBuilder:
    def __init__(self):
        self._stack: List[MUIComponent] = []
        self._roots: List[MUIComponent] = []
        self._icons = MUIIcons(self)
        self._id_counter = 0

    def get_next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    @property
    def icons(self):
        return self._icons

    @property
    def icon(self):
        return MUIIconAccess(self)

    def create_component(self, element: str, *args, **props) -> MUIComponent:
        # Process props but don't create components yet
        processed_props = {}
        for key, value in props.items():
            if isinstance(value, MUIComponent):
                value._is_prop = True
                processed_props[key] = value
            else:
                processed_props[key] = value

        # Create main component
        comp = MUIComponent(
            element, 
            module="muiElements", 
            props=processed_props, 
            builder=self
        )

        # Process children
        for arg in args:
            if isinstance(arg, (str, int, float)):
                text_comp = MUIComponent(str(arg), module="text", builder=self)
                comp.children.append(text_comp)
            elif isinstance(arg, MUIComponent):
                if not hasattr(arg, '_is_prop'):
                    comp.children.append(arg)

        # Only create component tree for non-prop components
        if not hasattr(comp, '_is_prop'):
            comp._component_creation()

        return comp

    def __getattr__(self, element):
        def component_factory(*args, **props):
            return self.create_component(element, *args, **props)
        return component_factory

    def __exit__(self, exc_type, exc_val, exc_tb):
        # When the stack is about to become empty, treat the current component as a root
        if len(self._stack) == 1:
            self._roots.append(self._stack.pop())
        else:
            self._stack.pop()
        return False

    def build(self) -> List[Dict[str, Any]]:
        # Return an array of root components, matching c.json's top-level list
        return [root.to_dict() for root in self._roots]
