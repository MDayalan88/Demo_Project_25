import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'

// New Pages
import LoginPage from './pages/LoginPage'
import MainDashboard from './pages/MainDashboard'
import FileTransferRequestPage from './pages/FileTransferRequestPage'
import AWSSSOPage from './pages/AWSSSOPage'

// Old Components (keeping for backward compatibility)
import { Toaster } from './components/Toaster'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import TransferRequest from './components/TransferRequest'
import TransferHistory from './components/TransferHistory'
import BucketExplorer from './components/BucketExplorer'
import ChatInterface from './components/ChatInterface'

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected App Routes - New UI Flow */}
        <Route path="/app" element={
          <ProtectedRoute>
            <Routes>
              <Route path="dashboard" element={<MainDashboard />} />
              <Route path="file-transfer" element={<FileTransferRequestPage />} />
              <Route path="aws-sso" element={<AWSSSOPage />} />
            </Routes>
          </ProtectedRoute>
        } />

        {/* Legacy Routes - Old UI with Header */}
        <Route path="/legacy/*" element={
          <div className="min-h-screen bg-gray-50">
            <Header />
            <main className="container mx-auto px-4 py-8">
              <Routes>
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="transfer" element={<TransferRequest />} />
                <Route path="history" element={<TransferHistory />} />
                <Route path="explorer" element={<BucketExplorer />} />
                <Route path="chat" element={<ChatInterface />} />
              </Routes>
            </main>
            <Toaster />
          </div>
        } />

        {/* Redirects */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  )
}

export default App
