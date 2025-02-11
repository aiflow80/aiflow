import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiflow import mui

print("hello")

with mui.Grid(container=True, spacing=2):
    with mui.Grid(item=True, xs=12):
        mui.Typography("Chat Application", variant="h4", sx={"mb": 2})