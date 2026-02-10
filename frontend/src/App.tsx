import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Personnel from './pages/Personnel'
import PersonnelCategories from './pages/PersonnelCategories'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/personnel" replace />} />
          <Route path="/personnel" element={<Personnel />} />
          <Route path="/personnel-categories" element={<PersonnelCategories />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App

