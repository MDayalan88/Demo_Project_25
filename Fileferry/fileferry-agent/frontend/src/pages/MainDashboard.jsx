import { useNavigate } from 'react-router-dom'
import { FileText, GitBranch, ArrowRight, Zap } from 'lucide-react'

export default function MainDashboard() {
  const navigate = useNavigate()
  const username = localStorage.getItem('username') || 'User'

  const dashboardCards = [
    {
      id: 'fileferry',
      title: 'FileFerry',
      description: 'Initiate file transfer requests across environments',
      icon: FileText,
      color: 'from-purple-600 to-indigo-600',
      path: '/app/file-transfer',
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600'
    }
  ]

  const handleCardClick = (path) => {
    navigate(path)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                <Zap className="w-6 h-6 text-yellow-300" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">FileFerry</h1>
                <p className="text-xs text-gray-500">Operations Dashboard</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-900">{username}</p>
                <p className="text-xs text-gray-500">Admin</p>
              </div>
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                {username.charAt(0).toUpperCase()}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-12">
        {/* Welcome Section */}
        <div className="mb-12 animate-fade-in">
          <h2 className="text-4xl font-bold text-gray-900 mb-3">
            Welcome back, {username}!
          </h2>
          <p className="text-lg text-gray-600">
            Select an operation to get started with your workflow
          </p>
        </div>

        {/* Dashboard Cards Grid */}
        <div className="grid grid-cols-1 gap-8 max-w-2xl">
          {dashboardCards.map((card, index) => (
            <div
              key={card.id}
              onClick={() => handleCardClick(card.path)}
              className="group cursor-pointer animate-slide-up"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 p-8 border-2 border-gray-100 hover:border-purple-200 transform hover:-translate-y-2">
                {/* Icon */}
                <div className={`inline-flex items-center justify-center w-16 h-16 ${card.iconBg} rounded-2xl mb-6 group-hover:scale-110 transition-transform duration-300 shadow-md`}>
                  <card.icon className={`w-8 h-8 ${card.iconColor}`} strokeWidth={2.5} />
                </div>

                {/* Content */}
                <div className="mb-6">
                  <h3 className="text-2xl font-bold text-gray-900 mb-3 group-hover:text-purple-600 transition-colors">
                    {card.title}
                  </h3>
                  <p className="text-gray-600 leading-relaxed">
                    {card.description}
                  </p>
                </div>

                {/* Action Button */}
                <div className="flex items-center text-purple-600 font-semibold group-hover:text-purple-700 transition-colors">
                  <span>Get Started</span>
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-2 transition-transform duration-300" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Stats Section */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-gray-600">Active Transfers</h4>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
            <p className="text-3xl font-bold text-gray-900">12</p>
            <p className="text-xs text-gray-500 mt-1">Last 24 hours</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-gray-600">Success Rate</h4>
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            </div>
            <p className="text-3xl font-bold text-gray-900">98.5%</p>
            <p className="text-xs text-gray-500 mt-1">This month</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-gray-600">Pending Requests</h4>
              <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
            </div>
            <p className="text-3xl font-bold text-gray-900">3</p>
            <p className="text-xs text-gray-500 mt-1">Awaiting approval</p>
          </div>
        </div>
      </main>
    </div>
  )
}
