from typing import List, Dict, Any
from .mui_component import MUIComponent
from .mui_icons import MUIIcons

class MUIBuilder:
    def __init__(self):
        self._stack: List[MUIComponent] = []
        self.root = None
        self._icons = MUIIcons(self)
        self._id_counter = 0

    def get_next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    @property
    def icons(self):
        return self._icons

    def create_component(self, element: str, *args, **props) -> MUIComponent:
        # Process text arguments first
        text_children = []
        for arg in args:
            if isinstance(arg, (str, int, float)):
                text_comp = MUIComponent(str(arg), module="text", builder=self)
                text_children.append(text_comp)
            else:
                text_children.append(arg)

        # Create main component
        comp = MUIComponent(
            element, 
            module="muiElements", 
            props=props, 
            children=text_children,  # Add children directly
            builder=self
        )

        # Set parent relationships
        for child in text_children:
            child._parent = comp

        # Handle stacking
        if len(self._stack) > 0:
            parent = self._stack[-1]
            comp._parent = parent
            parent.children.append(comp)

        # Print state immediately after children are added
        comp._component_creation()

        return comp

    def __getattr__(self, element):
        def component_factory(*args, **props):
            return self.create_component(element, *args, **props)
        return component_factory

    def build(self) -> Dict[str, Any]:
        return self.root.to_dict() if self.root else {}
