/**
 * Jest Configuration for ARC-8
 * ES Modules support for PQC testing
 */

export default {
  // ES modules support (type: module in package.json handles .js)
  transform: {},

  // Test environment
  testEnvironment: 'node',

  // Test file patterns
  testMatch: [
    '**/scripts/**/__tests__/**/*.test.js',
    '**/tests/**/*.test.js'
  ],

  // Module resolution
  moduleFileExtensions: ['js', 'json'],

  // Root directories
  roots: ['<rootDir>/scripts'],

  // Coverage configuration
  collectCoverageFrom: [
    'scripts/**/*.js',
    '!scripts/**/__tests__/**',
    '!**/node_modules/**'
  ],

  // Verbose output
  verbose: true,

  // Timeout for async tests
  testTimeout: 30000,

  // Globals for crypto
  globals: {
    crypto: true
  }
};
