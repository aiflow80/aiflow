import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from libz import mui, events_store


# Card container for the form
with mui.Card(variant="outlined", sx={"padding": "16px", "maxWidth": "100%", "margin": "0 auto"}):

    # Additional fields using Paper for organization
    with mui.Paper(variant="outlined", sx={"padding": "10px", "marginTop": "20px", "marginBottom": "10px"}):
        mui.Typography("Additional Information", id="additional-info-title", variant="h6", gutterBottom=True) 
        
    if events_store.get('events'):
        mui.Typography(str(events_store), variant="body2", sx={"whiteSpace": "pre-wrap", "fontFamily": "monospace"})

    mui.Button("Submit", id="submit-button", type="submit", variant="contained", color="primary", sx={"marginTop": "20px", "marginBottom": "10px", "float": "center"})
        
