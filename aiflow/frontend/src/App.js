import React, { useMemo } from 'react';
import { WebSocketProvider } from './context/WebSocketContext';
import ElementsApp from './components/elementsApp';
import { CssBaseline } from '@mui/material';
import ElementsTheme, { getInitialThemeColors } from './components/elementsTheme';
import { themeConfig } from './config/theme.config';

function App() {
    const defaultTheme = useMemo(() => {
        const initialColors = getInitialThemeColors();
        console.log('App - Using base mode:', themeConfig.defaultMode);
        return {
            base: themeConfig.defaultMode,
            backgroundColor: initialColors.background,
            secondaryBackgroundColor: initialColors.paper,
            primaryColor: initialColors.primary,    // Use primary from theme presets
            textColor: initialColors.text,
            fadedText60: initialColors.textSecondary
        };
    }, []);

    return (
        <ElementsTheme theme={defaultTheme}>
            <CssBaseline enableColorScheme />
            <WebSocketProvider url="ws://localhost:8888">
                <ElementsApp theme={defaultTheme} />
            </WebSocketProvider>
        </ElementsTheme>
    );
}

export default App;
