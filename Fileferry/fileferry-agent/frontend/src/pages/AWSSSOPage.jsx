import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, CheckCircle2, ArrowRight, Lock, Key } from 'lucide-react'

export default function AWSSSOPage() {
  const navigate = useNavigate()
  const [transferRequest, setTransferRequest] = useState(null)
  const [isAuthenticating, setIsAuthenticating] = useState(false)
  const [authStep, setAuthStep] = useState('initial') // initial, authenticating, success

  useEffect(() => {
    // Load the transfer request data
    const requestData = localStorage.getItem('transferRequest')
    if (requestData) {
      setTransferRequest(JSON.parse(requestData))
    } else {
      // If no data, redirect back
      navigate('/app/file-transfer')
    }
  }, [navigate])

  const handleAuthenticate = () => {
    setIsAuthenticating(true)
    setAuthStep('authenticating')

    // Simulate AWS SSO authentication process
    setTimeout(() => {
      setAuthStep('success')
      setIsAuthenticating(false)
      
      // Redirect to dashboard after successful authentication
      setTimeout(() => {
        navigate('/app/dashboard')
        // Show success notification (you can implement toast notification here)
      }, 2000)
    }, 3000)
  }

  return (
    <div className="min-h-screen fileferry-gradient flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-2xl">
        {authStep === 'initial' && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 animate-slide-up">
            {/* Header */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl mb-4 shadow-lg">
                <Shield className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">AWS SSO Authentication</h1>
              <p className="text-gray-600">Secure authentication required to proceed</p>
            </div>

            {/* Request Summary */}
            {transferRequest && (
              <div className="bg-gray-50 rounded-xl p-6 mb-8 border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-4 flex items-center">
                  <Lock className="w-5 h-5 mr-2 text-purple-600" />
                  Transfer Request Summary
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Assignment Group:</span>
                    <span className="font-semibold text-gray-900">{transferRequest.assignmentGroup}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Environment:</span>
                    <span className="font-semibold text-gray-900">{transferRequest.environment}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Bucket Name:</span>
                    <span className="font-semibold text-gray-900">{transferRequest.bucketName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">File Name:</span>
                    <span className="font-semibold text-gray-900">{transferRequest.fileName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Priority:</span>
                    <span className={`font-semibold ${
                      transferRequest.priority === 'High' ? 'text-red-600' :
                      transferRequest.priority === 'Medium' ? 'text-orange-600' : 'text-green-600'
                    }`}>
                      {transferRequest.priority}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Authentication Info */}
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg mb-6">
              <h4 className="font-semibold text-blue-900 mb-2 flex items-center">
                <Key className="w-5 h-5 mr-2" />
                Authentication Required
              </h4>
              <p className="text-sm text-blue-700">
                To access AWS resources and initiate the file transfer, you must authenticate through AWS Single Sign-On (SSO). This ensures secure access to your cloud resources.
              </p>
            </div>

            {/* Security Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-gray-900 text-sm">Multi-Factor Authentication</h4>
                  <p className="text-xs text-gray-600 mt-1">Enhanced security with MFA</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-gray-900 text-sm">Encrypted Connection</h4>
                  <p className="text-xs text-gray-600 mt-1">TLS 1.3 secure protocol</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-gray-900 text-sm">Session Management</h4>
                  <p className="text-xs text-gray-600 mt-1">Automatic session timeout</p>
                </div>
              </div>
              <div className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-gray-900 text-sm">Audit Logging</h4>
                  <p className="text-xs text-gray-600 mt-1">All actions are logged</p>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-6 border-t border-gray-200">
              <button
                onClick={() => navigate('/app/file-transfer')}
                className="px-6 py-3 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 transition-all"
              >
                Go Back
              </button>
              <button
                onClick={handleAuthenticate}
                className="px-8 py-3 bg-gradient-to-r from-orange-500 to-red-600 text-white font-semibold rounded-xl hover:from-orange-600 hover:to-red-700 transition-all shadow-lg hover:shadow-xl flex items-center space-x-2"
              >
                <span>Authenticate with AWS SSO</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {authStep === 'authenticating' && (
          <div className="bg-white rounded-2xl shadow-2xl p-12 animate-fade-in text-center">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-orange-500 to-red-600 rounded-full mb-6 shadow-lg">
              <Shield className="w-12 h-12 text-white animate-pulse" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">Authenticating...</h2>
            <p className="text-gray-600 mb-8">Please wait while we verify your AWS credentials</p>
            
            {/* Loading Steps */}
            <div className="space-y-4 text-left max-w-md mx-auto">
              <div className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm text-gray-700">Connecting to AWS SSO</span>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg">
                <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm text-gray-700">Verifying credentials</span>
              </div>
              <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg opacity-50">
                <div className="w-5 h-5 border-2 border-gray-400 rounded-full"></div>
                <span className="text-sm text-gray-500">Obtaining access token</span>
              </div>
            </div>
          </div>
        )}

        {authStep === 'success' && (
          <div className="bg-white rounded-2xl shadow-2xl p-12 animate-slide-up text-center">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-green-100 rounded-full mb-6">
              <CheckCircle2 className="w-16 h-16 text-green-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Authentication Successful!</h2>
            <p className="text-gray-600 mb-6">Your file transfer request has been submitted</p>
            
            <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded-lg max-w-md mx-auto">
              <p className="text-sm text-green-700">
                <strong>Request ID:</strong> FT-{Date.now().toString().slice(-8)}
              </p>
              <p className="text-sm text-green-700 mt-2">
                You will receive a notification once the transfer is complete.
              </p>
            </div>

            <p className="text-sm text-gray-500 mt-6">
              Redirecting to dashboard...
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
