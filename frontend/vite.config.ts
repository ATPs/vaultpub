import { defineConfig } from "vite";
import { transform } from "esbuild";

export default defineConfig({
  base: "/static/vaultpub/",
  plugins: [
    {
      name: "format-entry-bundle",
      async generateBundle(_, bundle) {
        const entry = bundle["app.js"];
        if (!entry || entry.type !== "chunk") return;

        const formatted = await transform(entry.code, {
          format: "esm",
          legalComments: "none",
          minify: false,
          target: "esnext",
        });
        entry.code = formatted.code;
      },
    },
  ],
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
