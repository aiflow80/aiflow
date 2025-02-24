import inspect
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiflow import mui

class ComponentSender:
    def __init__(self):
        self.component_stack = []

    def send_component(self, component):
        self.component_stack.append(component)
        if hasattr(component, '__enter__'):
            with component:
                yield from self.send_component_children(component)
        else:
            yield component
        self.component_stack.pop()

    def send_component_children(self, component):
        if hasattr(component, 'children'):
            for child in component.children:
                yield from self.send_component(child)
        elif hasattr(component, '__dict__'):
            for key, value in component.__dict__.items():
                if isinstance(value, list):
                    for item in value:
                        yield from self.send_component(item)
                elif hasattr(value, '__enter__') or hasattr(value, '__dict__'):
                    yield from self.send_component(value)

    def send_components(self, component_func):
        frame = inspect.currentframe().f_back
        component_tree = None
        for line in inspect.getframeinfo(frame).code_context:
            if 'component_func' in line:
                component_tree = eval(line.split('=')[1].strip(), frame.f_globals, frame.f_locals)
                break
        yield from self.send_component(component_tree)

# Usage:
sender = ComponentSender()

def card_component():
    with mui.Grid(container=True, spacing=2):
        with mui.Grid(item=True, xs=12, sm=6, md=3):
            with mui.Card(
                sx={
                    "display": "flex",
                    "flexDirection": "column",
                    "borderRadius": 3,
                    "overflow": "hidden",
                },
                elevation=1
            ):
                mui.CardHeader(
                    title="Shrimp and Chorizo Paella",
                    subheader="September 14, 2016",
                    avatar=mui.Avatar("R", sx={"bgcolor": "red"}),
                    action=mui.IconButton(mui.icon.MoreVert),
                )

                mui.CardMedia(
                    component="img",
                    height=294,
                    image="https://mui.com/static/images/cards/paella.jpg",
                    alt="Paella dish",
                )
                
                with mui.CardContent(sx={"flex": 1}):
                    mui.Typography(
                        "This impressive paella is a perfect party dish and a fun meal to cook together "
                        "with your guests. Add 1 cup of frozen peas along with the mussels, if you like."
                    )

# Send the components to the frontend
for component in sender.send_components(card_component()):
    print(component)
