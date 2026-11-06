import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// Tauri drives the dev server; keep the port fixed so tauri.conf.json matches.
export default defineConfig({
  plugins: [svelte()],
  clearScreen: false,
  server: { port: 5183, strictPort: true },
  build: { target: "chrome105", minify: "esbuild", sourcemap: false },
});
