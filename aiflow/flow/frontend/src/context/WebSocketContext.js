import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';

const WebSocketContext = createContext(null);
const WS_URL = 'ws://localhost:8888/ws';
// Add max chunk size constant (1MB)
const MAX_CHUNK_SIZE = 3 * 1024 * 1024; 

// Helper function to determine if a message needs to be chunked
const shouldChunkMessage = (data) => {
  if (typeof data !== 'object' || !data) return false;
  
  // Check if this is a file upload with base64 data
  if (data.payload.type === 'file-change' && 
      data.payload.fileEvent.data &&
      data.payload.fileEvent.data.length > MAX_CHUNK_SIZE) {
    return true;
  }
  
  return false;
};

// Function to split base64 content into chunks
const splitIntoChunks = (data) => {
  const messageId = Date.now().toString() + Math.random().toString(36).substring(2, 15);
  const base64Data = data.payload.fileEvent.data;
  const chunks = [];
  
  for (let i = 0; i < base64Data.length; i += MAX_CHUNK_SIZE) {
    chunks.push(base64Data.substring(i, i + MAX_CHUNK_SIZE));
  }
  
  return {
    messageId,
    totalChunks: chunks.length,
    chunks,
    originalMessage: data
  };
};

export const WebSocketProvider = ({ children }) => {
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [clientId, setClientId] = useState(null);
  const wsRef = useRef(null);

  const connect = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      try {
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
            if (!event.data) return console.warn('Received empty message');
            let data = typeof event.data === 'string'
              ? JSON.parse(event.data.replace(/:\s*NaN\s*([,}])/g, ': null$1')
                                  .replace(/:\s*Infinity\s*([,}])/g, ': null$1')
                                  .replace(/:\s*-Infinity\s*([,}])/g, ': null$1'))
              : event.data;
            if (data.type === 'connection') {
              console.log('Connection established with ID:', data.client_id);
              setClientId(data.client_id);
              sessionId && socket.send(JSON.stringify({ type: 'pair', client_id: sessionId, sender_id: data.client_id, payload: 'Connection established' }));
              return console.log('Pair message sent:', data.client_id);
            } else if (data.type === 'component_update' && data.payload) {
              return socket.dispatchEvent(new CustomEvent('component_update', { detail: data.payload }));
            } else if (data.from && data.content !== undefined) {
              if (data.content === null) return console.warn('Received null content from server');
              return socket.dispatchEvent(new CustomEvent('message', { detail: data.content }));
            } else if (data.type === 'message' && data.payload) {
              return socket.dispatchEvent(new CustomEvent('message', { detail: data.payload }));
            } else if (data.type === 'paired') {
              return socket.dispatchEvent(new CustomEvent('component_update', { detail: data.payload }));
            } else if (['chunk_ack', 'chunks_complete_ack'].includes(data.type)) {
              return;
            } else if (data.type === 'chunked_message_complete') {
              return console.log(`Completed sending all chunks ${data.messageId}`);
            }
            console.warn('Unhandled message format:', data);
          } catch (error) { console.error('Error handling message:', error, event.data); }
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
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const sendChunk = async (chunk) => {
    if (ws?.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify(chunk));
        return true;
      } catch (error) {
        console.error("Error sending chunk:", error);
      }
    }
    console.error("WebSocket not connected, failed to send chunk");
    return false;
  };

  const socketService = {
    send: async (data) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket not open, skipping sending");
        return;
      }
      if (shouldChunkMessage(data)) {
        const { messageId, totalChunks, chunks, originalMessage } = splitIntoChunks(data);
        console.log(`Starting to send ${totalChunks} chunks for message ${messageId}`);
        
        // Send all chunks concurrently
        const chunkPromises = chunks.map((chunkData, index) => {
          const chunkMessage = JSON.parse(JSON.stringify(originalMessage));
          chunkMessage.payload.fileEvent.data = chunkData;
    
          const message = {
            type: 'chunked_message',
            messageId: messageId,
            chunkIndex: index,
            totalChunks: totalChunks,
            payload: chunkMessage
          };
    
          return sendChunk(message).then(sent => {
            if (sent) {
              console.log(`Sent chunk ${index + 1}/${totalChunks} for message ${messageId}`);
            } else {
              console.error(`Failed to send chunk ${index + 1}/${totalChunks}`);
            }
          });
        });
    
        await Promise.all(chunkPromises);
        console.log(`Completed sending all chunks for message ${messageId}`);
      } else {
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
      clientId
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
