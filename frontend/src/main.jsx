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

// The staff panel lives under /staff: on the hosting /admin/ is the Django admin.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />

        <Route
          path="/staff/login"
          element={<AdminLoginPage />}
        />

        <Route path="/staff" element={<AdminLayout />}>
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
