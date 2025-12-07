import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, GitBranch, Calendar, FileText, User, AlertCircle } from 'lucide-react'

export default function ChangeRequestPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    requestTitle: '',
    requestType: '',
    priority: '',
    targetDate: '',
    assignedTo: '',
    description: ''
  })
  const [errors, setErrors] = useState({})

  const requestTypes = [
    'Standard Change',
    'Emergency Change',
    'Normal Change'
  ]

  const priorities = [
    { value: 'Critical', label: 'Critical', color: 'bg-red-500' },
    { value: 'High', label: 'High', color: 'bg-orange-500' },
    { value: 'Medium', label: 'Medium', color: 'bg-yellow-500' },
    { value: 'Low', label: 'Low', color: 'bg-green-500' }
  ]

  const teams = [
    'Infrastructure Team',
    'Application Team',
    'Database Team',
    'Security Team',
    'Network Team'
  ]

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.requestTitle) newErrors.requestTitle = 'Request title is required'
    if (!formData.requestType) newErrors.requestType = 'Request type is required'
    if (!formData.priority) newErrors.priority = 'Priority is required'
    if (!formData.targetDate) newErrors.targetDate = 'Target date is required'
    if (!formData.assignedTo) newErrors.assignedTo = 'Assignment is required'
    if (!formData.description) newErrors.description = 'Description is required'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    console.log('Change request form submitted with data:', formData)
    
    if (validateForm()) {
      // Store form data
      localStorage.setItem('changeRequest', JSON.stringify(formData))
      console.log('Navigating to dashboard...')
      // Navigate to success page or dashboard
      navigate('/app/dashboard')
    } else {
      console.log('Form validation failed:', errors)
    }
  }

  const isFormValid = () => {
    return formData.requestTitle && 
           formData.requestType && 
           formData.priority && 
           formData.targetDate && 
           formData.assignedTo && 
           formData.description
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Breadcrumb Navigation */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center space-x-2 text-sm">
            <button
              onClick={() => navigate('/app/dashboard')}
              className="text-gray-500 hover:text-blue-600 transition-colors flex items-center"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Dashboard
            </button>
            <ChevronRight className="w-4 h-4 text-gray-400" />
            <span className="text-gray-900 font-semibold">Change Request</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        <div className="max-w-4xl mx-auto">
          {/* Page Header */}
          <div className="mb-8 animate-fade-in">
            <div className="flex items-center space-x-3 mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg">
                <GitBranch className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Submit Change Request</h1>
                <p className="text-gray-600">Fill out the form to submit a new change request</p>
              </div>
            </div>
          </div>

          {/* Form Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 animate-slide-up">
            <form onSubmit={handleSubmit} className="space-y-8">
              {/* Request Title */}
              <div>
                <label htmlFor="requestTitle" className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                  <FileText className="w-5 h-5 mr-2 text-blue-600" />
                  Request Title
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <input
                  id="requestTitle"
                  name="requestTitle"
                  type="text"
                  value={formData.requestTitle}
                  onChange={handleChange}
                  placeholder="Brief description of the change"
                  className={`block w-full px-4 py-3 border-2 ${errors.requestTitle ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900 placeholder-gray-400`}
                />
                {errors.requestTitle && (
                  <p className="mt-2 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.requestTitle}
                  </p>
                )}
              </div>

              {/* Request Type & Priority */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Request Type */}
                <div>
                  <label htmlFor="requestType" className="block text-sm font-bold text-gray-900 mb-3">
                    Request Type
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <select
                    id="requestType"
                    name="requestType"
                    value={formData.requestType}
                    onChange={handleChange}
                    className={`block w-full px-4 py-3 border-2 ${errors.requestType ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900`}
                  >
                    <option value="">Select type</option>
                    {requestTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                  {errors.requestType && (
                    <p className="mt-2 text-sm text-red-600 flex items-center">
                      <AlertCircle className="w-4 h-4 mr-1" />
                      {errors.requestType}
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
                    className={`block w-full px-4 py-3 border-2 ${errors.priority ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900`}
                  >
                    <option value="">Select priority</option>
                    {priorities.map(priority => (
                      <option key={priority.value} value={priority.value}>
                        {priority.label}
                      </option>
                    ))}
                  </select>
                  {errors.priority && (
                    <p className="mt-2 text-sm text-red-600 flex items-center">
                      <AlertCircle className="w-4 h-4 mr-1" />
                      {errors.priority}
                    </p>
                  )}
                </div>
              </div>

              {/* Target Date & Assigned To */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Target Date */}
                <div>
                  <label htmlFor="targetDate" className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                    <Calendar className="w-5 h-5 mr-2 text-blue-600" />
                    Target Date
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <input
                    id="targetDate"
                    name="targetDate"
                    type="date"
                    value={formData.targetDate}
                    onChange={handleChange}
                    min={new Date().toISOString().split('T')[0]}
                    className={`block w-full px-4 py-3 border-2 ${errors.targetDate ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900`}
                  />
                  {errors.targetDate && (
                    <p className="mt-2 text-sm text-red-600 flex items-center">
                      <AlertCircle className="w-4 h-4 mr-1" />
                      {errors.targetDate}
                    </p>
                  )}
                </div>

                {/* Assigned To */}
                <div>
                  <label htmlFor="assignedTo" className="block text-sm font-bold text-gray-900 mb-3 flex items-center">
                    <User className="w-5 h-5 mr-2 text-blue-600" />
                    Assign To
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <select
                    id="assignedTo"
                    name="assignedTo"
                    value={formData.assignedTo}
                    onChange={handleChange}
                    className={`block w-full px-4 py-3 border-2 ${errors.assignedTo ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900`}
                  >
                    <option value="">Select team</option>
                    {teams.map(team => (
                      <option key={team} value={team}>{team}</option>
                    ))}
                  </select>
                  {errors.assignedTo && (
                    <p className="mt-2 text-sm text-red-600 flex items-center">
                      <AlertCircle className="w-4 h-4 mr-1" />
                      {errors.assignedTo}
                    </p>
                  )}
                </div>
              </div>

              {/* Description */}
              <div>
                <label htmlFor="description" className="block text-sm font-bold text-gray-900 mb-3">
                  Change Description
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows="6"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Provide detailed description of the change, including impact analysis and rollback plan..."
                  className={`block w-full px-4 py-3 border-2 ${errors.description ? 'border-red-300' : 'border-gray-200'} rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-gray-900 placeholder-gray-400 resize-none`}
                />
                {errors.description && (
                  <p className="mt-2 text-sm text-red-600 flex items-center">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {errors.description}
                  </p>
                )}
                <p className="mt-2 text-sm text-gray-500">
                  {formData.description.length} / 500 characters
                </p>
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
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white hover:from-blue-700 hover:to-cyan-700 hover:shadow-xl'
                      : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  Submit Request
                </button>
              </div>
            </form>
          </div>

          {/* Info Box */}
          <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg">
            <p className="text-sm text-yellow-700">
              <strong>Important:</strong> All change requests will go through an approval workflow. You will receive email notifications at each stage of the process.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
