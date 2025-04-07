import React from "react";

export const createAutocompleteComponent = (module) => props => {
  const {
    onChange,
    options = [],
    value,
    ...rest
  } = props;

  const handleChange = (event, newValue) => {
    const selectedIndices = Array.isArray(newValue) 
      ? newValue.map(v => options.findIndex(opt => 
          typeof opt === 'object' ? opt.value === v.value : opt === v
        ))
      : newValue ? [options.findIndex(opt => 
          typeof opt === 'object' ? opt.value === newValue.value : opt === newValue
        )] : [];

    const selectionData = {
      selected: newValue,
      selectedIndices,
      totalSelected: Array.isArray(newValue) ? newValue.length : (newValue ? 1 : 0)
    };

    if (onChange) {
      onChange(event, newValue, selectionData);
    }
  };

  return React.createElement(module.default, {
    ...rest,
    options,
    value,
    onChange: handleChange,
    getOptionLabel: (option) => {
      if (option == null) return '';
      if (typeof option === 'object' && option.label) return option.label;
      return String(option);
    },
    isOptionEqualToValue: (option, value) => {
      if (!option || !value) return false;
      if (option === value) return true;
      if (typeof option === 'object' && typeof value === 'object') {
        return option.value === value.value;
      }
      return false;
    }
  });
};

export const createSelectComponent = (module) => props => {
  const {
    onChange,
    value,
    children,
    ...rest
  } = props;

  const handleChange = (event) => {
    const selectedValue = event.target.value;
    const selectedOption = React.Children.toArray(children)
      .find(child => child.props.value === selectedValue);

    const selectionData = {
      value: selectedValue,
      option: selectedOption?.props?.id || '',
      label: selectedOption?.props?.children || selectedValue
    };

    if (onChange) {
      onChange(event, selectionData);
    }
  };

  return React.createElement(module.default, {
    ...rest,
    value,
    onChange: handleChange,
    children
  });
};
