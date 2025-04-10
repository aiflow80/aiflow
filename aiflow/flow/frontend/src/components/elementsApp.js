import React, { useEffect, useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { jsx } from "@emotion/react";
import Box from "@mui/material/Box";
import ElementsTheme from "./elementsTheme";
import ElementsLoading from "./elementsLoading";
import loadMuiElements from "./modules/mui/elements";
import loadMuiIcons from "./modules/mui/icons";
import loadMuiLab from "./modules/mui/lab";
import { useWebSocket } from "../context/WebSocketContext";

// Constants
const loaders = { muiElements: loadMuiElements, muiIcons: loadMuiIcons, muiLab: loadMuiLab };
const EVENT_TYPES = {
  CLICK: 'click', 
  CHANGE: 'change', 
  BLUR: 'blur', 
  AUTOCOMPLETE_CHANGE: 'autocomplete-change',
  SELECT_CHANGE: 'select-change', 
  FILE_CHANGE: 'file-change', 
  FILTER_CHANGE: 'filter-change',
  SORT_CHANGE: 'sort-change', 
  PAGINATION_CHANGE: 'pagination-change'
};

// Helper functions
const sanitizeValue = (value) => {
  if (value === null || value === undefined) return null;
  if (typeof value === 'object' && value !== null && value.$$typeof) return '[React Element]';
  if (typeof value === 'function') return '[Function]';
  if (value instanceof File) return { name: value.name, type: value.type, size: value.size };
  if (Array.isArray(value)) return value.map(sanitizeValue);
  if (typeof value === 'object') {
    const cleaned = {};
    for (const [key, val] of Object.entries(value)) cleaned[key] = sanitizeValue(val);
    return cleaned;
  }
  return value;
};

const createEventPayload = (key, type, value) => ({ key, type, value, timestamp: Date.now() });

const send = async (data) => {
  try {
    const sanitizedData = {
      ...data, 
      value: sanitizeValue(data.value),
      formEvents: data.formEvents ? sanitizeValue(data.formEvents) : null,
      timestamp: Date.now()
    };
    if (window.socketService) {
      const urlParams = new URLSearchParams(window.location.search);
      const sessionId = urlParams.get('session_id');
      if (sessionId) {
        window.socketService.send({
          type: 'events', 
          client_id: sessionId,
          sender_id: window.clientId, 
          payload: sanitizedData
        });
      }
    }
  } catch (error) { console.error('Failed to serialize data:', error); }
};

const handleFileEvent = async (event, key, socketService, clientId, setLoadingState) => {
  try {
    if (!event?.target?.files?.length) return;
    const file = event.target.files[0];
    const reader = new FileReader();

    // Set loading to true at the start of file reading
    setLoadingState(true);

    reader.onload = () => {
      send({
        key: key,
        type: EVENT_TYPES.FILE_CHANGE,
        value: null,
        fileEvent: {
          data: reader.result,
          name: file.name,
          type: file.type,
          size: file.size
        },
        timestamp: Date.now()
      }, socketService, clientId);
      
      // Set loading back to false when file is processed
      setLoadingState(false);
    };

    reader.readAsDataURL(file);
  } catch (error) {
    console.error('File handling error:', error);
    send({}, socketService, clientId);
    // Make sure to reset loading state on error
    setLoadingState(false);
  }
};

const evaluateFunction = (funcString) => {
  // Validate function string to prevent malicious code execution
  if (!funcString || typeof funcString !== 'string' || !funcString.startsWith('(params)')) {
    console.error('Invalid function string format');
    return null;
  }

  const context = {
    TextField: loaders.muiElements("TextField"),
    React, 
    createElement: React.createElement
  };
  
  // eslint-disable-next-line no-new-func
  const func = new Function(...Object.keys(context), `return ${funcString}`);
  return func(...Object.values(context));
};

const convertNode = (node, renderElement) => {
  if (node === null || node === undefined) return node;
  if (typeof node !== "object")
    return (typeof node === "string" && node.startsWith("(params)")) ? evaluateFunction(node) : node;
  if (Array.isArray(node)) return node.map(n => convertNode(n, renderElement));
  if (node.type && node.module) return renderElement(node);

  const newObj = {};
  for (const key in node) newObj[key] = convertNode(node[key], renderElement);
  return newObj;
};

const validateElement = (module, element) => {
  if (module === "text") return;
  if (!loaders.hasOwnProperty(module)) throw new Error(`Module "${module}" does not exist`);
  const elementLoader = loaders[module];
  if (typeof element !== "string" || !elementLoader(element))
    throw new Error(`Element "${element}" does not exist in module "${module}"`);
};

// Main component
const ElementsApp = ({ args, theme }) => {
  // State
  const [uiTree, setUiTree] = useState([]);
  const [formEvents, setFormEvents] = useState({});
  const [componentsMap, setComponentsMap] = useState({});
  const [streamingStart, setStreamingStart] = useState(null);
  const [streamingEnd, setStreamingEnd] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  // eslint-disable-next-line no-unused-vars
  const [previousComponentsMap, setPreviousComponentsMap] = useState({});
  const { socketService, clientId } = useWebSocket();

  // Set global references
  useEffect(() => {
    window.socketService = socketService;
    window.clientId = clientId;
  }, [socketService, clientId]);

  // Event handling functions
  function sendEvent(data) { send(data, socketService, clientId); }
  
  function handleFileEventWithContext(event, key) { 
    handleFileEvent(event, key, socketService, clientId, setIsLoading); 
  }
  
  function handleFormEvent(eventData) {
    setFormEvents(prev => ({
      ...prev, [eventData.key]: { id: eventData.key, value: eventData.value }
    }));
  }

  function handleEvent(event, key, eventType, props = {}) {
    try {
      let value;
      const targetType = event?.target?.type;
      if (targetType === 'checkbox') value = event.target.checked;
      else if (targetType === 'radio' || targetType === 'button') value = targetType === 'button' ? 'clicked' : event.target.value;
      else value = event?.target?.value;

      if (props.type === 'submit') sendEvent({ key, type: props.type, value, formEvents });
      else if (value !== undefined && value !== null && value !== '')
        handleFormEvent({ key, value });
    } catch (error) {
      console.error('Event handling error:', error);
      sendEvent(createEventPayload(key, 'error', error.message));
    }
  }

  function createEventHandlers(id, type, props) {
    if (!id) return {};
    const handlers = {};

    if (type === 'Autocomplete' || type === 'Select') {
      handlers.onChange = (event, value, selectionData) => {
        const data = type === 'Autocomplete' ? selectionData : value;
        if (props.type === 'submit') sendEvent({ key: id, type: props.type, value: data });
        else handleFormEvent({ key: id, value: data });
      };
    } else if (type === 'Input') {
      if (props?.type === 'file') {
        handlers.onChange = async (e) => {
          e.preventDefault(); e.stopPropagation();
          if (e?.target?.files?.length) {
            await handleFileEventWithContext(e, id);
            e.target.value = '';
          }
        };
        handlers.onClick = (e) => e.stopPropagation();
      } else {
        handlers.onChange = (e) => handleEvent(e, id, EVENT_TYPES.CHANGE, props);
        handlers.onClick = (e) => handleEvent(e, id, EVENT_TYPES.CLICK, props);
      }
    } else if (type === 'DataGrid') {
      handlers.onFilterModelChange = (model) => sendEvent(createEventPayload(id, EVENT_TYPES.FILTER_CHANGE, model));
      handlers.onSortModelChange = (model) => sendEvent(createEventPayload(id, EVENT_TYPES.SORT_CHANGE, model));
      handlers.onPaginationModelChange = (model) => sendEvent(createEventPayload(id, EVENT_TYPES.PAGINATION_CHANGE, model));
    } else {
      handlers.onClick = (e) => handleEvent(e, id, EVENT_TYPES.CLICK, props);
      handlers.onChange = (e) => handleEvent(e, id, EVENT_TYPES.CHANGE, props);
    }
    return handlers;
  }

  // Rendering functions
  function renderElement(node) {
    const { module, type, props = {}, children = [], content } = node;
    if (module === "text" || type === "text") return <span>{props?.content || content || ""}</span>;

    validateElement(module, type);
    const LoadedElement = loaders[module](type);
    const renderedChildren = children.map(child => renderElement(child));
    const finalProps = { ...convertNode(props, renderElement) };

    if (type === 'Input' && finalProps.type === 'file') {
      finalProps.key = `file-input-${Date.now()}`;
      finalProps.onClick = (e) => e.stopPropagation();
    }

    if (finalProps.id) {
      const eventHandlers = createEventHandlers(finalProps.id, type, finalProps);
      if (type === 'DataGrid') {
        finalProps.components = { ...finalProps.components };
        Object.entries(eventHandlers).forEach(([eventName, handler]) => {
          if (handler) {
            const existingHandler = finalProps[eventName];
            finalProps[eventName] = (...args) => {
              if (existingHandler) existingHandler(...args);
              handler(...args);
            };
          }
        });
      } else Object.assign(finalProps, eventHandlers);
    }
    return jsx(LoadedElement, finalProps, ...renderedChildren);
  }

  // Build the UI tree from component map
  function buildUiTree(map) {
    const lookup = {};
    Object.values(map).forEach(comp => lookup[comp.id] = { ...comp, children: [...(comp.children || [])] });
    Object.values(lookup).forEach(comp => {
      if (comp.parentId && lookup[comp.parentId]) lookup[comp.parentId].children.push(comp);
    });
    return Object.values(lookup).filter(c => !c.parentId);
  }

  // WebSocket listener for component updates
  useEffect(() => {
    const unsub = socketService.addListener('component_update', (payload) => {
      if (!payload?.component) {
        if (!payload?.component) {
          if (payload.message === 'stream_start') {
            setStreamingStart(payload.time_stamp);
            console.warn('New streaming session started:', payload.time_stamp);
          } else if (payload.message === 'stream_end') {
            setStreamingEnd(payload.time_stamp);
            console.warn('Streaming session ended:', payload.time_stamp);
          }
        }
        return;
      }

      setComponentsMap(prevMap => {
        const newMap = { ...prevMap };
        newMap[payload.component.id] = {
          ...payload.component,
          timestamp: payload.timestamp,
          streamingId: payload.streaming_id
        };
        return newMap;
      });
    });
    return unsub;
  }, [socketService]);

  useEffect(() => {
    if (Object.keys(componentsMap).length > 0 && streamingStart) {
      setPreviousComponentsMap(componentsMap);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamingStart]);

  // Clean up old components when streaming ends
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (Object.keys(componentsMap).length > 0 && streamingStart) {
      const newMap = { ...componentsMap };
      Object.keys(newMap).forEach(key => {
        if (newMap[key].time_stamp && newMap[key].time_stamp < streamingStart) {
          console.log("Removing component:", newMap[key]);
          delete newMap[key];
        }
      });
      setComponentsMap(newMap);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamingEnd]);

  // Update UI tree when component map changes
  useEffect(() => {
    const tree = buildUiTree(componentsMap);
    setUiTree(tree);
    console.log('UiTree updated with new component details:', tree);
    
    // Set loading to false once we have components
    if (tree.length > 0) {
      setIsLoading(false);
    }
  }, [componentsMap]);

  // Render UI elements
  const elements = uiTree.map((node, index) => (
    <React.Fragment key={node.id || index}>{renderElement(node)}</React.Fragment>
  ));

  return (
    <ElementsTheme theme={theme}>
      <Box sx={{ width: '100%', boxSizing: 'border-box', padding: '20px' }}>
        <ErrorBoundary
          fallback={<div style={{
            padding: '20px', margin: '20px', backgroundColor: '#ffebee',
            border: '1px solid #ef5350', borderRadius: '4px', minHeight: '800px', color: '#d32f2f'
          }}>
            An error occurred while rendering the component.
          </div>}
          onError={(error) => sendEvent({ error: error.message })}>
          {isLoading ? <ElementsLoading /> : elements}
        </ErrorBoundary>
      </Box>
    </ElementsTheme>
  );
};

export default ElementsApp;