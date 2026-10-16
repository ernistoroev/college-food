import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Listen on IPv4: by default Vite may bind only to ::1, and http://127.0.0.1:5173 hangs.
  server: {
    host: '127.0.0.1',
  },
})
