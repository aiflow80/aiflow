import React from 'react';
import { WebSocketProvider } from './context/WebSocketContext';
import ElementsApp from './components/elementsApp';

function App() {
    return (
        <WebSocketProvider url="ws://localhost:8888">
            <ElementsApp />
        </WebSocketProvider>
    );
}

export default App;
