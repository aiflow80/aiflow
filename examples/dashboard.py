import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from aiflow import mui
import io

def earningcard():
    with mui.Card(
        sx={
            "backgroundColor": "primary.main",
            "color": "#fff",
            "overflow": "hidden",
            "position": "relative",
            "&:after": {
                "content": '""',
                "position": "absolute",
                "width": 210,
                "height": 210,
                "background": "linear-gradient(210.04deg, #90CAF9 -50.94%, rgba(144, 202, 249, 0) 83.49%)",
                "borderRadius": "50%",
                "top": -85,
                "right": -95,
                "@media (max-width: 600px)": {  # sm breakpoint
                    "top": -105,
                    "right": -140
                }
            },
            "&:before": {
                "content": '""',
                "position": "absolute",
                "width": 210,
                "height": 210,
                "background": "linear-gradient(140.9deg, #90CAF9 -14.02%, rgba(144, 202, 249, 0) 77.58%)",
                "borderRadius": "50%",
                "top": -125,
                "right": -15,
                "opacity": 0.5,
                "@media (max-width: 600px)": {  # sm breakpoint
                    "top": -155,
                    "right": -70
                }
            }
        }
    ):
        with mui.Box(sx={"p": 2.25}):
            with mui.Grid(container=True, direction="column"):
                # First row with avatars
                with mui.Grid(item=True):
                    with mui.Grid(container=True, justifyContent="space-between"):
                        with mui.Grid(item=True):
                            mui.Avatar("AA",
                                variant="rounded",
                                sx={
                                    "backgroundColor": "primary.main",
                                    "mt": 1,
                                    "width": 56,
                                    "height": 56,
                                },
                            )
                        with mui.Grid(item=True):
                            mui.Avatar(
                                variant="rounded",
                                sx={
                                    "backgroundColor": "primary.main",
                                    "color": "primary.800",
                                    "zIndex": 1,
                                    "width": 40,
                                    "height": 40,
                                },
                                # Add onClick event handler if needed
                            )(mui.IconButton(mui.icon.MoreHoriz(sx={"transform": "rotate(45deg)"})))

                # Second row with amount and icon
                with mui.Grid(item=True):
                    with mui.Grid(container=True, alignItems="center"):
                        mui.Typography(
                            "$500.00",
                            sx={
                                "fontSize": "2.125rem",
                                "fontWeight": 500,
                                "mr": 1,
                                "mt": 1.25,
                                "mb": 0.75,
                            },
                        )
                        mui.Avatar(
                            sx={
                                "backgroundColor": "primary.main",
                                "width": 30,
                                "height": 30,
                            },
                        )(mui.icon.ArrowUpward(sx={"transform": "rotate(45deg)"}))
                # Third row with description
                with mui.Grid(item=True, sx={"mb": 1.25}):
                    mui.Typography(
                        "Total Earning",
                        sx={
                            "fontSize": "1rem",
                            "fontWeight": 500,
                            "mb": 1.75,
                        },
                    )

