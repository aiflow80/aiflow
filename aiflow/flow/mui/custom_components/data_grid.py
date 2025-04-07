import pandas as pd
from aiflow import mui, events_store, state

def datagrid(df, grid_id="my-grid", **grid_props):
    _state = state
    # Initialize state variables for grid events
    if '__last_grid_event' not in _state:
        _state['__last_grid_event'] = None
    if '__grid_filter' not in _state:
        _state['__grid_filter'] = None
    if '__grid_page' not in _state:
        _state['__grid_page'] = 0
    if '__grid_page_size' not in _state:
        _state['__grid_page_size'] = 25
    if '__grid_sort_field' not in _state:
        _state['__grid_sort_field'] = None
    if '__grid_sort_dir' not in _state:
        _state['__grid_sort_dir'] = None

    # Create a copy of the dataframe to avoid modifying the original
    if df is None:
        return mui.Typography(
            "No data available to display",
            sx={"textAlign": "center"}
        )
    
    original_df = df.copy()
    processed_df = original_df.copy()

    # Handle grid events with deduplication
    # Corrected to handle events_store structure with payload
    payload = events_store.get('payload', {})
    grid_event = {}
    
    # Check if the payload is for our grid
    if payload and payload.get('key') == grid_id:
        grid_event = payload
    
    if grid_event:
        current_event = (grid_event.get('type'), str(grid_event.get('value')))
        
        # Only process if event is different from last one
        if current_event != _state['__last_grid_event']:
            _state['__last_grid_event'] = current_event
            
            if grid_event.get('type') == 'filter-change':
                filter_model = grid_event['value']
                _state['__grid_filter'] = filter_model
                
                # Apply filtering
                if filter_model and filter_model.get('items'):
                    processed_df = original_df.copy()
                    for filter_item in filter_model['items']:
                        field = filter_item.get('field')
                        operator = filter_item.get('operator')
                        value = filter_item.get('value')
                        
                        if field and operator:
                            # String operators
                            if operator == 'contains' and isinstance(value, str):
                                processed_df = processed_df[processed_df[field].astype(str).str.contains(value, na=False)]
                            elif operator == 'does not contain' and isinstance(value, str):
                                processed_df = processed_df[~processed_df[field].astype(str).str.contains(value, na=False)]
                            elif operator == '=' or operator == 'equals':
                                processed_df = processed_df[processed_df[field] == value]
                            elif operator == '!=' or operator == 'does not equal':
                                processed_df = processed_df[processed_df[field] != value]
                            elif operator == 'starts with' and isinstance(value, str):
                                processed_df = processed_df[processed_df[field].astype(str).str.startswith(value, na=False)]
                            elif operator == 'ends with' and isinstance(value, str):
                                processed_df = processed_df[processed_df[field].astype(str).str.endswith(value, na=False)]
                            elif operator == 'is empty':
                                processed_df = processed_df[processed_df[field].isna() | (processed_df[field].astype(str) == '')]
                            elif operator == 'is not empty':
                                processed_df = processed_df[processed_df[field].notna() & (processed_df[field].astype(str) != '')]
                            elif operator == 'is any of' and isinstance(value, list):
                                processed_df = processed_df[processed_df[field].isin(value)]
                    
                    _state['__df'] = processed_df
                    _state['__grid_page'] = 0
                else:
                    _state['__df'] = original_df.copy()
                    _state['__grid_page'] = 0

            elif grid_event.get('type') == 'sort-change':
                sort_model = grid_event['value']
                if sort_model and len(sort_model) > 0:
                    _state['__grid_sort_field'] = sort_model[0].get('field')
                    _state['__grid_sort_dir'] = sort_model[0].get('sort')
                    # Apply sorting
                    if _state['__grid_sort_field'] and _state['__grid_sort_dir']:
                        sorted_df = original_df.copy() if '__df' not in _state else _state['__df'].copy()
                        _state['__df'] = sorted_df.sort_values(
                            by=_state['__grid_sort_field'],
                            ascending=(_state['__grid_sort_dir'] == 'asc')
                        )
                        _state['__grid_page'] = 0

            elif grid_event.get('type') == 'pagination-change':
                _state['__grid_page'] = grid_event['value'].get('page', 0)
                _state['__grid_page_size'] = grid_event['value'].get('pageSize', 25)

    # Use processed dataframe if available in state
    if '__df' in _state:
        processed_df = _state['__df']

    # Apply pagination
    row_count = len(processed_df)
    start_idx = _state['__grid_page'] * _state['__grid_page_size']
    end_idx = start_idx + _state['__grid_page_size']
    page_df = processed_df.iloc[start_idx:end_idx]

    # Convert processed DataFrame to rows format
    rows = page_df.to_dict('records')
    for i, row in enumerate(rows):
        row['id'] = i + start_idx

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

    # Create and return the DataGrid component with server-side features
    return mui.DataGrid(
        id=grid_id,
        rows=rows,
        columns=columns,
        checkboxSelection=False,
        paginationMode="server",
        sortingMode="server",
        filterMode="server",
        rowCount=row_count,
        pageSizeOptions=[5, 10, 25, 50],
        page=_state['__grid_page'],
        pageSize=_state['__grid_page_size'],
        initialState={
            "pagination": {
                "paginationModel": {
                    "pageSize": _state['__grid_page_size'],
                    "page": _state['__grid_page']
                }
            }
        },
        **grid_props
    )
