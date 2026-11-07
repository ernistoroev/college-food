import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'

import App from './App.jsx'
import AdminLoginPage from './pages/admin/ui/AdminLoginPage.jsx'
import AdminLayout from './pages/admin/ui/AdminLayout.jsx'
import AdminDashboardPage from './pages/admin/ui/AdminDashboardPage.jsx'
import AdminOrdersPage from './pages/admin/ui/AdminOrdersPage.jsx'
import AdminDishesPage from './pages/admin/ui/AdminDishesPage.jsx'

function AdminPlaceholder({ title, description }) {
  return (
    <div>
      <h1 style={{ margin: '0 0 10px', fontSize: 28 }}>{title}</h1>
      <p style={{ color: '#7b8493' }}>{description}</p>
    </div>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />

        <Route
          path="/admin/login"
          element={<AdminLoginPage />}
        />

        <Route path="/admin" element={<AdminLayout />}>
          <Route
            index
            element={<Navigate to="dashboard" replace />}
          />

          <Route
            path="dashboard"
            element={
              <AdminDashboardPage />
            }
          />

          <Route path="orders" element={<AdminOrdersPage />} />

          <Route path="dishes" element={<AdminDishesPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
