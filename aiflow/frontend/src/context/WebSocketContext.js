import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

const WebSocketContext = createContext(null);
const WS_URL = 'ws://localhost:8888/ws';

export const WebSocketProvider = ({ children }) => {
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [clientId, setClientId] = useState(null);  // Add this line
  const wsRef = useRef(null);

  const connect = useCallback(() => {
    // Only attempt to connect if we don't have an active connection
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      try {
        // Get client_id from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session_id');

        const socket = new WebSocket(WS_URL);
        wsRef.current = socket;

        socket.onopen = () => {
          console.log('WebSocket Connected');
          setIsConnected(true);
          setConnectionError(null);
        };

        socket.onmessage = (event) => {
          try {
            if (!event.data) {
              console.warn('Received empty message');
              return;
            }

            const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
            console.log('📥 WebSocket message received:', {
              timestamp: new Date().toISOString(),
              data: data
            });

            // Handle connection messages
            if (data.type === 'connection') {
              console.log('Connection established with ID:', data.client_id);
              setClientId(data.client_id);  // Store our client_id
              
              // Send pairing message after receiving our client_id
              if (sessionId) {
                socket.send(JSON.stringify({
                  type: 'pair',
                  client_id: sessionId,
                  sender_id: data.client_id,  // Use our assigned client_id
                  payload: 'Connection established'
                }));
              }
              return;
            }

            // Handle component updates
            if (data.type === 'component_update' && data.payload) {
              socket.dispatchEvent(new CustomEvent('component_update', {
                detail: data.payload
              }));
              return;
            }

            // Handle messages with 'from' field (server broadcasts)
            if (data.from && data.content !== undefined) {
              if (data.content === null) {
                console.warn('Received null content from server');
                return;
              }
              socket.dispatchEvent(new CustomEvent('message', {
                detail: data.content
              }));
              return;
            }

            // Handle direct message type events
            if (data.type === 'message' && data.payload) {
              socket.dispatchEvent(new CustomEvent('message', {
                detail: data.payload
              }));
              return;
            }

            console.warn('Unhandled message format:', data);
          } catch (error) {
            console.error('Error handling message:', error, event.data);
          }
        };

        socket.onclose = (event) => {
          if (event.wasClean) {
            console.log('WebSocket Closed Cleanly');
          } else {
            console.log('WebSocket Disconnected');
          }
          setIsConnected(false);
          setConnectionError('Connection closed. Server may be down.');
        };

        socket.onerror = (error) => {
          console.error('WebSocket Error:', error);
          setConnectionError('Failed to connect to server');
        };

        setWs(socket);
      } catch (error) {
        console.error('Connection error:', error);
        setConnectionError('Failed to connect to server');
        setIsConnected(false);
      }
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
      setWs(null);
    }
  }, []);

  useEffect(() => {
    connect();
    // Cleanup function
    return () => {
      disconnect();
    };
  }, []); // Only run on mount/unmount

  const socketService = {
    send: (data) => {
      if (ws?.readyState === WebSocket.OPEN) {
        const message = typeof data === 'string' ? 
          { type: 'message', payload: data } : data;
        ws.send(JSON.stringify(message));
      }
    },
    addListener: (event, callback) => {
      if (!ws) return () => {};

      const handler = (e) => {
        if (e.detail !== undefined) {
          try {
            callback(e.detail);
          } catch (error) {
            console.error(`Error in ${event} handler:`, error);
          }
        }
      };
      ws.addEventListener(event, handler);
      return () => ws.removeEventListener(event, handler);
    },
    removeListener: (event, handler) => {
      ws?.removeEventListener(event, handler);
    }
  };

  return (
    <WebSocketContext.Provider value={{ 
      socketService,
      isConnected,
      connectionError,
      clientId  // Make clientId available in context if needed
    }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
