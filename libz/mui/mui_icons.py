from .mui_component import MUIComponent

class MUIIcons:
    def __init__(self, builder):
        self._builder = builder

    def __getattr__(self, element):
        def icon_factory(**props):
            # Create icon with props
            icon = MUIComponent(element, module="muiIcons", props=props, builder=self._builder)
            
            # Store original __call__ method
            original_call = icon.__call__
            
            def enhanced_call(*args, **kwargs):
                # Merge any new props from the call
                if kwargs:
                    for key, value in kwargs.items():
                        icon.props[key] = value
                        print(f"Icon {element}: Setting prop {key} = {value}")
                
                # Call original method
                result = original_call(*args, **kwargs)
                return result
            
            # Replace the __call__ method
            icon.__call__ = enhanced_call
            
            return icon
        return icon_factory
