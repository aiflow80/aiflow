import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiflow import mui
from aiflow.events import events_store  # Direct import of the events dictionary

# Form title using Typography
mui.Typography("User Registration Form", variant="h4", gutterBottom=True)

if events_store.get('events'):
    mui.Typography(str(events_store), variant="body2", sx={"whiteSpace": "pre-wrap", "fontFamily": "monospace"})

mui.Button("Submit", id="submit-button", type="submit", variant="contained", color="primary", sx={"marginTop": "20px", "marginBottom": "10px", "float": "center"})
        
