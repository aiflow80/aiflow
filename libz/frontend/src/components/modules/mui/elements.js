import React, { lazy, Suspense } from "react";
import ElementsLoading from "../../elementsLoading";
import { PlotComponent } from "../plot/plotly";
import { createAutocompleteComponent, createSelectComponent } from "./customElements";
import { dataGridComponents } from "./customDataGrid";

const dynamicImport = (importFn, componentName) => {
  const Component = lazy(() => {
    if (componentName === 'Plot' || componentName === 'plot') {
      return Promise.resolve({ default: PlotComponent });
    }

    if (componentName === 'Autocomplete') {
      return importFn().then(module => ({
        default: createAutocompleteComponent(module)
      }));
    } 
    
    if (componentName === 'Select') {
      return importFn().then(module => ({
        default: createSelectComponent(module)
      }));
    }

    return importFn();
  });

  return (props) => (
    <Suspense fallback={<ElementsLoading />}>
      <Component {...props} />
    </Suspense>
  );
};

// Material-UI Components
const mui = {
  Accordion: dynamicImport(() => import("@mui/material/Accordion")),
  AccordionActions: dynamicImport(() => import("@mui/material/AccordionActions")),
  AccordionDetails: dynamicImport(() => import("@mui/material/AccordionDetails")),
  AccordionSummary: dynamicImport(() => import("@mui/material/AccordionSummary")),
  Alert: dynamicImport(() => import("@mui/material/Alert")),
  AlertTitle: dynamicImport(() => import("@mui/material/AlertTitle")),
  AppBar: dynamicImport(() => import("@mui/material/AppBar")),
  Autocomplete: dynamicImport(() => import("@mui/material/Autocomplete"), "Autocomplete"),
  Avatar: dynamicImport(() => import("@mui/material/Avatar")),
  AvatarGroup: dynamicImport(() => import("@mui/material/AvatarGroup")),
  Backdrop: dynamicImport(() => import("@mui/material/Backdrop")),
  Badge: dynamicImport(() => import("@mui/material/Badge")),
  BottomNavigation: dynamicImport(() => import("@mui/material/BottomNavigation")),
  BottomNavigationAction: dynamicImport(() => import("@mui/material/BottomNavigationAction")),
  Box: dynamicImport(() => import("@mui/material/Box")),
  Breadcrumbs: dynamicImport(() => import("@mui/material/Breadcrumbs")),
  Button: dynamicImport(() => import("@mui/material/Button")),
  ButtonBase: dynamicImport(() => import("@mui/material/ButtonBase")),
  ButtonGroup: dynamicImport(() => import("@mui/material/ButtonGroup")),
  Card: dynamicImport(() => import("@mui/material/Card")),
  CardActionArea: dynamicImport(() => import("@mui/material/CardActionArea")),
  CardActions: dynamicImport(() => import("@mui/material/CardActions")),
  CardContent: dynamicImport(() => import("@mui/material/CardContent")),
  CardHeader: dynamicImport(() => import("@mui/material/CardHeader")),
  CardMedia: dynamicImport(() => import("@mui/material/CardMedia")),
  Checkbox: dynamicImport(() => import("@mui/material/Checkbox")),
  Chip: dynamicImport(() => import("@mui/material/Chip")),
  CircularProgress: dynamicImport(() => import("@mui/material/CircularProgress")),
  ClickAwayListener: dynamicImport(() => import("@mui/material/ClickAwayListener")),
  Collapse: dynamicImport(() => import("@mui/material/Collapse")),
  Container: dynamicImport(() => import("@mui/material/Container")),
  CssBaseline: dynamicImport(() => import("@mui/material/CssBaseline")),
  Dialog: dynamicImport(() => import("@mui/material/Dialog")),
  DialogActions: dynamicImport(() => import("@mui/material/DialogActions")),
  DialogContent: dynamicImport(() => import("@mui/material/DialogContent")),
  DialogContentText: dynamicImport(() => import("@mui/material/DialogContentText")),
  DialogTitle: dynamicImport(() => import("@mui/material/DialogTitle")),
  Divider: dynamicImport(() => import("@mui/material/Divider")),
  Drawer: dynamicImport(() => import("@mui/material/Drawer")),
  Fab: dynamicImport(() => import("@mui/material/Fab")),
  Fade: dynamicImport(() => import("@mui/material/Fade")),
  FilledInput: dynamicImport(() => import("@mui/material/FilledInput")),
  FormControl: dynamicImport(() => import("@mui/material/FormControl")),
  FormControlLabel: dynamicImport(() => import("@mui/material/FormControlLabel")),
  FormGroup: dynamicImport(() => import("@mui/material/FormGroup")),
  FormHelperText: dynamicImport(() => import("@mui/material/FormHelperText")),
  FormLabel: dynamicImport(() => import("@mui/material/FormLabel")),
  Grid: dynamicImport(() => import("@mui/material/Grid")),
  Grow: dynamicImport(() => import("@mui/material/Grow")),
  Hidden: dynamicImport(() => import("@mui/material/Hidden")),
  Icon: dynamicImport(() => import("@mui/material/Icon")),
  IconButton: dynamicImport(() => import("@mui/material/IconButton")),
  ImageList: dynamicImport(() => import("@mui/material/ImageList")),
  ImageListItem: dynamicImport(() => import("@mui/material/ImageListItem")),
  ImageListItemBar: dynamicImport(() => import("@mui/material/ImageListItemBar")),
  Input: dynamicImport(() => import("@mui/material/Input")),
  InputAdornment: dynamicImport(() => import("@mui/material/InputAdornment")),
  InputBase: dynamicImport(() => import("@mui/material/InputBase")),
  InputLabel: dynamicImport(() => import("@mui/material/InputLabel")),
  LinearProgress: dynamicImport(() => import("@mui/material/LinearProgress")),
  Link: dynamicImport(() => import("@mui/material/Link")),
  List: dynamicImport(() => import("@mui/material/List")),
  ListItem: dynamicImport(() => import("@mui/material/ListItem")),
  ListItemAvatar: dynamicImport(() => import("@mui/material/ListItemAvatar")),
  ListItemButton: dynamicImport(() => import("@mui/material/ListItemButton")),
  ListItemIcon: dynamicImport(() => import("@mui/material/ListItemIcon")),
  ListItemSecondaryAction: dynamicImport(() => import("@mui/material/ListItemSecondaryAction")),
  ListItemText: dynamicImport(() => import("@mui/material/ListItemText")),
  ListSubheader: dynamicImport(() => import("@mui/material/ListSubheader")),
  Menu: dynamicImport(() => import("@mui/material/Menu")),
  MenuItem: dynamicImport(() => import("@mui/material/MenuItem")),
  MenuList: dynamicImport(() => import("@mui/material/MenuList")),
  Modal: dynamicImport(() => import("@mui/material/Modal")),
  NativeSelect: dynamicImport(() => import("@mui/material/NativeSelect")),
  OutlinedInput: dynamicImport(() => import("@mui/material/OutlinedInput")),
  Pagination: dynamicImport(() => import("@mui/material/Pagination")),
  Paper: dynamicImport(() => import("@mui/material/Paper")),
  Popover: dynamicImport(() => import("@mui/material/Popover")),
  Popper: dynamicImport(() => import("@mui/material/Popper")),
  Portal: dynamicImport(() => import("@mui/material/Portal")),
  Radio: dynamicImport(() => import("@mui/material/Radio")),
  RadioGroup: dynamicImport(() => import("@mui/material/RadioGroup")),
  Rating: dynamicImport(() => import("@mui/material/Rating")),
  ScopedCssBaseline: dynamicImport(() => import("@mui/material/ScopedCssBaseline")),
  Select: dynamicImport(() => import("@mui/material/Select"), "Select"),
  Slider: dynamicImport(() => import("@mui/material/Slider")),
  Snackbar: dynamicImport(() => import("@mui/material/Snackbar")),
  SpeedDial: dynamicImport(() => import("@mui/material/SpeedDial")),
  Stack: dynamicImport(() => import("@mui/material/Stack")),
  Step: dynamicImport(() => import("@mui/material/Step")),
  Stepper: dynamicImport(() => import("@mui/material/Stepper")),
  SvgIcon: dynamicImport(() => import("@mui/material/SvgIcon")),
  Switch: dynamicImport(() => import("@mui/material/Switch")),
  Tab: dynamicImport(() => import("@mui/material/Tab")),
  Table: dynamicImport(() => import("@mui/material/Table")),
  TableBody: dynamicImport(() => import("@mui/material/TableBody")),
  TableContainer: dynamicImport(() => import("@mui/material/TableContainer")),
  TableFooter: dynamicImport(() => import("@mui/material/TableFooter")),
  Tabs: dynamicImport(() => import("@mui/material/Tabs")),
  TextField: dynamicImport(() => import("@mui/material/TextField")),
  ToggleButton: dynamicImport(() => import("@mui/material/ToggleButton")),
  Toolbar: dynamicImport(() => import("@mui/material/Toolbar")),
  Tooltip: dynamicImport(() => import("@mui/material/Tooltip")),
  Typography: dynamicImport(() => import("@mui/material/Typography")),
  Plot: dynamicImport(() => Promise.resolve(), "Plot"), // Use uppercase Plot
};

// Use dataGridComponents to create the dataGrid object
const dataGrid = Object.entries(dataGridComponents).reduce((acc, [key, componentFn]) => {
  acc[key] = componentFn(dynamicImport);
  return acc;
}, {});

// Combined Elements
const elements = {
  ...mui,
  ...dataGrid
};

const loadMuiElements = (element) => {
  return elements[element];
};

export default loadMuiElements;
