import { useEffect, useState } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";
import { alpha, darken, lighten } from '@mui/material/styles';

const baseTheme = {
  dark: {
    palette: {
      mode: 'dark',
      primary: {
        main: '#90caf9',
        light: '#e3f2fd',
        dark: '#42a5f5',
        contrastText: '#000000',
      },
      secondary: {
        main: '#f48fb1',
        light: '#fce4ec',
        dark: '#f06292',
        contrastText: '#000000',
      },
      background: {
        default: '#121212',
        paper: '#1e1e1e',
      },
      text: {
        primary: '#ffffff',
        secondary: 'rgba(255, 255, 255, 0.7)',
        disabled: 'rgba(255, 255, 255, 0.5)',
      },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: '#121212',
            color: '#ffffff'
          }
        }
      },
      MuiCard: {
        defaultProps: {
          elevation: 1
        },
        styleOverrides: {
          root: ({ theme }) => ({
            backgroundColor: theme.palette.background.paper,
            borderColor: theme.palette.divider,
            boxShadow: theme.shadows[1]
          })
        }
      },
      MuiTypography: {
        styleOverrides: {
          h2: ({ theme }) => ({
            color: theme.palette.primary.main,
            fontWeight: 500
          }),
          h4: ({ theme }) => ({
            color: theme.palette.primary.main,
            fontWeight: 400
          }),
          body1: ({ theme }) => ({
            color: theme.palette.text.primary
          })
        }
      },
      MuiSvgIcon: {
        styleOverrides: {
          root: ({ theme }) => ({
            color: theme.palette.primary.main,
            '&:hover': {
              color: theme.palette.primary.light
            }
          })
        }
      },
      MuiStack: {
        defaultProps: {
          spacing: 2
        },
        styleOverrides: {
          root: {
            alignItems: 'center'
          }
        }
      }
    }
  },
  light: {
    palette: {
      mode: 'light',
      primary: {
        main: '#1976d2',
        light: '#42a5f5',
        dark: '#1565c0',
        contrastText: '#ffffff',
      },
      secondary: {
        main: '#dc004e',
        light: '#ff4081',
        dark: '#9a0036',
        contrastText: '#ffffff',
      },
      background: {
        default: '#ffffff',
        paper: '#f5f5f5',
      },
      text: {
        primary: 'rgba(0, 0, 0, 0.87)',
        secondary: 'rgba(0, 0, 0, 0.6)',
        disabled: 'rgba(0, 0, 0, 0.38)',
      },
    },
  },
};

const getCommonComponents = (mode) => ({
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        scrollbarColor: mode === 'dark' ? '#6b6b6b #2b2b2b' : '#959595 #f5f5f5',
        '&::-webkit-scrollbar': {
          width: '8px',
          height: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: mode === 'dark' ? '#2b2b2b' : '#f5f5f5',
        },
        '&::-webkit-scrollbar-thumb': {
          background: mode === 'dark' ? '#6b6b6b' : '#959595',
          borderRadius: '4px',
        },
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        textTransform: 'none',
        borderRadius: '4px',
      },
    },
    defaultProps: {
      disableElevation: true,
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        backgroundImage: 'none',
      },
    },
    defaultProps: {
      elevation: 0,
    },
  },
  MuiCard: {
    defaultProps: {
      elevation: 1
    },
    styleOverrides: {
      root: {
        backgroundImage: 'none',
        backgroundColor: mode === 'dark' ? '#1e1e1e' : '#ffffff',
        borderRadius: '8px'
      }
    }
  },
  MuiTextField: {
    defaultProps: {
      variant: 'outlined',
      size: 'small',
    },
  },
  MuiDialog: {
    defaultProps: {
      PaperProps: {
        elevation: 2,
      },
    },
  },
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        fontSize: '0.75rem',
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: '4px',
      },
    },
  },
});

const ElementsTheme = ({ children, theme }) => {
  const defaultMode = 'dark';
  
  const [elementsTheme, setElementsTheme] = useState(createTheme({
    ...baseTheme[defaultMode],
    components: {
      ...baseTheme[defaultMode].components,
      ...getCommonComponents(defaultMode)
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      button: {
        textTransform: 'none',
      },
    },
    shape: {
      borderRadius: 4,
    },
  }));

  useEffect(() => {
    if (theme) {
      const mode = theme.base === 'light' ? 'light' : 'dark';
      const baseColors = baseTheme[mode];
      
      const newTheme = createTheme({
        ...baseColors,
        palette: {
          ...baseColors.palette,
          primary: {
            ...baseColors.palette.primary,
            main: theme.primaryColor || baseColors.palette.primary.main,
          },
          background: {
            default: theme.backgroundColor || baseColors.palette.background.default,
            paper: theme.secondaryBackgroundColor || baseColors.palette.background.paper,
          },
          text: {
            primary: theme.textColor || baseColors.palette.text.primary,
            secondary: theme.fadedText60 || baseColors.palette.text.secondary,
          },
        },
        components: {
          ...baseColors.components,
          ...getCommonComponents(mode)
        },
        typography: {
          fontFamily: theme.font || '"Roboto", "Helvetica", "Arial", sans-serif',
          button: {
            textTransform: 'none',
          },
        },
        shape: {
          borderRadius: 4,
        },
      });

      setElementsTheme(newTheme);
    }
  }, [theme]);

  return <ThemeProvider theme={elementsTheme}>{children}</ThemeProvider>;
};

export default ElementsTheme;
