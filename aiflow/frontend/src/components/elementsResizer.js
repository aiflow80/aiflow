import ResizeObserver from "resize-observer-polyfill";
import { Streamlit } from "streamlit-component-lib";

const resizeObserver = new ResizeObserver((entries) => {
  Streamlit.setFrameHeight(entries[0].contentRect.height + 25);
});

const observeElement = (element) => {
  if (element !== null) {
    resizeObserver.observe(element);
  } else {
    resizeObserver.disconnect();
  }
};

const ElementsResizer = ({ children }) => (
  <div ref={observeElement}>
    {children}
  </div>
);

export default ElementsResizer;
