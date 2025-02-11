import { useCallback } from 'react';
import React from 'react';
import { loaders } from '../config/loaders';
import { validateElement, convertNode } from '../utils/renderUtils';

export const useComponentRenderer = () => {
  const renderElement = useCallback((type, module, props) => {
    try {
      validateElement(module, type);
      const LoadedElement = loaders[module](type);
      return React.createElement(LoadedElement, props);
    } catch (error) {
      console.error('Error rendering element:', error);
      return null;
    }
  }, []);

  const renderComponent = useCallback((id, hierarchy) => {
    const node = hierarchy.get(id);
    if (!node) return null;

    const { component, children } = node;
    
    if (component.type === 'text') return component.content;

    const { module = 'muiElements', type, props = {} } = component;

    try {
      const LoadedElement = loaders[module](type);
      const processedProps = { ...props };
      delete processedProps.parent_id;
      delete processedProps.order;

      const convertedProps = Object.entries(processedProps).reduce((acc, [key, value]) => {
        acc[key] = convertNode(value, (node) => 
          renderElement(node.type, node.module, node.props)
        );
        return acc;
      }, {});

      const renderedChildren = [
        ...(component.children || []).map(child => 
          child.type === 'text' ? child.content : renderComponent(child.id, hierarchy)
        ),
        ...children.map(childId => renderComponent(childId, hierarchy))
      ].filter(Boolean);

      return React.createElement(
        LoadedElement,
        { key: id, ...convertedProps },
        renderedChildren.length > 0 ? renderedChildren : undefined
      );

    } catch (error) {
      console.error('Error rendering component:', error);
      return null;
    }
  }, [renderElement]);

  return { renderComponent };
};
