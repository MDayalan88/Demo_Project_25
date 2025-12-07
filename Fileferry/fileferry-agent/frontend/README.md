# FileFerry Slack React Frontend

Modern React-based UI for FileFerry AI Agent with Slack integration, replacing the Microsoft Teams bot.

## 🎨 Features

### Dashboard
- **Real-time Stats**: View total transfers, success rates, active transfers, and failures
- **Recent Activity**: Monitor recent file transfers with status indicators
- **Quick Actions**: Fast access to common operations

### AI Chat Interface
- **Natural Language**: Chat with AWS Bedrock Claude 3.5 Sonnet AI
- **Smart Assistance**: Get help with S3 operations, transfers, and troubleshooting
- **Contextual Responses**: AI understands your transfer history and preferences

### S3 Bucket Explorer
- **Browse Buckets**: View all accessible S3 buckets
- **File Navigation**: Explore bucket contents with file metadata
- **Batch Selection**: Select multiple files for transfer operations
- **Visual Indicators**: File sizes, last modified dates, and status badges

### Transfer Management
- **Create Transfers**: Intuitive form for S3 to FTP/SFTP transfers
- **Transfer History**: View completed, in-progress, and failed transfers
- **ServiceNow Integration**: Automatic ticket creation for audit trails
- **Priority Levels**: Set transfer urgency (low, medium, high)

## 🚀 Technology Stack

### Frontend
- **React 18**: Modern React with hooks
- **Vite**: Lightning-fast build tool
- **TailwindCSS**: Utility-first CSS framework
- **React Query**: Server state management
- **React Router**: Client-side routing
- **Lucide Icons**: Beautiful icon library
- **Axios**: HTTP client

### Backend Integration
- **FastAPI**: High-performance Python backend
- **AWS Bedrock**: Claude 3.5 Sonnet AI model
- **Slack API**: (Optional) Slack notifications and commands

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- AWS credentials configured
- Bedrock model access enabled

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
VITE_API_URL=http://localhost:8000/api
EOF

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000` or `http://localhost:5173` (Vite default).

### Backend Setup

```bash
# Install Python dependencies
pip install fastapi uvicorn python-multipart

# Start backend API server
cd src/slack_bot
python slack_api.py
```

The API will be available at `http://localhost:8000`.

## 🛠️ Development

### Frontend Development

```bash
# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code
npm run format
```

### Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── Header.jsx          # Navigation header
│   │   ├── Dashboard.jsx       # Dashboard view
│   │   ├── ChatInterface.jsx   # AI chat UI
│   │   ├── BucketExplorer.jsx  # S3 browser
│   │   ├── TransferRequest.jsx # Transfer form
│   │   ├── TransferHistory.jsx # History view
│   │   ├── TransferCard.jsx    # Transfer item card
│   │   └── Toaster.jsx         # Toast notifications
│   ├── services/        # API services
│   │   └── api.js              # Backend API client
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── package.json         # Dependencies
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
└── postcss.config.js    # PostCSS configuration
```

## 🔌 API Endpoints

### Dashboard
- `GET /api/dashboard/stats` - Get transfer statistics
- `GET /api/dashboard/recent-transfers` - Get recent activity

### S3 Operations
- `POST /api/s3/list-buckets` - List S3 buckets
- `POST /api/s3/list-contents` - List bucket contents

### Transfers
- `POST /api/transfer/create` - Create transfer request
- `GET /api/transfer/history` - Get transfer history

### AI Chat
- `POST /api/chat/message` - Send message to AI agent

## 🎯 Usage Examples

### Chat with AI Agent
```
"List my S3 buckets in us-east-1"
"Transfer file.txt from my-bucket to ftp.example.com"
"Show me recent failed transfers"
"What files are in production-bucket?"
```

### Create Transfer Request
1. Navigate to "New Transfer" tab
2. Enter S3 bucket and file path
3. Select FTP or SFTP destination
4. Provide server credentials
5. Set priority level
6. Submit - ServiceNow tickets created automatically

### Browse S3 Buckets
1. Click "Load Buckets" in Explorer
2. Select a bucket to view contents
3. Check files to select for transfer
4. Click "Transfer to FTP/SFTP"

## 🎨 UI Components

### Color Scheme (Slack-inspired)
- **Primary Purple**: `#611f69` - Main actions
- **Green**: `#2BAC76` - Success states
- **Blue**: `#1264A3` - Information
- **Red**: `#E01E5A` - Errors/warnings
- **Yellow**: `#ECB22E` - In-progress states

