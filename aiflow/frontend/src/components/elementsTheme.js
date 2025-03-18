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
    }
    // Removed custom baseComponents to use MUI's default behavior
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

// Simplified initialization method to use MUI defaults
ElementsTheme.initializeTheme = () => {
  // Let MUI handle default styling through ThemeProvider
  // This method can be kept for backward compatibility or removed if not needed
};

export const getInitialThemeColors = () => getThemeColors();
export default ElementsTheme;
