# FileFerry Frontend & ServiceNow Integration Guide

## 🎨 Frontend Customization Complete

The FileFerry frontend has been enhanced with:

### ✨ Visual Enhancements

1. **FileFerry Gradient Branding**
   - Purple to indigo gradient (`#667eea` → `#764ba2`)
   - Soft gradient backgrounds for cards
   - Glassmorphism effects with backdrop blur

2. **Custom Animations**
   - `fadeIn` - Smooth fade-in effect (0.6s)
   - `slideUp` - Slide-up entrance animation (0.7s)
   - `shimmer` - Progress bar animation (2s)
   - `pulse-glow` - Glowing pulse effect for highlights
   - `spin` - Loading spinner rotation

3. **Enhanced Components**
   - **Header**: Gradient background with live connection indicator
   - **Dashboard**: Animated stat cards with gradients
   - **TransferCard**: File type icons, progress bars, ServiceNow ticket display
   - **Buttons**: Gradient backgrounds with hover effects
   - **Badges**: Color-coded status indicators with gradients

4. **File Type Icons**
   - CSV/Excel: Green spreadsheet icon
   - ZIP/Archives: Orange archive icon
   - Default: Blue document icon

5. **Status Indicators**
   - Success: Green with glow
   - Error: Red with glow
   - Pending: Yellow with pulse animation

### 🎯 Key CSS Classes Added

```css
/* Gradients */
.fileferry-gradient - Main purple-indigo gradient
.fileferry-gradient-soft - Soft transparent gradient

/* Animations */
.animate-fade-in - Fade in entrance
.animate-slide-up - Slide up entrance
.animate-pulse-glow - Glowing pulse effect

/* ServiceNow */
.servicenow-ticket - Ticket number display with link
.servicenow-badge - Compact ticket badge

/* Progress */
.transfer-progress - Progress bar container
.transfer-progress-bar - Animated progress indicator

/* Status */
.status-indicator - Colored dot indicator
.status-success/.status-error/.status-pending - Status variants
```

---

## 🎫 ServiceNow Integration

### Overview

FileFerry automatically creates ServiceNow incident tickets for every file transfer request. This provides:
- **Audit Trail**: Every transfer is logged in ServiceNow
- **Issue Tracking**: Failed transfers create tickets for resolution
- **Accountability**: Tickets track who initiated transfers and when
- **Compliance**: Meet organizational tracking requirements

### How It Works

1. **User Initiates Transfer** (via Frontend)
   ```
   User fills out transfer form → Submits to backend API
   ```

2. **Backend Creates Ticket** (Automatic)
   ```python
   # In slack_api_simple.py
   async def create_servicenow_ticket(transfer_data):
       ticket = {
           "short_description": f"File Transfer: {file_name}",
           "description": f"Transfer from {source} to {destination}",
           "assignment_group": "DataOps"
       }
       # POST to ServiceNow API
   ```

3. **Response Includes Ticket** (Sent to Frontend)
   ```json
   {
     "transfer_id": "12345",
     "status": "initiated",
     "servicenow_ticket": "INC0010123"
   }
   ```

4. **Frontend Displays Ticket** (In TransferCard)
   ```jsx
   {transfer.servicenow_ticket && (
     <a href={ticketUrl} className="servicenow-ticket">
       <ExternalLink /> {transfer.servicenow_ticket}
     </a>
   )}
   ```

### ServiceNow Ticket Information

Each ticket contains:
- **Short Description**: `File Transfer: filename.csv`
- **Description**: Detailed transfer information
  - Source location (S3 bucket/FTP)
  - Destination location (SFTP/S3)
  - File size and type
  - Requested by (user)
  - Timestamp
- **Assignment Group**: `DataOps` (configurable)
- **Priority**: 3 (Medium) - configurable
- **Category**: Data Operations
- **State**: New (auto-updates on transfer completion)

### Configuration Required

#### Step 1: Get ServiceNow Instance

1. Visit https://developer.servicenow.com/
2. Create free account
3. Request **Personal Developer Instance** (PDI)
4. Wait 2-5 minutes for provisioning
5. Note your instance URL: `https://devXXXXXX.service-now.com`
   - Replace XXXXXX with your actual instance number
   - **Important**: NOT `devxxxxx` - that's a placeholder!

#### Step 2: Configure Instance

1. Log into your ServiceNow instance
2. Navigate to: **User Administration → Groups**
3. Create new group: `DataOps`
4. Add yourself to the group
5. Note the group name (must match backend config)

#### Step 3: Set Environment Variables

**Option A: Using PowerShell Script (Recommended)**
```powershell
.\setup-servicenow.ps1
```
- Script will prompt for your credentials
- Automatically validates connection
- Saves to `.env` file

**Option B: Manual Setup**
```powershell
# Set environment variables
$env:SERVICENOW_INSTANCE_URL = "https://dev123456.service-now.com"
$env:SERVICENOW_USERNAME = "admin"
$env:SERVICENOW_PASSWORD = "your-password"

# Restart backend for changes to take effect
```

**Option C: Edit .env File**
```bash
# Create/edit .env file in project root
SERVICENOW_INSTANCE_URL=https://dev123456.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=your-password-here
```

#### Step 4: Verify Integration

```powershell
# Run test script
python test_servicenow_integration.py

# Expected output:
✅ Connection test passed
✅ Assignment group exists
✅ Create ticket passed (INC0010001)
✅ Update ticket passed
✅ Close ticket passed
```

### Frontend Configuration

