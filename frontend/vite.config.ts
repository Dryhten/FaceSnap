import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 从项目根目录加载环境变量（与后端共用 .env 文件）
  const rootDir = path.resolve(__dirname, '..')
  const env = loadEnv(mode, rootDir, '')
  
  // 从环境变量读取后端端口和主机（与后端配置一致）
  const backendPort = env.API_PORT || '8000'
  // API_HOST 可能是 0.0.0.0，前端代理需要使用 localhost
  const backendHost = (env.API_HOST === '0.0.0.0' || env.API_HOST === '127.0.0.1') 
    ? 'localhost' 
    : (env.API_HOST || 'localhost')
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0',  // 允许外部访问
      port: 3000,
      proxy: {
        '/api': {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  }
})

