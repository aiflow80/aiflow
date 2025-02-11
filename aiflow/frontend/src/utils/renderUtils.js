import React from 'react';
import { loaders } from '../config/loaders';

export const evaluateFunction = (funcString) => {
  const context = {
    TextField: loaders.muiElements("TextField"),
    React: React,
    createElement: React.createElement
  };
  // eslint-disable-next-line 
  const func = new Function(...Object.keys(context), `return ${funcString}`);
  return func(...Object.values(context));
};

export const convertNode = (node, renderElement) => {
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
  return Object.entries(node).reduce((acc, [key, value]) => {
    acc[key] = convertNode(value, renderElement);
    return acc;
  }, {});
};

export const validateElement = (module, element) => {
  if (!loaders.hasOwnProperty(module)) {
    throw new Error(`Module "${module}" does not exist`);
  }
  if (typeof element !== "string" || !loaders[module](element)) {
    throw new Error(`Element "${element}" does not exist in module "${module}"`);
  }
};

export const preprocessJsonString = (jsonString) => {
  const patterns = [
    { from: /"[^"]+"\s*:\s*NaN/g, to: match => match.replace(/NaN$/, 'null') },
    { from: /,\s*NaN\s*,/g, to: ',null,' },
    { from: /\[\s*NaN\s*,/g, to: '[null,' },
    { from: /,\s*NaN\s*\]/g, to: ',null]' },
    { from: /\[\s*NaN\s*\]/g, to: '[null]' },
    { from: /:\s*NaN\b/g, to: ': null' }
  ];
  
  return patterns.reduce((processed, { from, to }) => 
    processed.replace(from, to), jsonString);
};
