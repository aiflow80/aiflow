export const themeConfig = {
  defaultMode: 'dark', // or 'light'
  presets: {
    dark: {
      primary: 'rgb(243, 24, 24)',
      secondary: 'rgb(24, 15, 51)',
      background: 'rgb(0, 0, 0)',
      paper: 'rgb(8, 18, 39)',
      text: 'rgba(255, 255, 255, 1)',
      textSecondary: 'rgba(235, 231, 231, 0.7)',
      error: 'rgba(244, 67, 54, 1)',
      warning: 'rgba(255, 152, 0, 1)',
      info: 'rgba(33, 150, 243, 1)',
      success: 'rgba(76, 175, 80, 1)',
      divider: 'rgba(255, 255, 255, 0.12)',
      action: {
        active: 'rgba(255, 255, 255, 0.7)',
        hover: 'rgba(255, 255, 255, 0.1)',
        selected: 'rgba(255, 255, 255, 0.2)',
        disabled: 'rgba(255, 255, 255, 0.3)',
        disabledBackground: 'rgba(255, 255, 255, 0.12)'
      }
    },
    light: {
      primary: 'rgba(25, 118, 210, 1)',
      secondary: 'rgba(156, 39, 176, 1)',
      background: 'rgba(255, 255, 255, 1)',
      paper: 'rgba(245, 245, 245, 1)',
      text: 'rgba(0, 0, 0, 0.87)',
      textSecondary: 'rgba(36, 36, 36, 0.6)',
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
