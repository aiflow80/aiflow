import pandas as pd
from aiflow import mui

def create_data_grid_from_df(df, grid_id="my-grid", **grid_props):
    """
    Create a DataGrid component from a pandas DataFrame.
    
    Args:
        df: pandas DataFrame containing the data
        grid_id: ID for the DataGrid component
        grid_props: Additional properties to pass to the DataGrid
        
    Returns:
        DataGrid component
    """
    # Convert DataFrame to rows format
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

    # Create and return the DataGrid component
    return mui.DataGrid(
        id=grid_id,
        rows=rows,
        columns=columns,
        filterMode="server",
        **grid_props
    )
