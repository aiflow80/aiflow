import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiflow import mui
from aiflow.events import events_store  # Direct import of the events dictionary

# Card container for the form
with mui.Card(variant="outlined", sx={"padding": "16px", "maxWidth": "100%", "margin": "0 auto"}):
    
    # Form title using Typography
    mui.Typography("User Registration Form", variant="h4", gutterBottom=True)

    # Profile Avatar
    mui.Avatar("A", sx={"width": 80, "height": 80, "marginBottom": "20px"})

    if events_store.get('events'):
        with mui.Box(sx={"marginTop": "40px", "padding": "16px",  "borderRadius": "4px"}):
            mui.Typography("Event Store Contents:", variant="h6", gutterBottom=True)
            mui.Typography(str(events_store), variant="body2", sx={"whiteSpace": "pre-wrap", "fontFamily": "monospace"})

    mui.Button("Submit", id="submit-button", type="submit", variant="contained", color="primary", sx={"marginTop": "20px", "marginBottom": "10px", "float": "center"})
        
