import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiflow import mui
from aiflow.events import events_store  # Direct import of the events dictionary

# # Form title using Typography
with mui.RadioGroup(defaultValue="female", id="gender", sx={"marginBottom": "15px"}):
    mui.FormControlLabel(value="female", control=mui.Radio(), label="Female")
    mui.FormControlLabel(value="male", control=mui.Radio(), label="Male")
    mui.FormControlLabel(value="other", control=mui.Radio(), label="Other")

print("hello")