def totalorderlinechartcard():
    # Create session state for time value if it doesn't exist
    with mui.Card(
        sx={
            "backgroundColor": "primary.main",
            "color": "#fff",
            "overflow": "hidden",
            "position": "relative",
            "&:after": {
                "content": '""',
                "position": "absolute",
                "width": 210,
                "height": 210,
                "background": "linear-gradient(210.04deg, #90CAF9 -50.94%, rgba(144, 202, 249, 0) 83.49%)",
                "borderRadius": "50%",
                "top": -85,
                "right": -95,
                "@media (max-width: 600px)": {  # sm breakpoint
                    "top": -105,
                    "right": -140
                }
            },
            "&:before": {
                "content": '""',
                "position": "absolute",
                "width": 210,
                "height": 210,
                "background": "linear-gradient(140.9deg, #90CAF9 -14.02%, rgba(144, 202, 249, 0) 77.58%)",
                "borderRadius": "50%",
                "top": -125,
                "right": -15,
                "opacity": 0.5,
                "@media (max-width: 600px)": {  # sm breakpoint
                    "top": -155,
                    "right": -70
                }
            }
        }
    ):
        with mui.Box(sx={"p": 2.25}):
            with mui.Grid(container=True, direction="column", spacing=0):  # Changed from {xs: 0} to 0
                # First row with avatar and buttons
                with mui.Grid(item=True):  # Reduce margi100n bottom
                    with mui.Grid(container=True, justifyContent="space-between"):
                        # Avatar section
                        with mui.Grid(item=True):
                            mui.Avatar(
                                variant="rounded",
                                sx={
                                    "backgroundColor": "primary.main",
                                    "color": "#fff",
                                    "mt": 0.4,
                                    "width": 56,
                                    "height": 56,
                                }
                            )(mui.icon.LocalMallOutlined())
                        
                        # Time toggle buttons - removed onClick handlers
                        with mui.Grid(item=True):
                            mui.Button(
                                "Month",
                                variant="contained",
                                size="small",
                                sx={"color": "inherit"}
                            )
                            mui.Button(
                                "Year",
                                variant="contained",
                                size="small",
                                sx={"color": "inherit"}
                            )

                # Second row with value and chart
                with mui.Grid(item=True):
                    with mui.Grid(container=True, alignItems="center", spacing=1):  # Changed from {xs: 1} to 1
                        # Left side - value and icon
                        with mui.Grid(item=True, xs=6):
                            with mui.Grid(container=True, alignItems="center"):
                                with mui.Grid(item=True):
                                    mui.Typography(
                                        "$108",
                                        sx={
                                            "fontSize": "2.125rem",
                                            "fontWeight": 500,
                                            "mr": 1,
                                            "mt": 1.25,  
                                            "mb": 0.75,
                                        }
                                    )
                                with mui.Grid(item=True):
                                    mui.Avatar(
                                        sx={
                                            "cursor": "pointer",
                                            "backgroundColor": "primary.200",
                                            "width": 30,
                                            "height": 30,
                                        }
                                    )(mui.icon.ArrowDownward(
                                            sx={"transform": "rotate3d(1, 1, 1, 45deg)"}
                                        ))
                                with mui.Grid(item=True, xs=12):
                                    mui.Typography(
                                        "Total Order",
                                        sx={
                                            "fontSize": "1rem",
                                            "fontWeight": 500,
                                        },
                                    )
                        
                        # Right side - chart
                        with mui.Grid(item=True, xs=6):
                            mui.Box(
                                sx={
                                    "height": 55,  # Further reduce height
                                    "backgroundColor": "primary.800",
                                    "borderRadius": 1,
                                    "opacity": 0.5,
                                }
                            )

def totalincomedarkcard():
    with mui.Card(
        sx={
            "backgroundColor": "secondary.500",
            "color": "primary.light",
            "overflow": "hidden",
            "position": "relative",
            "&:after": {
                "content": '""',
                "position": "absolute",
                "width": 210,
                "height": 210,
                "background": "linear-gradient(210.04deg, #90CAF9 -50.94%, rgba(144, 202, 249, 0) 83.49%)",
                "borderRadius": "50%",
                "top": -30,
                "right": -180
            },
            "&:before": {
                "content": '""',
                "position": "absolute",
                "width": 210,
                "height": 210,
                "background": "linear-gradient(140.9deg, #90CAF9 -14.02%, rgba(144, 202, 249, 0) 77.58%)",
                "borderRadius": "50%",
                "top": -160,
                "right": -130
            }
        }
    ):
        with mui.Box(sx={"p": 1.6}):
            with mui.List(sx={"py": 0}):
                with mui.ListItem(alignItems="center", disableGutters=True, sx={"py": 0}):
                    with mui.ListItemAvatar():
                        mui.Avatar(
                            variant="rounded",
                            sx={
                                "backgroundColor": "secondary.dark",
                                "color": "#fff",
                                # Add typography common avatar styles if needed
                            }
                        )(mui.icon.TableChartOutlined(fontSize="inherit"))

                    with mui.ListItemText(
                        sx={
                            "py": 0,
                            "mt": 0.45,
                            "mb": 0.45
                        }
                    ):
                        mui.Typography("$205k", variant="h5", sx={"color": "#fff"})
                        mui.Typography(
                            "Total Income",
                            variant="subtitle2",
                            sx={
                                "color": "grey.100",
                                "mt": 0.5,
                                "mb": 1
                            }
                        )

