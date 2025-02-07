import React, { lazy, Suspense } from "react";
import ElementsLoading from "../../elementsLoading";

// Utility function for dynamic imports with lazy and suspense
const dynamicImport = (importFn) => {
  const Component = lazy(importFn);
  return (props) => (
    <Suspense fallback={<ElementsLoading />}>
      <Component {...props} />
    </Suspense>
  );
};

// Material-UI Lab Components
const lab = {
  Accordion: dynamicImport(() => import("@mui/material/Accordion")),
  LoadingButton: dynamicImport(() => import("@mui/lab/LoadingButton")),
  Alert: dynamicImport(() => import("@mui/lab/Alert")),
  AlertTitle: dynamicImport(() => import("@mui/lab/AlertTitle")),
  AvatarGroup: dynamicImport(() => import("@mui/lab/AvatarGroup")),
  CalendarPicker: dynamicImport(() => import("@mui/lab/CalendarPicker")),
  CalendarPickerSkeleton: dynamicImport(() => import("@mui/lab/CalendarPickerSkeleton")),
  ClockPicker: dynamicImport(() => import("@mui/lab/ClockPicker")),
  DatePicker: dynamicImport(() => import("@mui/lab/DatePicker")),
  DateTimePicker: dynamicImport(() => import("@mui/lab/DateTimePicker")),
  DesktopDatePicker: dynamicImport(() => import("@mui/lab/DesktopDatePicker")),
  DesktopDateTimePicker: dynamicImport(() => import("@mui/lab/DesktopDateTimePicker")),
  DesktopTimePicker: dynamicImport(() => import("@mui/lab/DesktopTimePicker")),
  LocalizationProvider: dynamicImport(() => import("@mui/lab/LocalizationProvider")),
  Masonry: dynamicImport(() => import("@mui/lab/Masonry")),
  MobileDatePicker: dynamicImport(() => import("@mui/lab/MobileDatePicker")),
  MobileDateTimePicker: dynamicImport(() => import("@mui/lab/MobileDateTimePicker")),
  MobileTimePicker: dynamicImport(() => import("@mui/lab/MobileTimePicker")),
  MonthPicker: dynamicImport(() => import("@mui/lab/MonthPicker")),
  Pagination: dynamicImport(() => import("@mui/lab/Pagination")),
  PaginationItem: dynamicImport(() => import("@mui/lab/PaginationItem")),
  PickersDay: dynamicImport(() => import("@mui/lab/PickersDay")),
  Rating: dynamicImport(() => import("@mui/lab/Rating")),
  Skeleton: dynamicImport(() => import("@mui/lab/Skeleton")),
  SpeedDial: dynamicImport(() => import("@mui/lab/SpeedDial")),
  SpeedDialAction: dynamicImport(() => import("@mui/lab/SpeedDialAction")),
  SpeedDialIcon: dynamicImport(() => import("@mui/lab/SpeedDialIcon")),
  StaticDatePicker: dynamicImport(() => import("@mui/lab/StaticDatePicker")),
  StaticDateTimePicker: dynamicImport(() => import("@mui/lab/StaticDateTimePicker")),
  StaticTimePicker: dynamicImport(() => import("@mui/lab/StaticTimePicker")),
  TabContext: dynamicImport(() => import("@mui/lab/TabContext")),
  TabList: dynamicImport(() => import("@mui/lab/TabList")),
  TabPanel: dynamicImport(() => import("@mui/lab/TabPanel")),
  TimePicker: dynamicImport(() => import("@mui/lab/TimePicker")),
  Timeline: dynamicImport(() => import("@mui/lab/Timeline")),
  TimelineConnector: dynamicImport(() => import("@mui/lab/TimelineConnector")),
  TimelineContent: dynamicImport(() => import("@mui/lab/TimelineContent")),
  TimelineDot: dynamicImport(() => import("@mui/lab/TimelineDot")),
  TimelineItem: dynamicImport(() => import("@mui/lab/TimelineItem")),
  TimelineOppositeContent: dynamicImport(() => import("@mui/lab/TimelineOppositeContent")),
  TimelineSeparator: dynamicImport(() => import("@mui/lab/TimelineSeparator")),
  ToggleButton: dynamicImport(() => import("@mui/lab/ToggleButton")),
  ToggleButtonGroup: dynamicImport(() => import("@mui/lab/ToggleButtonGroup")),
  TreeItem: dynamicImport(() => import("@mui/lab/TreeItem")),
  TreeView: dynamicImport(() => import("@mui/lab/TreeView")),
  YearPicker: dynamicImport(() => import("@mui/lab/YearPicker")),
};

// Combined Elements
const elements = {
  ...lab,
};

const loadMuiLab = (element) => {
  return elements[element];
};

export default loadMuiLab;