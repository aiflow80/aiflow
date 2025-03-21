import { useEffect, useState, createContext, useContext, useMemo } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { themeConfig } from '../config/theme.config';

const THEME_PRESETS = themeConfig.presets;
const ThemeContext = createContext(null);

// Color conversion utility for handling different color formats
const colorToHex = (color) => {
  // Handle RGB format
  if (typeof color === 'string' && color.startsWith('rgb(')) {
    const rgbValues = color.match(/\d+/g).map(Number);
    if (rgbValues?.length === 3) {
      const [r, g, b] = rgbValues;
      return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
  }
  
  // Handle RGBA format by stripping alpha
  if (typeof color === 'string' && color.startsWith('rgba(')) {
    const rgbaValues = color.match(/\d+(\.\d+)?/g).map(Number);
    if (rgbaValues?.length >= 3) {
      const [r, g, b] = rgbaValues;
      return `#${Math.round(r).toString(16).padStart(2, '0')}${Math.round(g).toString(16).padStart(2, '0')}${Math.round(b).toString(16).padStart(2, '0')}`;
    }
  }
  
  return color;
};

// Enhanced color adjustment with proper color format handling
const adjustColorLightness = (color, factor) => {
  const hex = colorToHex(color);
  
  // Skip if not a valid hex color
  if (!hex.startsWith('#')) return color;
  
  // Convert hex to RGB
  let r = parseInt(hex.slice(1, 3), 16);
  let g = parseInt(hex.slice(3, 5), 16);
  let b = parseInt(hex.slice(5, 7), 16);

  // Adjust lightness - increase or decrease based on factor
  r = Math.min(255, Math.max(0, Math.round(r * factor)));
  g = Math.min(255, Math.max(0, Math.round(g * factor)));
  b = Math.min(255, Math.max(0, Math.round(b * factor)));

  // Convert back to hex
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
};

// Generate more comprehensive color palette like MUI
const generateColorVariants = (baseColor) => {
  const baseHex = colorToHex(baseColor);
  const variants = {};
  
  // Base color will be "500"
  variants[500] = baseHex;
  
  // Generate lighter variants (more levels for better granularity)
  variants[50] = adjustColorLightness(baseHex, 2.0);
  variants[100] = adjustColorLightness(baseHex, 1.8);
  variants[200] = adjustColorLightness(baseHex, 1.6);
  variants[300] = adjustColorLightness(baseHex, 1.4);
  variants[400] = adjustColorLightness(baseHex, 1.2);
  
  // Generate darker variants
  variants[600] = adjustColorLightness(baseHex, 0.9);
  variants[700] = adjustColorLightness(baseHex, 0.8);
  variants[800] = adjustColorLightness(baseHex, 0.7);
  variants[900] = adjustColorLightness(baseHex, 0.6);
  
  // Add A (accent) variants like MUI
  variants.A100 = adjustColorLightness(baseHex, 1.5);
  variants.A200 = adjustColorLightness(baseHex, 1.3);
  variants.A400 = adjustColorLightness(baseHex, 1.1);
  variants.A700 = adjustColorLightness(baseHex, 0.85);
  
  // Add contrast text calculation
  variants.contrastText = getContrastText(baseHex);
  
  return variants;
};

// Calculate contrast text color for accessibility
const getContrastText = (background) => {
  const hex = colorToHex(background).replace('#', '');
  
  // Convert to RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  // Calculate luminance using WCAG formula
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  
  // Return white for dark backgrounds, black for light backgrounds
  return luminance > 0.5 ? getThemeColors('light').text : getThemeColors('dark').text;
};

// Parse color references like "primary.800"
const parseColorReference = (colorRef, palette) => {
  if (typeof colorRef !== 'string') return colorRef;
  
  if (colorRef.includes('.')) {
    const [colorBase, colorShade] = colorRef.split('.');
    
    if (palette[colorBase] && palette[colorBase][colorShade]) {
      return palette[colorBase][colorShade];
    }
  }
  
  return colorRef;
};

const getThemeColors = (mode) => {
  const validMode = (mode && ['light', 'dark'].includes(mode)) 
    ? mode 
    : themeConfig.defaultMode;
  return THEME_PRESETS[validMode];
};

// Enhanced theme creation function
const createThemeWithColors = (mode, customColors = {}) => {
  const defaultColors = getThemeColors(mode);
  const colors = {
    primary: customColors.primaryColor || defaultColors.primary,
    secondary: customColors.secondaryColor || defaultColors.secondary || defaultColors.textSecondary,
    error: customColors.errorColor || defaultColors.error,
    warning: customColors.warningColor || defaultColors.warning,
    info: customColors.infoColor || defaultColors.info,
    success: customColors.successColor || defaultColors.success,
    background: customColors.backgroundColor || defaultColors.background,
    paper: customColors.secondaryBackgroundColor || defaultColors.paper,
    text: customColors.textColor || defaultColors.text,
    textSecondary: customColors.fadedText60 || defaultColors.textSecondary
  };
  
  // Generate color variants for all main colors
  const primaryVariants = generateColorVariants(colors.primary);
  const secondaryVariants = generateColorVariants(colors.secondary);
  const errorVariants = generateColorVariants(colors.error);
  const warningVariants = generateColorVariants(colors.warning);
  const infoVariants = generateColorVariants(colors.info);
  const successVariants = generateColorVariants(colors.success);
  
  // Complete palette with all MUI options
  return createTheme({
    palette: {
      mode,
      primary: {
        ...primaryVariants,
        main: primaryVariants[500],
        light: primaryVariants[300],
        dark: primaryVariants[700],
        contrastText: primaryVariants.contrastText
      },
      secondary: {
        ...secondaryVariants,
        main: secondaryVariants[500],
        light: secondaryVariants[300],
        dark: secondaryVariants[700],
        contrastText: secondaryVariants.contrastText
      },
      error: {
        main: errorVariants[500],
        light: errorVariants[300],
        dark: errorVariants[700],
        contrastText: errorVariants.contrastText
      },
      warning: {
        main: warningVariants[500],
        light: warningVariants[300],
        dark: warningVariants[700],
        contrastText: warningVariants.contrastText
      },
      info: {
        main: infoVariants[500],
        light: infoVariants[300],
        dark: infoVariants[700],
        contrastText: infoVariants.contrastText
      },
      success: {
        main: successVariants[500],
        light: successVariants[300],
        dark: successVariants[700],
        contrastText: successVariants.contrastText
      },
      background: {
        default: parseColorReference(colors.background, { 
          primary: primaryVariants, 
          secondary: secondaryVariants 
        }),
        paper: parseColorReference(colors.paper, { 
          primary: primaryVariants, 
          secondary: secondaryVariants 
        }),
      },
      text: {
        primary: parseColorReference(colors.text, { 
          primary: primaryVariants, 
          secondary: secondaryVariants 
        }),
        secondary: parseColorReference(colors.textSecondary, { 
          primary: primaryVariants, 
          secondary: secondaryVariants 
        }),
        disabled: mode === 'light' ? 
          'rgba(0, 0, 0, 0.38)' : 
          'rgba(255, 255, 255, 0.38)',
      },
      divider: defaultColors.divider,
      action: defaultColors.action
    },
    // Add MUI's other theme sections
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      // Default typography values
    },
    spacing: 8, // Default spacing unit
    breakpoints: {
      values: {
        xs: 0,
        sm: 600,
        md: 960,
        lg: 1280,
        xl: 1920,
      },
    },
    // Can be extended with shape, transitions, zIndex, etc.
  });
};

