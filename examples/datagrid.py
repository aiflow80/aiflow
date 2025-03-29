import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from aiflow import mui, logger
from aiflow.mui.custom_components import data_grid
from aiflow.events import events, state
from aiflow.mui.datagrid_utils import create_data_grid_from_df

import io

def datagridcard():
    # State management for uploaded data
    file_event = events.get("csv_upload", {})

    # Handle file upload event
    if file_event:
        try:
            # Get the file content from the event
            file_content = file_event.get('data', None)
            if file_content:
                # Convert base64 to bytes and create DataFrame
                import base64
                content = base64.b64decode(file_content.split(',')[1])
                df = pd.read_csv(io.BytesIO(content))
                state['df'] = df
                
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")

    with mui.Card(sx={"p": 2}):
        with mui.CardHeader(
            title=mui.Typography("Data Grid", variant="h4"),
            action=mui.Button(
                "Upload CSV",
                variant="contained",
                startIcon=mui.icon.Upload(),
                component="label",
                sx={"mt": 1}
            )(
                mui.Input(
                    type="file",
                    id="csv_upload",
                    inputProps={
                        "accept": ".csv",
                        "multiple": False,
                    },
                    sx={"display": "none"},
                    disableUnderline=True,  # Add this
                )
            ),
            sx={"pb": 0}
        ):
            pass

        with mui.CardContent(sx={"pt": 2}):
            # Display DataGrid if data is available
            if state.get('df') is not None:
                df = state['df']
                
                with mui.Box(
                    create_data_grid_from_df(df, grid_id="my-grid")
                ): pass

                mui.Button("Submit", id="submit-button", type="submit", variant="contained", color="primary", sx={"marginTop": "20px", "marginBottom": "10px", "float": "right"})
        
            else:
                mui.Typography(
                    "Upload a CSV file to display data",
                    sx={"textAlign": "center"}
                )

def dashboard():
        with mui.Grid(container=True, spacing=2):
            # First row
            # Third row - DataGrid
            with mui.Grid(item=True, xs=12):
                datagridcard()

if __name__ == "__main__":
    dashboard()
    logger.info("Dashboard loaded successfully.")
