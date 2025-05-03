import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vitejs.dev/config/
export default defineConfig({
  base: "/", // Replace with your repository name
  plugins: [react()], // Removed ghPages plugin
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});