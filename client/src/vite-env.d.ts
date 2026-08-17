/// <reference types="vite/client" />

// Vite statically replaces process.env.NODE_ENV at build time.
declare namespace NodeJS {
  interface ProcessEnv {
    readonly NODE_ENV: 'development' | 'production' | 'test'
  }
}
