const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  expoConfig,
  { ignores: ['dist/*', 'node_modules/*', 'android/*', 'ios/*', '.expo/*'] },
  {
    // Las fábricas de jest.mock necesitan require y los mocks no son componentes reales.
    files: ['__tests__/**'],
    rules: { '@typescript-eslint/no-require-imports': 'off', 'react-hooks/exhaustive-deps': 'off' },
  },
]);