def totalincomelightcard():
    with mui.Card(
        sx={
            "backgroundColor": "primary.main",
            "overflow": "hidden",
            "position": "relative",
            "&:after": {
                "content": '""',
                "position": "absolute",
                "width": 210,
                "height": 210,
                "background": "linear-gradient(210.04deg, #FF6B00 -50.94%, rgba(144, 202, 249, 0) 83.49%)",  # warning.dark color
                "borderRadius": "50%",
                "top": -30,
                "right": -180
            },
            "&:before": {
                "content": '""',
                "position": "absolute",
                "width": 210,
                "height": 210,
                "background": "linear-gradient(140.9deg, #FF6B00 -14.02%, rgba(144, 202, 249, 0) 70.50%)",  # warning.dark color
                "borderRadius": "50%",
                "top": -160,
                "right": -130
            }
        }
    ):
        # ...existing content remains the same...
        with mui.Box(sx={"p": 1.6}):
            with mui.List(sx={"py": 0}):
                with mui.ListItem(alignItems="center", disableGutters=True, sx={"py": 0}):
                    with mui.ListItemAvatar():
                        mui.Avatar(
                            variant="rounded",
                            sx={
                                "backgroundColor": "warning.light",
                                "color": "warning.dark"
                            }
                        )(mui.icon.StorefrontTwoTone())
                    with mui.ListItemText(
                        sx={
                            "py": 0,
                            "mt": 0.45,
                            "mb": 0.45
                        }
                    ):
                        mui.Typography("$203k", variant="h5")
                        mui.Typography(
                            "Total Income",
                            variant="subtitle2",
                            sx={
                                "color": "grey.500",
                                "mt": 0.5,
                                "mb": 1
                            }
                        )

def popularcard():
    with mui.Card():
        with mui.CardContent():
            with mui.Grid(container=True, spacing=3):
                # Header section
                with mui.Grid(item=True, xs=12):
                    with mui.Grid(container=True, alignContent="center", justifyContent="space-between"):
                        with mui.Grid(item=True):
                            mui.Typography("Popular Stocks", variant="h4")
                        with mui.Grid(item=True):
                            with mui.IconButton(
                                sx={
                                    "color": "primary.200",
                                    "cursor": "pointer"
                                }
                            ):
                                mui.icon.MoreHoriz()

                # Chart section
                with mui.Grid(item=True, xs=12, sx={"pt": "16px !important"}):
                    # Note: You'll need to implement BajajAreaChartCard equivalent
                    pass

                # Stocks list section
                with mui.Grid(item=True, xs=12):
                    # Bajaj Finery
                    with mui.Grid(container=True, direction="column"):
                        with mui.Grid(item=True):
                            with mui.Grid(container=True, alignItems="center", justifyContent="space-between"):
                                with mui.Grid(item=True):
                                    mui.Typography("Bajaj Finery", variant="subtitle1")
                                with mui.Grid(item=True):
                                    with mui.Grid(container=True, alignItems="center", justifyContent="space-between"):
                                        with mui.Grid(item=True):
                                            mui.Typography("$1839.00", variant="subtitle1")
                                        with mui.Grid(item=True):
                                            with mui.Avatar(
                                                variant="rounded",
                                                sx={
                                                    "width": 16,
                                                    "height": 16,
                                                    "borderRadius": "5px",
                                                    "backgroundColor": "success.light",
                                                    "color": "success.dark",
                                                    "ml": 2
                                                }
                                            ):
                                                mui.icon.KeyboardArrowUp()
                        with mui.Grid(item=True):
                            mui.Typography("10% Profit", variant="subtitle2", sx={"color": "success.dark"})
                    
                    mui.Divider(sx={"my": 1.5})

                    # TTML
                    with mui.Grid(container=True, direction="column"):
                        # Similar structure for TTML stock...
                        pass

                    mui.Divider(sx={"my": 1.5})

                    # Reliance
                    with mui.Grid(container=True, direction="column"):
                        # Similar structure for Reliance stock...
                        pass

                    mui.Divider(sx={"my": 1.5})

                    # Additional stocks...

        with mui.CardActions(sx={"p": 1.25, "pt": 0, "justifyContent": "center"}):
            with mui.Button(size="small", disableElevation=True):
                mui.Typography("View All")
                mui.icon.ChevronRight()

