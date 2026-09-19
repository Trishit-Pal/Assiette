import { defineConfig } from "vite";

const backend = "http://127.0.0.1:8000";

export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      "/health": backend,
      "/query": backend,
      "/retrieve": backend,
      "/compose": backend,
      "/venues": backend,
      "/refresh-runs": backend,
      "/auth": backend,
      "/internal": backend,
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
