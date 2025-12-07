import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, TrendingUp, CheckCircle, AlertCircle, Clock, FileText } from 'lucide-react'
import { fetchDashboardStats, fetchRecentTransfers } from '../services/api'
import TransferCard from './TransferCard'

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
  })

  const { data: recentTransfers, isLoading: transfersLoading } = useQuery({
    queryKey: ['recent-transfers'],
    queryFn: fetchRecentTransfers,
  })

  if (statsLoading) {
    return <div className="text-center py-12">Loading dashboard...</div>
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 mb-1">Dashboard</h2>
          <p className="text-sm text-gray-600">Monitor your file transfer operations in real-time</p>
        </div>
        <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-xl shadow-sm border border-gray-200">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600 font-medium">
            {new Date().toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Transfers"
          value={stats?.total_transfers || 0}
          icon={Activity}
          color="blue"
          trend="+12% from last month"
        />
        <StatCard
          title="Success Rate"
          value={`${stats?.success_rate || 0}%`}
          icon={CheckCircle}
          color="green"
          trend="98.5% this month"
        />
        <StatCard
          title="Active Transfers"
          value={stats?.active_transfers || 0}
          icon={Clock}
          color="yellow"
          trend="2 in progress"
        />
        <StatCard
          title="Failed Transfers"
          value={stats?.failed_transfers || 0}
          icon={AlertCircle}
          color="red"
          trend="3 need attention"
        />
      </div>

      {/* Recent Activity */}
      <div className="card animate-slide-up">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-gray-900 flex items-center">
            <div className="w-10 h-10 fileferry-gradient rounded-lg flex items-center justify-center mr-3 shadow-lg">
              <FileText className="text-white" size={20} />
            </div>
            Recent Transfers
          </h3>
          <button className="text-sm font-semibold text-purple-600 hover:text-purple-700 transition-colors flex items-center space-x-1">
            <span>View All</span>
            <TrendingUp size={16} />
          </button>
        </div>

        {transfersLoading ? (
          <div className="text-center py-12">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-gray-500 font-medium">Loading transfers...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recentTransfers?.length > 0 ? (
              recentTransfers.map((transfer) => (
                <TransferCard key={transfer.id} transfer={transfer} />
              ))
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Clock size={48} className="mx-auto mb-4 opacity-50" />
                <p className="font-medium">No recent transfers</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <QuickAction
          title="Start New Transfer"
          description="Transfer files from S3 to FTP/SFTP"
          action="Start Transfer"
          to="/transfer"
        />
        <QuickAction
          title="Explore S3 Buckets"
          description="Browse your S3 buckets and files"
          action="Open Explorer"
          to="/explorer"
        />
        <QuickAction
          title="Ask AI Agent"
          description="Chat with AI for transfer assistance"
          action="Open Chat"
          to="/chat"
        />
      </div>
    </div>
  )
}

function StatCard({ title, value, icon: Icon, color, trend }) {
  const colorClasses = {
    blue: 'fileferry-gradient-soft border-blue-200',
    green: 'bg-gradient-to-br from-green-50 to-emerald-100 border-green-200',
    yellow: 'bg-gradient-to-br from-yellow-50 to-amber-100 border-yellow-200',
    red: 'bg-gradient-to-br from-red-50 to-rose-100 border-red-200',
  }

  const iconClasses = {
    blue: 'text-purple-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
  }

  return (
    <div className={`card border-2 ${colorClasses[color]} animate-slide-up`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-600 mb-2 font-medium">{title}</p>
          <p className="text-4xl font-bold text-gray-900 mb-2">{value}</p>
          <p className="text-xs text-gray-500 flex items-center">
            <TrendingUp className="w-3 h-3 mr-1" />
            {trend}
          </p>
        </div>
        <div className={`w-14 h-14 rounded-xl bg-white shadow-lg flex items-center justify-center ${iconClasses[color]}`}>
          <Icon size={28} strokeWidth={2.5} />
        </div>
      </div>
    </div>
  )
}

function QuickAction({ title, description, action, to }) {
  return (
    <a href={to}>
      <div className="card hover:shadow-2xl transition-all cursor-pointer group">
        <div className="flex items-start justify-between mb-3">
          <h4 className="font-bold text-gray-900 text-lg group-hover:text-purple-600 transition-colors">{title}</h4>
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
        </div>
        <p className="text-sm text-gray-600 mb-6 leading-relaxed">{description}</p>
        <button className="btn-primary w-full group-hover:shadow-xl">
          {action}
        </button>
      </div>
    </a>
  )
}
