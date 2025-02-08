import React, { useEffect, useState, useCallback } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { dequal } from "dequal/lite";
import { jsx } from "@emotion/react";
import { useWebSocket } from '../context/WebSocketContext';
import { CssBaseline } from '@mui/material';

import ElementsResizer from "./elementsResizer";
import ElementsTheme from "./elementsTheme";

import loadMuiElements from "./modules/mui/elements";
import loadMuiIcons from "./modules/mui/icons";
import loadMuiLab from "./modules/mui/lab";

const loaders = {
  muiElements: loadMuiElements,
  muiIcons: loadMuiIcons,
  muiLab: loadMuiLab,
};

const EVENT_TYPES = {
  CLICK: 'click',
  CHANGE: 'change',
  BLUR: 'blur',
  AUTOCOMPLETE_CHANGE: 'autocomplete-change',
  SELECT_CHANGE: 'select-change',
  FILE_CHANGE: 'file-change',  // Add new event type
  FILTER_CHANGE: 'filter-change',
  SORT_CHANGE: 'sort-change',
  PAGINATION_CHANGE: 'pagination-change',
  MESSAGE: 'message',  // Add message event type
};

const sanitizeValue = (value) => {
  if (value === null || value === undefined) {
    return null;
  }
  
  if (typeof value === 'function') {
    return '[Function]';
  }
  
  if (value instanceof File) {
    return {
      name: value.name,
      type: value.type,
      size: value.size
    };
  }
  
  if (Array.isArray(value)) {
    return value.map(sanitizeValue);
  }
  
  if (typeof value === 'object') {
    const cleaned = {};
    for (const [key, val] of Object.entries(value)) {
      cleaned[key] = sanitizeValue(val);
    }
    return cleaned;
  }
  
  return value;
};

const createEventPayload = (key, type, value) => ({
  key,
  type,
  value,
  timestamp: Date.now()
});

const evaluateFunction = (funcString) => {
  // Create a context with MUI components
  const context = {
    TextField: loaders.muiElements("TextField"),
    React: React,
    createElement: React.createElement
  };

  // eslint-disable-next-line 
  const func = new Function(...Object.keys(context), `return ${funcString}`);
  return func(...Object.values(context));
};

const convertNode = (node, renderElement) => {
  if (node === null || node === undefined) return node;
  if (typeof node !== "object") {
    if (typeof node === "string" && node.startsWith("(params)")) {
      return evaluateFunction(node);
    }
    return node;
  }
  if (Array.isArray(node)) {
    return node.map(n => convertNode(n, renderElement));
  }
  if (node.type && node.module) {
    return renderElement(node);
  }

  const newObj = {};
  for (const key in node) {
    newObj[key] = convertNode(node[key], renderElement);
  }
  return newObj;
};

const validateElement = (module, element) => {
  if (!loaders.hasOwnProperty(module)) {
    throw new Error(`Module "${module}" does not exist`);
  }

  const elementLoader = loaders[module];
  if (typeof element !== "string" || !elementLoader(element)) {
    console.error(`Element "${element}" does not exist in module "${module}"`);
    throw new Error(`Element "${element}" does not exist in module "${module}"`);
  }
};

const preprocessJsonString = (jsonString) => {
  try {
    // First try to locate any NaN values
    console.debug('Starting JSON preprocessing');
    
    // Convert standalone NaN values to null using multiple patterns
    let processed = jsonString
      // Handle key-value pairs with NaN
      .replace(/"[^"]+"\s*:\s*NaN/g, match => match.replace(/NaN$/, 'null'))
      // Handle array elements that are NaN
      .replace(/,\s*NaN\s*,/g, ',null,')
      // Handle NaN at start of array
      .replace(/\[\s*NaN\s*,/g, '[null,')
      // Handle NaN at end of array
      .replace(/,\s*NaN\s*\]/g, ',null]')
      // Handle single NaN in array
      .replace(/\[\s*NaN\s*\]/g, '[null]')
      // Handle any remaining NaN values
      .replace(/:\s*NaN\b/g, ': null');

    console.debug('Preprocessing complete');
    return processed;
  } catch (error) {
    console.error('Error during preprocessing:', error);
    throw error;
  }
};

