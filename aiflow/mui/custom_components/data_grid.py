import pandas as pd
from aiflow.events import events_store, state
from aiflow import mui

def datagrid(id, dataframe):
    """Create a MUI DataGrid with server-side pagination, sorting, and filtering."""
    _state = state
    # Add event tracking state
    if '__last_grid_event' not in _state:
        _state['__last_grid_event'] = None

    # Add filter state
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
    if dataframe is None:
        return mui.Typography(
            "No data available to display",
            sx={"textAlign": "center"}
        )
    
    df = dataframe.copy()
    processed_df = df.copy()

    # Handle grid events with deduplication
    grid_event = events_store.get(id, {})
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
                    processed_df = df.copy()
                    for filter_item in filter_model['items']:
                        field = filter_item.get('field')
                        operator = filter_item.get('operator')
                        value = filter_item.get('value')
                        
                        if field and operator == '=':
                            processed_df = processed_df[processed_df[field] == value]
                    
                    _state['__df'] = processed_df
                    _state['__grid_page'] = 0
                else:
                    _state['__df'] = df.copy()
                    _state['__grid_page'] = 0

            elif grid_event.get('type') == 'sort-change':
                sort_model = grid_event['value']
                if sort_model and len(sort_model) > 0:
                    _state['__grid_sort_field'] = sort_model[0].get('field')
                    _state['__grid_sort_dir'] = sort_model[0].get('sort')
                    # Apply sorting
                    if _state['__grid_sort_field'] and _state['__grid_sort_dir']:
                        sorted_df = df.copy() if '__df' not in _state else _state['__df'].copy()
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
    columns = []
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

    if len(columns) > 2000:
        return mui.Typography(
            "Too many columns (maximum 2000 supported)",
            sx={"textAlign": "center"}
        )
    
    return mui.DataGrid(
        id=id,  # Use the provided id parameter instead of hardcoding
        rows=rows,
        columns=columns,
        checkboxSelection=True,
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
        }
    )
