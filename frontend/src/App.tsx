import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Personnel from './pages/Personnel'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/personnel" replace />} />
          <Route path="/personnel" element={<Personnel />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App

