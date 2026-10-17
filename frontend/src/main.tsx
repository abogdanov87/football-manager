import { ConfigProvider } from 'antd'
import ruRU from 'antd/locale/ru_RU'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import { fmTheme } from './theme/fmTheme'
import './index.css'
import './styles/fm-shell.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider locale={ruRU} theme={fmTheme}>
      <App />
    </ConfigProvider>
  </StrictMode>,
)
