import { useEffect, useState } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { themeConfig } from '../config/theme.config';

const THEME_PRESETS = themeConfig.presets;

const getThemeColors = (mode) => {
  const validMode = (mode && ['light', 'dark'].includes(mode)) 
    ? mode 
    : themeConfig.defaultMode;
  console.log('getThemeColors - Using mode:', validMode);
  return THEME_PRESETS[validMode];
};

const baseComponents = (colors) => ({
  MuiCssBaseline: {
    styleOverrides: {
      '*': {
        margin: 0,
        padding: 0,
        boxSizing: 'border-box',
      },
      'html, body, #root': {
        width: '100%',
        height: '100%',
        backgroundColor: colors.background,
        color: colors.text,
      }
    }
  },
});

const createThemeWithColors = (mode, customColors = {}) => {
  const defaultColors = getThemeColors(mode);
  const colors = {
    primary: customColors.primaryColor || defaultColors.primary,
    background: customColors.backgroundColor || defaultColors.background,
    paper: customColors.secondaryBackgroundColor || defaultColors.paper,
    text: customColors.textColor || defaultColors.text,
    textSecondary: customColors.fadedText60 || defaultColors.textSecondary
  };
  
  return createTheme({
    palette: {
      mode,
      primary: {
        main: colors.primary,
      },
      background: {
        default: colors.background,
        paper: colors.paper,
      },
      text: {
        primary: colors.text,
        secondary: colors.textSecondary,
      },
    },
    components: baseComponents(colors)
  });
};

const ElementsTheme = ({ children, theme }) => {
  const [elementsTheme, setElementsTheme] = useState(() => {
    const initialMode = themeConfig.defaultMode;
    console.log('ElementsTheme - Initial mode:', initialMode);
    return createThemeWithColors(initialMode);
  });

  useEffect(() => {
    if (theme) {
      console.log('Theme prop changed:', theme); // Add debug log
      const newTheme = createThemeWithColors(theme.base || 'dark', theme);
      setElementsTheme(newTheme);
    }
  }, [theme]);

  return <ThemeProvider theme={elementsTheme}>{children}</ThemeProvider>;
};

// Add static initialization method
ElementsTheme.initializeTheme = () => {
  const colors = getThemeColors();
  const style = document.createElement('style');
  const css = `
    *, *::before, *::after {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    html, body, #root {
      width: 100%;
      height: 100%;
      background-color: ${colors.background};
      color: ${colors.text};
    }
  `;
  
  style.innerHTML = css;
  document.head.insertBefore(style, document.head.firstChild);
};

export const getInitialThemeColors = () => getThemeColors();
export default ElementsTheme;
