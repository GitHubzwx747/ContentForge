import { HashRouter, Routes, Route } from 'react-router-dom'
import { GenerateProvider } from './context/GenerateContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Generate from './pages/Generate'
import History from './pages/History'
import Models from './pages/Models'

export default function App() {
  return (
    <GenerateProvider>
      <HashRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/generate" element={<Generate />} />
            <Route path="/history" element={<History />} />
            <Route path="/models" element={<Models />} />
          </Routes>
        </Layout>
      </HashRouter>
    </GenerateProvider>
  )
}
