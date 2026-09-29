/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "react": path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      "react/jsx-runtime": path.resolve(__dirname, "node_modules/react/jsx-runtime"),
    },
    dedupe: ["react", "react-dom"],
  },
  server: {
    port: 5173,
    strictPort: false,
    host: true,
  },
  preview: {
    port: 5173,
    strictPort: false,
  },
  build: {
    sourcemap: false,
    target: "es2022",
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    server: {
      deps: {
        inline: ["lucide-react"],
      },
    },
  },
});