Update the ServiceNow ticket link in `TransferCard.jsx`:

```jsx
// Line 52 - Replace with your actual instance URL
<a 
  href={`https://YOUR-INSTANCE.service-now.com/nav_to.do?uri=incident.do?sysparm_query=number=${transfer.servicenow_ticket}`}
  target="_blank"
  rel="noopener noreferrer"
  className="servicenow-ticket"
>
```

Example:
```jsx
href={`https://dev123456.service-now.com/nav_to.do?uri=incident.do?sysparm_query=number=${transfer.servicenow_ticket}`}
```

---

## 🚀 Running the Application

### Prerequisites

1. **Node.js** (Required for frontend)
   - Download: https://nodejs.org/en/download/
   - Install LTS version
   - Restart PowerShell after installation

2. **Python Environment** (Already configured)
   - Python 3.8+
   - All dependencies installed via `requirements.txt`

3. **ServiceNow Instance** (Optional but recommended)
   - Follow configuration steps above
   - Backend works without it (tickets disabled)

### Start Backend API

```powershell
# Navigate to project directory
cd C:\Martin-Files\Training\Demo\End-End\Fileferry\fileferry-agent

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python .\src\slack_bot\slack_api_simple.py"

# Backend runs on: http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### Start Frontend (After Node.js Installation)

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Frontend runs on: http://localhost:5173
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend UI** | http://localhost:5173 | React web interface |
| **Backend API** | http://localhost:8000 | FastAPI REST endpoints |
| **Swagger Docs** | http://localhost:8000/docs | Interactive API documentation |
| **ServiceNow** | https://yourinstance.service-now.com | Ticket management (external) |

---

## 🎨 UI Features

### Dashboard View
- **Animated stat cards** showing:
  - Total Transfers
  - Success Rate
  - Active Transfers
  - Failed Transfers
- **Recent Transfers** list with:
  - File type icons
  - Status indicators
  - ServiceNow ticket links
  - Progress bars (for active transfers)

### Transfer Card Features
- **File Type Icons**: Visual identification of CSV, PDF, ZIP files
- **ServiceNow Badge**: Clickable ticket number
- **Status Indicators**: Color-coded dots (green/yellow/red)
- **Progress Bar**: Real-time transfer progress with shimmer animation
- **Hover Effects**: Card lifts and glows on hover

### Header Features
- **FileFerry Branding**: Gradient background with lightning bolt icon
- **Live Connection**: Shows green "Live" badge when backend is connected
- **Navigation**: 5 main sections (Dashboard, Transfer, History, Explorer, Chat)
- **Glassmorphism**: Frosted glass effect on navigation items

---

## 📊 ServiceNow Ticket Lifecycle

```
1. Transfer Initiated
   └─> Create ServiceNow Ticket (State: New)
       └─> Display ticket number in UI

2. Transfer In Progress
   └─> Update ticket with progress (State: In Progress)
       └─> Show progress bar in UI

3. Transfer Completed
   └─> Update ticket (State: Resolved)
       └─> Show success badge in UI

4. Transfer Failed
   └─> Update ticket (State: Awaiting Attention)
       └─> Show error badge + ticket link in UI
```

---

## 🔧 Troubleshooting

### ServiceNow Not Working

**Issue**: "ServiceNow integration DISABLED"

**Solution**:
1. Check environment variables are set
2. Verify instance URL is correct (not `devxxxxx`)
3. Ensure instance is not hibernated
   - Visit https://developer.servicenow.com/
   - Click "Manage" → "Instance"
   - Click "Wake Up" if hibernated
4. Run `python test_servicenow_integration.py` for diagnostics

**Issue**: "Assignment group not found"

**Solution**:
1. Log into ServiceNow
2. Navigate to: User Administration → Groups
3. Create group: `DataOps`
4. Or update `SERVICENOW_ASSIGNMENT_GROUP` in backend config

### Frontend Not Starting

**Issue**: `npm: The term 'npm' is not recognized`

**Solution**:
1. Install Node.js from https://nodejs.org/
2. Restart PowerShell
3. Verify: `node --version` and `npm --version`

**Issue**: Port 5173 already in use

**Solution**:
```powershell
# Find and stop process using port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Or use different port
npm run dev -- --port 3000
```

### Backend Connection Issues

**Issue**: Frontend shows "Offline" badge

**Solution**:
1. Ensure backend is running: http://localhost:8000/docs
2. Check firewall is not blocking port 8000
3. Verify CORS settings in `slack_api_simple.py`

---

## 📚 Additional Resources

- **ServiceNow Setup**: See `SERVICENOW_SETUP.md`
- **ServiceNow Quickstart**: See `SERVICENOW_QUICKSTART.md`
- **ServiceNow Troubleshooting**: See `SERVICENOW_TROUBLESHOOTING.md`
- **React Frontend**: See `frontend/README.md`
- **API Documentation**: Visit http://localhost:8000/docs when backend is running

---

## 🎯 Next Steps

1. **Install Node.js** if not already installed
2. **Configure ServiceNow** following steps above
3. **Start Backend** API
4. **Start Frontend** development server
5. **Test Integration** by creating a transfer
6. **Verify Ticket** in ServiceNow instance

---

## 📧 Support

For issues or questions:
1. Check `SERVICENOW_TROUBLESHOOTING.md`
2. Run test scripts: `test_servicenow_integration.py`
3. Check backend logs for error messages
4. Verify all environment variables are set

---

**🚀 FileFerry - AI-Powered File Transfer Agent with ServiceNow Integration**
