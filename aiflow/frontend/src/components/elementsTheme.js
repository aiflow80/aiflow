import { useEffect, useState, createContext, useContext, useMemo } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { themeConfig } from '../config/theme.config';

const THEME_PRESETS = themeConfig.presets;
const ThemeContext = createContext(null);

// Helper function to adjust color lightness
const adjustColorLightness = (hex, factor) => {
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

// Generate color variations from 100 (lightest) to 1000 (darkest)
const generateColorVariants = (baseColor) => {
  const variants = {};
  
  // Base color will be "500"
  variants[500] = baseColor;
  
  // Generate lighter variants
  variants[100] = adjustColorLightness(baseColor, 1.8);
  variants[200] = adjustColorLightness(baseColor, 1.6);
  variants[300] = adjustColorLightness(baseColor, 1.4);
  variants[400] = adjustColorLightness(baseColor, 1.2);
  
  // Generate darker variants
  variants[600] = adjustColorLightness(baseColor, 0.9);
  variants[700] = adjustColorLightness(baseColor, 0.8);
  variants[800] = adjustColorLightness(baseColor, 0.7);
  variants[900] = adjustColorLightness(baseColor, 0.6);
  variants[1000] = adjustColorLightness(baseColor, 0.5);
  
  return variants;
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

const createThemeWithColors = (mode, customColors = {}) => {
  const defaultColors = getThemeColors(mode);
  const colors = {
    primary: customColors.primaryColor || defaultColors.primary,
    secondary: customColors.secondaryColor || defaultColors.secondary || defaultColors.textSecondary,
    background: customColors.backgroundColor || defaultColors.background,
    paper: customColors.secondaryBackgroundColor || defaultColors.paper,
    text: customColors.textColor || defaultColors.text,
    textSecondary: customColors.fadedText60 || defaultColors.textSecondary
  };
  
  // Generate color variants
  const primaryVariants = generateColorVariants(colors.primary);
  const secondaryVariants = generateColorVariants(colors.secondary);
  
  // Create extended color palette
  const colorPalette = {
    primary: {
      ...primaryVariants,
      main: primaryVariants[500],
    },
    secondary: {
      ...secondaryVariants,
      main: secondaryVariants[500],
    },
    background: {
      default: parseColorReference(colors.background, { primary: primaryVariants, secondary: secondaryVariants }),
      paper: parseColorReference(colors.paper, { primary: primaryVariants, secondary: secondaryVariants }),
    },
    text: {
      primary: parseColorReference(colors.text, { primary: primaryVariants, secondary: secondaryVariants }),
      secondary: parseColorReference(colors.textSecondary, { primary: primaryVariants, secondary: secondaryVariants }),
    },
  };
  
  return createTheme({
    palette: {
      mode,
      ...colorPalette,
    }
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
