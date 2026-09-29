/// <reference types="vite/client" />

declare module "*.css";
declare module "*.jsx";
declare module "./pages/dispatcher/*";
declare module "./pages/storemanager/*";

declare module 'leaflet/dist/images/*.png' {
  const src: string;
  export default src;
}

declare module 'node:fs' {
  export function readdirSync(path: string): string[];
  export function readFileSync(path: string, encoding: string): string;
  export function statSync(path: string): { isDirectory(): boolean };
}

declare module 'node:path' {
  export function join(...paths: string[]): string;
  export function resolve(...paths: string[]): string;
  export function basename(path: string): string;
}

declare const process: {
  cwd: () => string;
};
