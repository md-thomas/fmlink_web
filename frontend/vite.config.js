import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// `npm run dev` serves the app with hot reload and forwards /api (HTTP and
// the event WebSocket) to a station started with ./run.sh on port 8080.
// `npm run build` writes dist/, which the station's server serves.
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: { '/api': { target: 'http://localhost:8080', ws: true } },
  },
});
