import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiflow import mui, events_store


# Card container for the form
with mui.Card(variant="outlined", sx={"padding": "16px", "maxWidth": "100%", "margin": "0 auto"}):
    
    # Form title using Typography
    mui.Typography("User Registration Form", variant="h4", gutterBottom=True)

# # Form title using Typography
with mui.RadioGroup(defaultValue="female", id="gender", sx={"marginBottom": "15px"}):
    mui.FormControlLabel(value="female", control=mui.Radio(), label="Female")
    mui.FormControlLabel(value="male", control=mui.Radio(), label="Male")
