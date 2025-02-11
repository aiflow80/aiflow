import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import ElementsTheme from './components/elementsTheme';
import { themeConfig } from './config/theme.config';

// Debug config
console.log('Theme configuration:', {
  defaultMode: themeConfig.defaultMode,
});

// Initialize theme immediately before any React code
ElementsTheme.initializeTheme();

// Prevent any transitions during initial load
document.documentElement.setAttribute('data-loading', 'true');

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Enable transitions after load
window.addEventListener('load', () => {
  document.documentElement.removeAttribute('data-loading');
});