export const useElementsTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useElementsTheme must be used within an ElementsTheme provider');
  }
  return context;
};

const ElementsTheme = ({ children, theme }) => {
  // Create initial theme based on default mode
  const [themeConfig, setThemeConfig] = useState({
    base: theme?.base || themeConfig.defaultMode,
    customColors: theme || {}
  });
  
  // Memoize theme creation to prevent unnecessary recreations
  const elementsTheme = useMemo(() => {
    return createThemeWithColors(themeConfig.base, themeConfig.customColors);
  }, [themeConfig.base, themeConfig.customColors]);

  // Update theme only when theme prop changes
  useEffect(() => {
    if (theme) {
      setThemeConfig({
        base: theme.base || themeConfig.defaultMode,
        customColors: theme
      });
    }
  }, [theme]);

  const contextValue = useMemo(() => ({
    theme: elementsTheme,
    mode: themeConfig.base,
    updateTheme: setThemeConfig
  }), [elementsTheme, themeConfig.base]);

  return (
    <ThemeContext.Provider value={contextValue}>
      <ThemeProvider theme={elementsTheme}>
        {children}
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};

// Simplified initialization - can be removed if not needed
ElementsTheme.initializeTheme = () => {
  // This is now handled by the context and ThemeProvider
};

export const getInitialThemeColors = () => getThemeColors();
export default ElementsTheme;
