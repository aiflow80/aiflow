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
        comp = MUIComponent(element, props=props, builder=self)
        if args:
            comp.children.extend(args)
        if len(self._stack) > 0:
            parent = self._stack[-1]
            comp._parent = parent
            if comp not in parent.children:
                parent.children.append(comp)
        elif self.root is None:
            self.root = comp
        return comp

    def __getattr__(self, element):
        def component_factory(*args, **props):
            if 'with' in props:
                del props['with']
                return MUIComponent(element, props=props, children=list(args) if args else [], builder=self)
            return self.create_component(element, *args, **props)
        return component_factory

    def build(self) -> Dict[str, Any]:
        return self.root.to_dict() if self.root else {}
