import React, { lazy, Suspense } from "react";
import ElementsLoading from "../../elementsLoading";

const cachedIcons = {};

const loadMuiIcons = (element) => {
  if (cachedIcons.hasOwnProperty(element)) {
    return cachedIcons[element];
  }

  const Component = lazy(() =>
    import("@mui/icons-material").then((module) => ({ default: module[element] }))
  );

  cachedIcons[element] = (props) => (
    <Suspense fallback={<ElementsLoading />}>
      <Component {...props} />
    </Suspense>
  );

  return cachedIcons[element];
};

export default loadMuiIcons;