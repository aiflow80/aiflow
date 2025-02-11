import React, { useEffect, useState, useCallback } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { dequal } from "dequal/lite";
import { useWebSocket } from '../context/WebSocketContext';
import { CssBaseline } from '@mui/material';
import ElementsTheme from "./elementsTheme";
import { sanitizeValue } from '../utils/eventUtils';
import { useComponentRenderer } from '../hooks/useComponentRenderer';
import StandardErrorPage from './StandardErrorPage';

const ElementsApp = ({ args, theme }) => {
  const [components, setComponents] = useState(new Map());
  const { socketService, isConnected, connectionError } = useWebSocket();
  const { renderComponent } = useComponentRenderer();

  const send = useCallback(async (data) => {
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
  }, [socketService]);

  const buildHierarchy = useCallback((componentsMap) => {
    const hierarchy = new Map();
    const roots = [];
    
    componentsMap.forEach((comp) => {
      hierarchy.set(comp.id, {
        component: comp,
        children: [],
        parentId: comp.parentId,
        order: comp.props?.order || 0
      });
    });
    
    componentsMap.forEach((comp) => {
      const node = hierarchy.get(comp.id);
      if (node.parentId && hierarchy.has(node.parentId)) {
        hierarchy.get(node.parentId).children.push(comp.id);
      } else {
        roots.push(comp.id);
      }
    });
    
    const sortByOrder = (a, b) => 
      (hierarchy.get(a)?.order || 0) - (hierarchy.get(b)?.order || 0);

    hierarchy.forEach(node => node.children.sort(sortByOrder));
    roots.sort(sortByOrder);
    
    return { hierarchy, roots };
  }, []);

  useEffect(() => {
    if (!socketService) return;

    const handleComponentUpdate = (payload) => {
      if (!payload?.component) return;
      
      console.debug('Received component update:', payload.component);
      
      setComponents(prev => {
        const next = new Map(prev);
        const { id, parentId, order } = payload.component;
        
        // Validate component creation order
        if (next.has(id)) {
          console.debug('Component already exists:', id);
          return prev;
        }

        // Store component with order information
        if (payload.component.type === 'text') {
          next.set(id, {
            id,
            type: 'text',
            content: payload.component.content,
            parentId,
            order
          });
        } else {
          next.set(id, { ...payload.component, parentId, order });
        }
        
        console.debug('Updated components:', Array.from(next.entries()));
        return next;
      });
    };

    const componentHandler = socketService.addListener('component_update', handleComponentUpdate);
    return () => componentHandler?.();
  }, [socketService]);

  if (!isConnected) {
    return (
      <StandardErrorPage
        title={connectionError ? 'Connection Error' : 'Connecting...'}
        message={connectionError || 'Attempting to connect to server... Please wait.'}
        checkList={connectionError ? [
          'The server is running and accessible',
          'Your network connection is stable',
          'The server URL is correct'
        ] : null}
      />
    );
  }

  const { hierarchy, roots } = buildHierarchy(components);

  return (
    <ElementsTheme theme={theme}>
      <CssBaseline />
      <ErrorBoundary 
        fallback={
          <StandardErrorPage
            title="Rendering Error"
            message="An error occurred while rendering the component."
            theme={theme}
          />
        }
        onError={(error) => send({ error: error.message })}
      >
        <div style={{ 
          minHeight: '100vh',
          padding: '16px',
          backgroundColor: theme?.backgroundColor
        }}>
          {roots.map(rootId => renderComponent(rootId, hierarchy))}
        </div>
      </ErrorBoundary>
    </ElementsTheme>
  );
};

export default React.memo(ElementsApp, dequal);
