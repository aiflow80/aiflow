from .mui_builder import MUIBuilder

mui = MUIBuilder()  # Create instance here

__all__ = ['mui']

from dataclasses import dataclass
from typing import Any, Optional, List, Dict

@dataclass
class MuiComponent:
    type: str
    props: Dict[str, Any] = None
    children: List[Any] = None

    def __post_init__(self):
        self.props = self.props or {}
        self.children = self.children or []

# Basic MUI components
def Button(props: Dict[str, Any] = None, children: List[Any] = None) -> MuiComponent:
    return MuiComponent("Button", props, children)

def TextField(props: Dict[str, Any] = None) -> MuiComponent:
    return MuiComponent("TextField", props)

def Container(props: Dict[str, Any] = None, children: List[Any] = None) -> MuiComponent:
    return MuiComponent("Container", props, children)

__all__ += ['Button', 'TextField', 'Container', 'MuiComponent']
