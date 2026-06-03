import { defineConfig } from "vite";

export default defineConfig({
  build: {
    outDir: "../src/vaultpub/django_app/static/vaultpub",
    emptyOutDir: true,
    rollupOptions: {
      input: "src/app.ts",
      output: {
        entryFileNames: "app.js",
        assetFileNames: "app.css",
      },
    },
  },
  css: {
    modules: false,
  },
});