const ElementsApp = ({ args, theme }) => {
  const [components, setComponents] = useState(new Map());
  const { socketService, isConnected, connectionError } = useWebSocket();

  // Send events through socket service
  const send = async (data) => {
    if (!socketService) {
      console.warn('WebSocket service not available');
      return;
    }

    try {
      const sanitizedData = {
        ...data,
        value: sanitizeValue(data.value),
        formEvents: data.formEvents ? sanitizeValue(data.formEvents) : null,
        timestamp: Date.now()
      };
      
      socketService.send({
        type: 'event',
        payload: sanitizedData
      });
    } catch (error) {
      console.error('Error sending event:', error);
    }
  };

  const renderComponent = useCallback((component) => {
    if (!component || !component.type) {
      console.error('Invalid component:', component);
      return null;
    }

    try {
      const { module = 'muiElements', type, props = {}, children = [], id } = component;
      
      validateElement(module, type);
      const LoadedElement = loaders[module](type);

      // Process event handlers in props
      const processedProps = {...props};
      if (props.onClick) {
        processedProps.onClick = (...args) => 
          send(createEventPayload(id, EVENT_TYPES.CLICK, args));
      }
      if (props.onChange) {
        processedProps.onChange = (e) => 
          send(createEventPayload(id, EVENT_TYPES.CHANGE, e.target.value));
      }
      
      const processedChildren = children.map(child => {
        if (typeof child === 'string') return child;
        if (child.type === 'text') return child.content;
        return renderComponent(child);
      }).filter(Boolean);

      return React.createElement(LoadedElement, { 
        key: id,
        ...processedProps
      }, ...processedChildren);
    } catch (error) {
      console.error('Error rendering component:', error, component);
      return null;
    }
  }, [send]);

  useEffect(() => {
    if (!socketService) return;

    const handleComponentUpdate = (payload) => {
      if (!payload || !payload.component) {
        console.warn('Invalid component update payload:', payload);
        return;
      }

      console.log('Processing component update:', payload);
      setComponents(prevComponents => {
        const newComponents = new Map(prevComponents);
        const component = payload.component;
        newComponents.set(component.id, component);
        return newComponents;
      });
    };

    const handleMessage = (payload) => {
      if (!payload) {
        console.warn('Empty message payload');
        return;
      }

      console.log('Processing message:', payload);
      // Handle component updates that come through regular messages
      if (typeof payload === 'object' && payload.type === 'component_update') {
        handleComponentUpdate(payload.payload);
      }
    };

    // Setup listeners with cleanup
    const componentHandler = socketService.addListener('component_update', handleComponentUpdate);
    const messageHandler = socketService.addListener('message', handleMessage);

    return () => {
      componentHandler && componentHandler();
      messageHandler && messageHandler();
    };
  }, [socketService]);

  if (!isConnected) {
    return (
      <div style={{
        padding: '20px',
        margin: '20px',
        backgroundColor: '#fff3e0',
        border: '1px solid #ffb74d',
        borderRadius: '4px',
        color: '#f57c00',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px'
      }}>
        <h3 style={{ margin: '0 0 10px 0' }}>
          {connectionError ? 'Connection Error' : 'Connecting...'}
        </h3>
        {connectionError && (
          <>
            <p style={{ margin: '0' }}>{connectionError}</p>
            <p style={{ margin: '0' }}>Please check if:</p>
            <ul style={{ margin: '0' }}>
              <li>The server is running and accessible</li>
              <li>Your network connection is stable</li>
              <li>The server URL is correct</li>
            </ul>
          </>
        )}
        {!connectionError && (
          <div>Attempting to connect to server... Please wait.</div>
        )}
      </div>
    );
  }

  return (
    <ElementsResizer>
      <ElementsTheme theme={theme}>
        <CssBaseline />
        <ErrorBoundary 
          fallback={
            <div style={{
              padding: '20px',
              margin: '20px',
              backgroundColor: '#ffebee',
              border: '1px solid #ef5350',
              borderRadius: '4px',
              minHeight: '800px',
              color: '#d32f2f'
            }}>
              An error occurred while rendering the component.
            </div>
          } 
          onError={(error) => send({ error: error.message })}
        >
          <div style={{ 
            minHeight: '100vh',
            padding: '24px',
            backgroundColor: theme?.backgroundColor || '#121212'
          }}>
            {Array.from(components.values())
              .filter(component => !component.parentId)
              .map(component => renderComponent(component))}
          </div>
        </ErrorBoundary>
      </ElementsTheme>
    </ElementsResizer>
  );
};

export default React.memo(ElementsApp, dequal);
