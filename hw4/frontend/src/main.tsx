import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './context/AuthContext'
import { ChatResultsProvider } from './context/ChatResultsContext'
import { BagProvider } from './context/BagContext'
import { VisitorProvider } from './context/VisitorContext'
import './eras.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <BagProvider>
          <VisitorProvider>
            <ChatResultsProvider>
              <App />
            </ChatResultsProvider>
          </VisitorProvider>
        </BagProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
