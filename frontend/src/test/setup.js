import '@testing-library/jest-dom'

// Mock window.scrollTo which is not implemented in jsdom
Object.defineProperty(window, 'scrollTo', {
  value: () => {},
  writable: true
})