def totalgrowthbarchart():
    # If file doesn't exist, create sample data
    df = pd.DataFrame({
        'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'current_year': [2100, 2300, 2500, 2200, 2800, 3000,
                        2900, 3200, 3100, 3400, 3600, 3800],
        'previous_year': [1800, 1900, 2100, 1950, 2300, 2500,
                        2400, 2600, 2800, 2900, 3100, 3300]
    })

    data = [
        {
            'type': 'bar',
            'name': 'Current Year',
            'x': df['month'].tolist(),
            'y': df['current_year'].tolist(),
            # Remove hardcoded colors - will be handled by theme
        },
        {
            'type': 'bar',
            'name': 'Previous Year',
            'x': df['month'].tolist(),
            'y': df['previous_year'].tolist(),
            # Remove hardcoded colors - will be handled by theme
        }
    ]
    
    layout = {
        'barmode': 'group',
        'margin': {'t': 20, 'r': 20, 'l': 40, 'b': 40},
        'height': 400,
        'xaxis': {
            'ticks': 'outside',
            'showgrid': False,  # Hide grid lines
        },
        'yaxis': {
            'ticks': 'outside',
            'showgrid': False,  # Hide grid lines
        },
    }

    with mui.Card(
        sx={
            "display": "flex",
            "flexDirection": "column",
            "borderRadius": 3,
            "overflow": "hidden",
        },
    ):
        with mui.CardHeader(
            sx={"p": 2}
        ):
            with mui.Grid(container=True, alignItems="center", justifyContent="space-between"):
                with mui.Grid(item=True):
                    with mui.Grid(container=True, direction="column", spacing=1):
                        with mui.Grid(item=True):
                            mui.Typography("Total Growth", variant="h3")
                        with mui.Grid(item=True):
                            mui.Typography("$2,324.00", variant="h5")
                with mui.Grid(item=True):
                    with mui.TextField(
                        select=True,
                        defaultValue="today",
                        size="small"
                    ):
                        mui.MenuItem("Today", value="today")
                        mui.MenuItem("This Month", value="month")
                        mui.MenuItem("This Year", value="year")
        
        with mui.CardContent():
            mui.Plot(
                data=data,
                layout=layout,
            )

def datagridcard():
    # State management for uploaded data
    if 'df' not in st.session_state:
        st.session_state.df = None

    # Get events from session state
    events = st.session_state.get("events", {})
    file_event = events.get("csv_upload", {})

    # Handle file upload event
    if file_event:
        try:
            # Get the file content from the event
            file_content = file_event.get('value', {}).get('result', None)
            if file_content:
                # Convert base64 to bytes and create DataFrame
                import base64
                content = base64.b64decode(file_content.split(',')[1])
                df = pd.read_csv(io.BytesIO(content))
                st.session_state.df = df
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

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
            if st.session_state.df is not None:
                df = st.session_state.df
                
                # Convert DataFrame to rows forma
                rows = df.to_dict('records')
                for i, row in enumerate(rows):
                    row['id'] = i

                # Create columns configuration with types
                columns = [
                    {'field': 'id', 'headerName': 'ID', 'width': 50, 'type': 'number'},
                ]
                
                for col in df.columns:
                    column_def = {
                        'field': col, 
                        'headerName': col.title(), 
                        'width': 100
                    }
                    
                    # Set column type based on dtype
                    if pd.api.types.is_numeric_dtype(df[col].dtype):
                        column_def['type'] = 'number'
                    elif pd.api.types.is_datetime64_any_dtype(df[col].dtype):
                        column_def['type'] = 'dateTime'
                    elif pd.api.types.is_bool_dtype(df[col].dtype):
                        column_def['type'] = 'boolean'
                        
                    columns.append(column_def)

                with mui.Box:
                    mui.DataGrid(
                        id="my-grid",
                        rows=rows,
                        columns=columns,
                        filterMode="server"
                    )
            else:
                mui.Typography(
                    "Upload a CSV file to display data",
                    sx={"textAlign": "center"}
                )

def dashboard():
        with mui.Grid(container=True, spacing=2):
            # First row
            with mui.Grid(item=True, xs=12):
                with mui.Grid(container=True, spacing=2):
                    with mui.Grid(item=True, lg=4, md=6, sm=6, xs=12):
                        earningcard()
                    with mui.Grid(item=True, lg=4, md=6, sm=6, xs=12):
                        totalorderlinechartcard()
                    # with mui.Grid(item=True, lg=4, md=12, sm=12, xs=12):
                    #     with mui.Grid(container=True, spacing=2):
                    #         with mui.Grid(item=True, sm=6, xs=12, md=6, lg=12):
                    #             totalincomedarkcard()
                    #         with mui.Grid(item=True, sm=6, xs=12, md=6, lg=12):
                    #             totalincomelightcard()
            # # Second row
            # with mui.Grid(item=True, xs=12):
            #     with mui.Grid(container=True, spacing=2):
            #         with mui.Grid(item=True, xs=12, md=8):
            #             totalgrowthbarchart()
            #         with mui.Grid(item=True, xs=12, md=4):
            #             popularcard()

            # Third row - DataGrid
            # with mui.Grid(item=True, xs=12):
            #     datagridcard()

if __name__ == "__main__":
    dashboard()