### Status Badges
- ✅ **Success** - Green badge for completed transfers
- ⏳ **In Progress** - Yellow badge for active transfers
- ❌ **Failed** - Red badge for failed transfers
- ℹ️ **Info** - Blue badge for informational states

## 🔐 Security

### Frontend Security
- API keys stored in environment variables
- No sensitive data in localStorage
- CORS configured for trusted origins
- Input validation on all forms

### Backend Security
- AWS SSO authentication with 10-second auto-logout
- Read-only S3 access
- Encrypted credentials via AWS Secrets Manager
- ServiceNow dual-ticket audit trail

## 📊 Performance

### Optimizations
- React Query caching (5-minute stale time)
- Code splitting with React.lazy()
- Tailwind CSS purging for small bundles
- Vite's optimized dev server
- Image optimization and lazy loading

### Build Size
- Estimated production bundle: ~150KB (gzipped)
- Initial load time: <2 seconds
- Time to Interactive: <3 seconds

## 🐛 Troubleshooting

### Frontend Issues

**Port already in use:**
```bash
# Change port in vite.config.js or use:
npm run dev -- --port 3001
```

**CORS errors:**
- Ensure backend is running on http://localhost:8000
- Check CORS middleware in `slack_api.py`
- Update VITE_API_URL in `.env`

**Build failures:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Backend Issues

**Import errors:**
```bash
# Ensure you're in the correct directory
cd c:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent
python -m src.slack_bot.slack_api
```

**AWS credential errors:**
- Check `~/.aws/credentials` file
- Verify Bedrock model access
- Enable test_mode in config.yaml for local development

## 🚀 Deployment

### Frontend Deployment (AWS S3 + CloudFront)

```bash
# Build production bundle
npm run build

# Upload to S3
aws s3 sync dist/ s3://fileferry-frontend-bucket/

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### Backend Deployment (AWS Lambda)

The backend API integrates with existing Lambda deployment:
- API Gateway routes to Lambda function
- Lambda serves both API and static frontend
- Environment variables configured in Secrets Manager

See `DEPLOYMENT.md` for complete deployment guide.

## 📝 Configuration

### Frontend Environment Variables

Create `.env` file:
```env
# API endpoint
VITE_API_URL=http://localhost:8000/api

# Optional: Slack workspace ID for deep linking
VITE_SLACK_WORKSPACE_ID=T01234567

# Optional: Enable debug mode
VITE_DEBUG=true
```

### Backend Configuration

Update `config/config.yaml`:
```yaml
# Slack Bot Configuration
slack_bot:
  bot_token: ${SLACK_BOT_TOKEN}
  signing_secret: ${SLACK_SIGNING_SECRET}
  app_token: ${SLACK_APP_TOKEN}
  socket_mode: true

# Agent Settings
agent:
  test_mode: true  # Use default AWS credentials for local dev
```

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/new-component`
2. Make changes and test locally
3. Run linter: `npm run lint`
4. Format code: `npm run format`
5. Commit: `git commit -m "Add new component"`
6. Push and create PR

## 📄 License

MIT License - See LICENSE file for details

## 🔗 Links

- [React Documentation](https://react.dev/)
- [Vite Guide](https://vitejs.dev/)
- [TailwindCSS](https://tailwindcss.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [AWS Bedrock](https://aws.amazon.com/bedrock/)
- [Slack API](https://api.slack.com/)

## 💡 Tips

### Development Workflow
1. Start backend: `python src/slack_bot/slack_api.py`
2. Start frontend: `npm run dev` (in frontend/)
3. Open browser: `http://localhost:5173`
4. Make changes - hot reload enabled

### Testing AI Chat
Use these example queries:
- "List my S3 buckets"
- "What files are in fileferry bucket?"
- "Transfer data.csv from fileferry to ftp.example.com"
- "Show me recent transfer history"

### Customizing UI
- Modify Tailwind config for color schemes
- Update components in `src/components/`
- Add new routes in `App.jsx`
- Extend API client in `src/services/api.js`

---

**Built with ❤️ using React, FastAPI, and AWS Bedrock**
