// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Mock window.matchMedia для Ant Design (must be before any imports)
global.matchMedia = global.matchMedia || function (query) {
  return {
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  };
};

// Also set on window object
if (typeof window !== 'undefined') {
  window.matchMedia = window.matchMedia || global.matchMedia;
}

// Mock window.ResizeObserver
global.ResizeObserver = global.ResizeObserver || class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock API context
jest.mock('./contexts/ApiContext', () => ({
  useApi: () => ({
    screens: {
      getAll: jest.fn(),
      getById: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
    },
    components: {
      getAll: jest.fn(),
      getById: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
    },
    analytics: {
      track: jest.fn(),
      getStats: jest.fn(),
      getOverview: jest.fn(),
    },
    abTesting: {
      getAll: jest.fn(),
      create: jest.fn(),
      activate: jest.fn(),
      deactivate: jest.fn(),
    },
    templates: {
      getAll: jest.fn(),
      getById: jest.fn(),
      create: jest.fn(),
    },
  }),
  ApiProvider: ({ children }) => children,
}));

