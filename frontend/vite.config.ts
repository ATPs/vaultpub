import { defineConfig } from "vite";

export default defineConfig({
  base: "/static/vaultpub/",
  build: {
    outDir: "../src/vaultpub/django_app/static/vaultpub",
    emptyOutDir: true,
    cssCodeSplit: false,
    rollupOptions: {
      input: "src/app.ts",
      output: {
        entryFileNames: "app.js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name || "";
          if (name.endsWith(".css")) return "app.css";
          return "assets/[name]-[hash][extname]";
        },
      },
    },
  },
  css: {
    modules: false,
  },
});
