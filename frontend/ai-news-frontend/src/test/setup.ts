/**
 * Test Setup Configuration
 * Configuración de setup para tests del frontend
 */

import '@testing-library/jest-dom'
import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extender expect con matchers de testing-library
expect.extend(matchers)

// Cleanup después de cada test
afterEach(() => {
  cleanup()
})

// Mock para IntersectionObserver
global.IntersectionObserver = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock para ResizeObserver
global.ResizeObserver = vi.fn(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock para window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock para window.HTMLMediaElement
Object.defineProperty(window, 'HTMLMediaElement', {
  writable: true,
  value: class HTMLMediaElement {
    play = vi.fn()
    pause = vi.fn()
    load = vi.fn()
    src = ''
  },
})

// Mock para navigator.clipboard
Object.defineProperty(navigator, 'clipboard', {
  value: {
    writeText: vi.fn(),
    readText: vi.fn(),
  },
})

// Mock para scrollTo
Object.defineProperty(window, 'scrollTo', {
  value: vi.fn(),
})

// Mock para requestAnimationFrame
global.requestAnimationFrame = vi.fn(callback => setTimeout(callback, 0))
global.cancelAnimationFrame = vi.fn()

// Mock para crypto.randomUUID
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: vi.fn(() => 'mock-uuid'),
  },
})

// Mock para console en tests (opcional)
if (import.meta.env.DEV) {
  console.log = vi.fn()
  console.warn = vi.fn()
  console.error = vi.fn()
}

// Mock para fetch si es necesario
global.fetch = vi.fn()

// Configuración para mock de APIs
export const mockApiResponse = {
  articles: [
    {
      id: '1',
      title: 'Test Article',
      content: 'Test content',
      description: 'Test description',
      url: 'https://example.com',
      publishedAt: '2023-12-01T10:00:00Z',
      source: {
        id: 'test-source',
        name: 'Test Source',
        credibilityScore: 0.8,
      },
    },
  ],
}

export const mockErrorResponse = {
  error: {
    code: 'TEST_ERROR',
    message: 'Test error message',
  },
}