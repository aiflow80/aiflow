export const EVENT_TYPES = {
  CLICK: 'click',
  CHANGE: 'change',
  BLUR: 'blur',
  AUTOCOMPLETE_CHANGE: 'autocomplete-change',
  SELECT_CHANGE: 'select-change',
  FILE_CHANGE: 'file-change',
  FILTER_CHANGE: 'filter-change',
  SORT_CHANGE: 'sort-change',
  PAGINATION_CHANGE: 'pagination-change',
  MESSAGE: 'message',
};

export const sanitizeValue = (value) => {
  if (value === null || value === undefined) return null;
  if (typeof value === 'function') return '[Function]';
  if (value instanceof File) {
    return { name: value.name, type: value.type, size: value.size };
  }
  if (Array.isArray(value)) return value.map(sanitizeValue);
  if (typeof value === 'object') {
    return Object.entries(value).reduce((acc, [key, val]) => {
      acc[key] = sanitizeValue(val);
      return acc;
    }, {});
  }
  return value;
};

export const createEventPayload = (key, type, value) => ({
  key,
  type,
  value,
  timestamp: Date.now()
});
