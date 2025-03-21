import React, { useMemo } from 'react';
import { WebSocketProvider } from './context/WebSocketContext';
import ElementsApp from './components/elementsApp';
import { CssBaseline } from '@mui/material';
import ElementsTheme, { getInitialThemeColors } from './components/elementsTheme';
import { themeConfig } from './config/theme.config';

function App() {
    // Create theme once and memoize it
    const defaultTheme = useMemo(() => {
        const initialColors = getInitialThemeColors();
        return {
            base: themeConfig.defaultMode,
            backgroundColor: initialColors.background,
            secondaryBackgroundColor: initialColors.paper,
            primaryColor: initialColors.primary,
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
