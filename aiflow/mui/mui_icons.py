from .mui_component import MUIComponent

class MUIIcons:
    def __init__(self, builder):
        self._builder = builder

    def __getattr__(self, element):
        def icon_factory(**props):
            return MUIComponent(element, module="muiIcons", props=props, builder=self._builder)
        return icon_factory
