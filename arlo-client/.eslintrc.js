const jsExtensions = ['.js', '.jsx']
const tsExtensions = ['.ts', '.tsx']
const allExtensions = jsExtensions.concat(tsExtensions)

module.exports = {
  env: {
    browser: true,
    node: true,
    es6: true,
    'jest/globals': true,
    'cypress/globals': true,
  },
  parser: '@typescript-eslint/parser', // Specifies the ESLint parser
  extends: [
    'airbnb',
    'plugin:import/errors',
    'plugin:import/warnings',
    'plugin:import/typescript',
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended', // Uses the recommended rules from @typescript-eslint/eslint-plugin
    'prettier/@typescript-eslint', // Uses eslint-config-prettier to disable ESLint rules from @typescript-eslint/eslint-plugin that would conflict with prettier
    'plugin:prettier/recommended', // Enables eslint-plugin-prettier and displays prettier errors as ESLint errors. Make sure this is always the last configuration in the extends array.
    'plugin:react/recommended', // Uses the recommended rules from @eslint-plugin-react
    'plugin:jsx-a11y/recommended',
    'prettier/react', // Overrides some of the rules in 'airbnb' to have more relaxed formatting in react.
    'plugin:cypress/recommended',
  ],
  globals: {
    Atomics: 'readonly',
    SharedArrayBuffer: 'readonly',
    // fetch: true, // required if using via 'jest-fetch-mock'
    fetchMock: true, // required if using via 'jest-fetch-mock'
  },
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 2018,
    project: './tsconfig.json',
    sourceType: 'module',
  },
  plugins: [
    '@typescript-eslint',
    'jest',
    'no-null',
    'react',
    'cypress',
    'jsx-a11y',
  ],
  settings: {
    react: {
      version: 'detect', // Tells eslint-plugin-react to automatically detect the version of React to use
    },
    'import/extensions': allExtensions,
    'import/parsers': {
      '@typescript-eslint/parser': tsExtensions,
    },
    'import/resolver': {
      node: {
        extensions: allExtensions,
      },
    },
  },
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'off', // Want to use it, but it requires return types for all built-in React lifecycle methods.
    '@typescript-eslint/no-non-null-assertion': 'off',
    '@typescript-eslint/no-null-keyword': 'on',
    camelcase: 'error',
    'import/no-extraneous-dependencies': [
      'error',
      {
        devDependencies: true,
      },
    ],
    'no-null/no-null': 2, // TypeScript with strictNullChecks
    'react/destructuring-assignment': 'off',
    'react/jsx-boolean-value': [2, 'never'],
    'react/jsx-filename-extension': [
      1,
      {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
      },
    ],
    strict: 0,
  },
}
