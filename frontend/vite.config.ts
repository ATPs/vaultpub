import { defineConfig } from "vite";
import { transform } from "esbuild";

export default defineConfig({
  base: "/static/vaultpub/",
  plugins: [
    {
      name: "format-entry-bundle",
      async generateBundle(_, bundle) {
        for (const entryName of ["app.js", "slides.js"]) {
          const entry = bundle[entryName];
          if (!entry || entry.type !== "chunk") continue;
          const formatted = await transform(entry.code, {
            format: "esm",
            legalComments: "none",
            minify: false,
            target: "esnext",
          });
          entry.code = formatted.code;
        }
      },
    },
  ],
  build: {
    outDir: "../src/vaultpub/django_app/static/vaultpub",
    emptyOutDir: true,
    cssCodeSplit: true,
    rollupOptions: {
      input: {
        app: "src/app.ts",
        slides: "src/slides.ts",
      },
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name || "";
          if (name === "app.css" || name === "slides.css") return name;
          return "assets/[name]-[hash][extname]";
        },
      },
    },
  },
  css: {
    modules: false,
  },
});
