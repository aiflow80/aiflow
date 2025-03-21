export const themeConfig = {
  defaultMode: 'dark', // or 'light'
  presets: {
    dark: {
      primary: 'rgb(192, 30, 30)',    // Christmas red
      secondary: 'rgb(21, 87, 36)',   // Christmas green
      background: 'rgb(8, 18, 39)',   // Deep night blue
      paper: 'rgb(16, 32, 48)',       // Midnight blue
      text: 'rgba(255, 255, 255, 1)', // Snow white
      textSecondary: 'rgba(212, 175, 55, 0.9)', // Gold accent
      error: 'rgba(244, 67, 54, 1)',
      warning: 'rgba(255, 152, 0, 1)',
      info: 'rgba(33, 150, 243, 1)',
      success: 'rgba(76, 175, 80, 1)',
      divider: 'rgba(212, 175, 55, 0.3)', // Gold divider
      action: {
        active: 'rgba(255, 255, 255, 0.7)',
        hover: 'rgba(255, 255, 255, 0.1)',
        selected: 'rgba(255, 255, 255, 0.2)',
        disabled: 'rgba(255, 255, 255, 0.3)',
        disabledBackground: 'rgba(255, 255, 255, 0.12)'
      }
    },
    light: {
      primary: 'rgba(192, 30, 30, 1)',    // Christmas red
      secondary: 'rgba(21, 87, 36, 1)',   // Christmas green
      background: 'rgba(245, 245, 250, 1)', // Snow white background
      paper: 'rgba(255, 255, 255, 1)',     // White paper
      text: 'rgba(21, 42, 59, 0.87)',      // Dark blue-gray text
      textSecondary: 'rgba(192, 30, 30, 0.7)', // Red secondary text
      error: 'rgba(211, 47, 47, 1)',
      warning: 'rgba(237, 108, 2, 1)',
      info: 'rgba(2, 136, 209, 1)',
      success: 'rgba(46, 125, 50, 1)',
      divider: 'rgba(0, 0, 0, 0.12)',
      action: {
        active: 'rgba(0, 0, 0, 0.54)',
        hover: 'rgba(0, 0, 0, 0.04)',
        selected: 'rgba(0, 0, 0, 0.08)',
        disabled: 'rgba(0, 0, 0, 0.26)',
        disabledBackground: 'rgba(0, 0, 0, 0.12)'
      }
    }
  }
};
