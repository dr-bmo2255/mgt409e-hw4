import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Dev: proxy to the studio backend on :8765. Production: `npm run build` → dist/, served by FastAPI.
export default defineConfig({
  plugins: [react()],
  server: { port: 5174, proxy: { '/api': 'http://127.0.0.1:8765', '/files': 'http://127.0.0.1:8765' } },
})
