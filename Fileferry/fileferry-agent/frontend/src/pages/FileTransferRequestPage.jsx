import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Database, Folder, FileText, AlertCircle, CheckCircle2 } from 'lucide-react'

export default function FileTransferRequestPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    assignmentGroup: '',
    environment: '',
    bucketName: '',
    fileName: '',
    priority: ''
  })
  const [errors, setErrors] = useState({})

  const assignmentGroups = [
    'DataOps Team',
    'DevOps Team',
    'Infrastructure Team',
    'Security Team'
  ]

  const environments = [
    { value: 'PROD', label: 'Production', color: 'text-red-600' },
    { value: 'QA', label: 'Quality Assurance', color: 'text-yellow-600' },
    { value: 'UAT', label: 'User Acceptance Testing', color: 'text-blue-600' }
  ]

  const priorities = [
    { value: 'High', label: 'High Priority', color: 'bg-red-500', textColor: 'text-red-700', bgLight: 'bg-red-50' },
    { value: 'Medium', label: 'Medium Priority', color: 'bg-orange-500', textColor: 'text-orange-700', bgLight: 'bg-orange-50' },
    { value: 'Low', label: 'Low Priority', color: 'bg-green-500', textColor: 'text-green-700', bgLight: 'bg-green-50' }
  ]

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.assignmentGroup) newErrors.assignmentGroup = 'Assignment group is required'
    if (!formData.environment) newErrors.environment = 'Environment is required'
    if (!formData.bucketName) newErrors.bucketName = 'Bucket name is required'
    if (!formData.fileName) newErrors.fileName = 'File name is required'
    if (!formData.priority) newErrors.priority = 'Priority is required'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    console.log('Form submitted with data:', formData)
    
    if (validateForm()) {
      // Store form data in localStorage for the next page
      localStorage.setItem('transferRequest', JSON.stringify(formData))
      console.log('Navigating to AWS SSO page...')
      // Navigate to AWS SSO authentication page
      navigate('/app/aws-sso')
    } else {
      console.log('Form validation failed:', errors)
    }
  }

  const isFormValid = () => {
    return formData.assignmentGroup && 
           formData.environment && 
           formData.bucketName && 
           formData.fileName && 
           formData.priority
  }

  const getPriorityConfig = (priority) => {
    return priorities.find(p => p.value === priority) || priorities[1]
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Breadcrumb Navigation */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center space-x-2 text-sm">
            <button
              onClick={() => navigate('/app/dashboard')}
              className="text-gray-500 hover:text-purple-600 transition-colors flex items-center"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Dashboard
            </button>
            <ChevronRight className="w-4 h-4 text-gray-400" />
            <span className="text-gray-900 font-semibold">File Transfer Request</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Page Header */}
          <div className="mb-8 animate-fade-in">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">File Transfer Request</h1>
                <p className="text-gray-600">Complete the form to initiate a file transfer</p>
              </div>
            </div>
          </div>

          {/* Form Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 animate-slide-up">
            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Assignment Group */}
              <div>
                <label htmlFor="assignmentGroup" className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                  <Database className="w-5 h-5 mr-2 text-purple-600" />
                  Assignment Group
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <select
                  id="assignmentGroup"
                  name="assignmentGroup"
                  value={formData.assignmentGroup}
                  onChange={handleChange}
                  className={`block w-full px-4 py-3 border-2 ${errors.assignmentGroup ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all text-gray-900`}
                >
                  <option value="">Select an assignment group</option>
                  {assignmentGroups.map(group => (
                    <option key={group} value={group}>{group}</option>
                  ))}
                </select>
                {errors.assignmentGroup && (
                  <p className="mt-2 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.assignmentGroup}
                  </p>
                )}
              </div>

              {/* Environment */}
              <div>
                <label className="block text-sm font-bold text-gray-900 mb-3">
                  Environment
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {environments.map(env => (
                    <label
                      key={env.value}
                      className={`relative flex items-center justify-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                        formData.environment === env.value
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <input
                        type="radio"
                        name="environment"
                        value={env.value}
                        checked={formData.environment === env.value}
                        onChange={handleChange}
                        className="sr-only"
                      />
                      <div className="text-center">
                        <div className={`text-lg font-bold ${formData.environment === env.value ? 'text-purple-600' : env.color}`}>
                          {env.value}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">{env.label}</div>
                      </div>
                      {formData.environment === env.value && (
                        <CheckCircle2 className="absolute top-3 right-3 w-5 h-5 text-purple-600" />
                      )}
                    </label>
                  ))}
                </div>
                {errors.environment && (
                  <p className="mt-2 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.environment}
                  </p>
                )}
              </div>

              {/* Bucket Name */}
              <div>
                <label htmlFor="bucketName" className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                  <Folder className="w-5 h-5 mr-2 text-purple-600" />
                  Bucket Name
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <input
                  id="bucketName"
                  name="bucketName"
                  type="text"
                  value={formData.bucketName}
                  onChange={handleChange}
                  placeholder="e.g., my-s3-bucket"
                  className={`block w-full px-4 py-3 border-2 ${errors.bucketName ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all text-gray-900 placeholder-gray-400`}
                />
                {errors.bucketName && (
                  <p className="mt-2 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.bucketName}
                  </p>
                )}
              </div>

              {/* File Name */}
              <div>
                <label htmlFor="fileName" className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-purple-600" />
                  File Name
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <input
                  id="fileName"
                  name="fileName"
                  type="text"
                  value={formData.fileName}
                  onChange={handleChange}
                  placeholder="e.g., data-export.csv"
                  className={`block w-full px-4 py-3 border-2 ${errors.fileName ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all text-gray-900 placeholder-gray-400`}
                />
                {errors.fileName && (
                  <p className="mt-2 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.fileName}
                  </p>
                )}
              </div>

              {/* Priority */}
              <div>
                <label htmlFor="priority" className="block text-sm font-bold text-gray-900 mb-3">
                  Priority Level
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <select
                  id="priority"
                  name="priority"
                  value={formData.priority}
                  onChange={handleChange}
                  className={`block w-full px-4 py-3 border-2 ${errors.priority ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all text-gray-900`}
                >
                  <option value="">Select priority level</option>
                  {priorities.map(priority => (
                    <option key={priority.value} value={priority.value}>
                      {priority.label}
                    </option>
                  ))}
                </select>
                {formData.priority && (
                  <div className={`mt-3 p-3 rounded-lg ${getPriorityConfig(formData.priority).bgLight} border-l-4 ${getPriorityConfig(formData.priority).color}`}>
                    <p className={`text-sm font-semibold ${getPriorityConfig(formData.priority).textColor}`}>
                      {formData.priority === 'High' && '⚠️ High priority requests are processed immediately'}
                      {formData.priority === 'Medium' && '📋 Medium priority requests are processed within 2 hours'}
                      {formData.priority === 'Low' && '✓ Low priority requests are processed within 24 hours'}
                    </p>
                  </div>
                )}
                {errors.priority && (
                  <p className="mt-2 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.priority}
                  </p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => navigate('/app/dashboard')}
                  className="px-6 py-3 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!isFormValid()}
                  onClick={(e) => {
                    if (!isFormValid()) {
                      e.preventDefault()
                      console.log('Button clicked but form is not valid')
                      validateForm()
                    }
                  }}
                  className={`px-8 py-3 font-semibold rounded-xl transition-all shadow-lg ${
                    isFormValid()
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:from-purple-700 hover:to-indigo-700 hover:shadow-xl'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  Continue to AWS SSO
                </button>
              </div>
            </form>
          </div>

          {/* Info Box */}
          <div className="mt-6 bg-blue-50 border-l-4 border-blue-500 p-4 rounded-lg">
            <p className="text-sm text-blue-700">
              <strong>Note:</strong> All fields marked with <span className="text-red-500">*</span> are mandatory. You'll be redirected to AWS SSO authentication after submitting this form.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
