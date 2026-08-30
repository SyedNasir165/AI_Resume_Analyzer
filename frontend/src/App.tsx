import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import DashboardPage from './pages/DashboardPage'
import UploadResumePage from './pages/UploadResumePage'
import AnalysisResultsPage from './pages/AnalysisResultsPage'
import JobAnalysisPage from './pages/JobAnalysisPage'
import ExportPage from './pages/ExportPage'

function App() {
  return (
    <AuthProvider>
      <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/resumes/new"
              element={
                <ProtectedRoute>
                  <UploadResumePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/resumes/:resumeId/analyze-job"
              element={
                <ProtectedRoute>
                  <JobAnalysisPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/resumes/:resumeId/export"
              element={
                <ProtectedRoute>
                  <ExportPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analyses/:analysisId"
              element={
                <ProtectedRoute>
                  <AnalysisResultsPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>
        <Footer />
      </div>
    </AuthProvider>
  )
}

export default App
