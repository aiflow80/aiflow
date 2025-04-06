import React from 'react';

export const createDataGridComponent = (module) => {
  return (props) => {
    // Extract server-side related props
    const {
      filterMode,
      sortingMode,
      paginationMode,
      onFilterModelChange,
      onSortModelChange,
      onPaginationModelChange,
      rowCount: providedRowCount,
      page = 0,
      pageSize = 25,
      pageSizeOptions = [25], // Add default value
      ...otherProps
    } = props;

    const isServerPagination = onPaginationModelChange ? 'server' : 'client';
    
    // Calculate rowCount - if server pagination, rowCount is required
    const rowCount = isServerPagination === 'server' 
      ? (providedRowCount || 0)  // Provide default value for server mode
      : (otherProps.rows || []).length;  // Use rows length for client mode

    const finalProps = {
      ...otherProps,
      // Enable server-side features if handlers are provided
      filterMode: onFilterModelChange ? 'server' : 'client',
      sortingMode: onSortModelChange ? 'server' : 'client',
      paginationMode: isServerPagination,
      pagination: true, // Add this line
      rowCount, // Add rowCount to props
      // Pass through the handlers
      onFilterModelChange,
      onSortModelChange,
      onPaginationModelChange,
      pageSizeOptions, // Add this prop
      paginationModel: {
        page,
        pageSize,
      },
      autoHeight: false,
      style: {
        height: props.height || 500,
        width: '100%',
      },
      sx: {
        ...props.sx,
        // Target all scrollbars in the DataGrid
        '& ::-webkit-scrollbar': {
          width: '6px',
          height: '6px',
        },
        '& ::-webkit-scrollbar-track': {
          background: (theme) => theme.palette.background.default,
        },
        '& ::-webkit-scrollbar-thumb': {
          background: (theme) => theme.palette.text.disabled,
          borderRadius: '3px',
          '&:hover': {
            background: (theme) => theme.palette.text.secondary,
          },
        },
        // Also target the specific virtualScroller scrollbars
        '& .MuiDataGrid-virtualScroller::-webkit-scrollbar': {
          width: '6px',
          height: '6px',
        },
        '& .MuiDataGrid-virtualScroller::-webkit-scrollbar-track': {
          background: (theme) => theme.palette.background.default,
        },
        '& .MuiDataGrid-virtualScroller::-webkit-scrollbar-thumb': {
          background: (theme) => theme.palette.text.disabled,
          borderRadius: '3px',
          '&:hover': {
            background: (theme) => theme.palette.text.secondary,
          },
        },
      }
    };

    return React.createElement(module.DataGrid, finalProps);
  };
};

export const dataGridComponents = {
  DataGrid: (dynamicImport) => dynamicImport(() => import("@mui/x-data-grid").then(module => ({ 
    default: createDataGridComponent(module)
  }))),
  GridActionsCellItem: (dynamicImport) => dynamicImport(() => import("@mui/x-data-grid").then(module => ({ default: module.GridActionsCellItem }))),
  GridToolbar: (dynamicImport) => dynamicImport(() => import("@mui/x-data-grid").then(module => ({ default: module.GridToolbar }))),
  GridToolbarColumnsButton: (dynamicImport) => dynamicImport(() => import("@mui/x-data-grid").then(module => ({ default: module.GridToolbarColumnsButton }))),
  GridToolbarContainer: (dynamicImport) => dynamicImport(() => import("@mui/x-data-grid").then(module => ({ default: module.GridToolbarContainer }))),
  GridToolbarDensitySelector: (dynamicImport) => dynamicImport(() => import("@mui/x-data-grid").then(module => ({ default: module.GridToolbarDensitySelector }))),
  GridToolbarExport: (dynamicImport) => dynamicImport(() => import("@mui/x-data-grid").then(module => ({ default: module.GridToolbarExport }))),
  GridToolbarFilterButton: (dynamicImport) => dynamicImport(() => import("@mui/x-data-grid").then(module => ({ default: module.GridToolbarFilterButton }))),
};
