# r4r - Super Easy Render CLI

🚀 The simplest and most powerful way to manage your Render deployments with advanced features.

[English](#english) | [ไทย](#ไทย)

## Features

- **🚀 Complete Service Management**: Deploy, rebuild, and manage all your Render services
- **⚡ One-Off Jobs**: Create and monitor background jobs with real-time status
- **📊 Detailed Information**: Rich service details, deployment history, and logs
- **🔍 Log Viewing**: Stream and view service logs directly from CLI
- **🔐 Secure Authentication**: API key management with user information
- **🎨 Beautiful UI**: Rich terminal interface with progress indicators
- **⚡ Fast**: Built with modern Python tooling (uv, typer, rich)
- **🌐 Network Resilient**: Advanced error handling and retry logic

## Quick Install

```bash
# One-line installation
curl -sSL https://raw.githubusercontent.com/your-username/r4r/main/install.sh | bash

# Or with wget
wget -qO- https://raw.githubusercontent.com/your-username/r4r/main/install.sh | bash
```

## Manual Install

```bash
# Using uv (recommended)
uv tool install r4r

# Using pip
pip install r4r
```

## Quick Start

```bash
# 1. Login with your Render API key
r4r login

# 2. List your services
r4r list

# 3. Deploy a service
r4r deploy myapp

# 4. Deploy with cache clear (rebuild)
r4r deploy myapp --clear
```

## Commands

### Authentication & User Management
| Command | Description | Example |
|---------|-------------|---------|
| `r4r login` | Login with API key | `r4r login --key xxx` |
| `r4r whoami` | Show current user info | `r4r whoami` |
| `r4r logout` | Logout and remove credentials | `r4r logout` |

### Service Management
| Command | Description | Example |
|---------|-------------|---------|
| `r4r list` | List all services | `r4r list --detailed` |
| `r4r info <name>` | Show detailed service info | `r4r info myapp` |
| `r4r deploy <name>` | Deploy service | `r4r deploy myapp` |
| `r4r deploy <name> --clear` | Deploy with cache clear | `r4r deploy myapp -c` |
| `r4r rebuild <name>` | Clear cache + deploy | `r4r rebuild myapp` |

### Deployments & Logs
| Command | Description | Example |
|---------|-------------|---------|
| `r4r deploys <name>` | List recent deployments | `r4r deploys myapp` |
| `r4r logs <name>` | View service logs | `r4r logs myapp --lines 50` |

### One-Off Jobs
| Command | Description | Example |
|---------|-------------|---------|
| `r4r job <name> <command>` | Create and run a job | `r4r job myapp "npm run migrate"` |
| `r4r jobs <name>` | List recent jobs | `r4r jobs myapp` |
| `r4r status <job_id>` | Get job status | `r4r status job-abc123` |

## Options

### Global Options
- `--help`: Show help information
- `--version`: Show version information

### Command-Specific Options
- `--clear, -c`: Clear cache and rebuild
- `--yes, -y`: Skip confirmation prompts
- `--key, -k`: Provide API key directly
- `--detailed, -d`: Show detailed information
- `--lines, -n`: Number of log lines to show
- `--limit, -l`: Limit number of results
- `--wait, -w`: Wait for job completion
- `--follow, -f`: Follow log output (streaming)
- `--type, -t`: Filter by service type
- `--plan, -p`: Specify plan for jobs

## Examples

### Basic Usage
```bash
# Login and check user info
r4r login --key rnd_xxx...
r4r whoami

# List all services with details
r4r list --detailed

# Get detailed info about a service
r4r info myapp

# Deploy with confirmation
r4r deploy myapp

# Deploy and clear cache without confirmation
r4r deploy myapp --clear --yes

# Rebuild (shorthand for --clear)
r4r rebuild myapp
```

### Advanced Features
```bash
# View service logs
r4r logs myapp --lines 100
r4r logs myapp --follow  # Stream logs

# List recent deployments
r4r deploys myapp --limit 5

# Create and run a job
r4r job myapp "rails db:migrate"
r4r job myapp "npm run build" --wait  # Wait for completion

# Monitor jobs
r4r jobs myapp
r4r status job-abc123

# Filter services by type
r4r list --type web_service
r4r list --type background_worker
```

## API Key Setup

### Method 1: Interactive Login
1. Get your API key from [Render Dashboard](https://dashboard.render.com/u/settings#api-keys)
2. Run `r4r login` and paste your key when prompted
3. Verify with `r4r whoami`

### Method 2: Direct Login
```bash
r4r login --key rnd_xxx...
```

### Method 3: Environment Variable
```bash
export RENDER_API_KEY=rnd_xxx...
r4r list  # Will use the environment variable
```

### การดึง API Key (Thai)
สามารถดึง API key ได้หลายวิธี:
- ผ่าน CLI: `r4r login --key your_api_key`
- ผ่าน Environment Variable: `export RENDER_API_KEY=your_key`
- ผ่าน Interactive Mode: `r4r login` แล้วใส่ key เมื่อถูกถาม

## Development

```bash
# Clone the repo
git clone https://github.com/your-username/r4r.git
cd r4r

# Install in development mode
uv sync
uv run r4r --help

# Run tests
uv run pytest

# Build
uv build
```

---

# ไทย

## คุณสมบัติ

- **🚀 จัดการเซอร์วิสแบบครบครัน**: Deploy, rebuild และจัดการ Render services ทั้งหมด
- **⚡ One-Off Jobs**: สร้างและติดตาม background jobs แบบ real-time
- **📊 ข้อมูลละเอียด**: ข้อมูลเซอร์วิส, ประวัติ deployment และ logs
- **🔍 ดู Logs**: ดู logs ของเซอร์วิสโดยตรงจาก CLI
- **🔐 ระบบรักษาความปลอดภัย**: การจัดการ API key พร้อมข้อมูลผู้ใช้
- **🎨 UI สวยงาม**: Terminal interface แบบ rich พร้อม progress indicators
- **⚡ เร็ว**: สร้างด้วย Python tooling สมัยใหม่
- **🌐 ทนทานต่อเครือข่าย**: การจัดการ error และ retry logic ขั้นสูง

## การติดตั้ง

```bash
# ติดตั้งด้วย uv (แนะนำ)
uv tool install r4r

# หรือใช้ pip
pip install r4r
```

## การใช้งานเบื้องต้น

```bash
# 1. Login ด้วย API key
r4r login

# 2. ดูรายการ services
r4r list

# 3. Deploy service
r4r deploy myapp

# 4. ดู logs
r4r logs myapp

# 5. สร้าง job
r4r job myapp "npm run migrate"
```

## คำสั่งหลัก

### การยืนยันตัวตน
- `r4r login` - เข้าสู่ระบบด้วย API key
- `r4r whoami` - แสดงข้อมูลผู้ใช้ปัจจุบัน
- `r4r logout` - ออกจากระบบ

### การจัดการ Services
- `r4r list` - แสดงรายการ services ทั้งหมด
- `r4r info <ชื่อ>` - แสดงข้อมูลละเอียดของ service
- `r4r deploy <ชื่อ>` - Deploy service
- `r4r rebuild <ชื่อ>` - ล้าง cache และ deploy ใหม่

### Logs และ Deployments
- `r4r logs <ชื่อ>` - ดู logs ของ service
- `r4r deploys <ชื่อ>` - แสดงประวัติ deployment

### One-Off Jobs
- `r4r job <ชื่อ> <คำสั่ง>` - สร้างและรัน job
- `r4r jobs <ชื่อ>` - แสดงรายการ jobs
- `r4r status <job_id>` - ตรวจสอบสถานะ job

## ตัวอย่างการใช้งาน

```bash
# ดู services แบบละเอียด
r4r list --detailed

# Deploy พร้อมล้าง cache
r4r deploy myapp --clear

# ดู logs 100 บรรทัดล่าสุด
r4r logs myapp --lines 100

# สร้าง job และรอให้เสร็จ
r4r job myapp "rails db:migrate" --wait

# กรอง services ตามประเภท
r4r list --type web_service
```

## การตั้งค่า API Key

### วิธีที่ 1: Login แบบ Interactive
```bash
r4r login
# จากนั้นใส่ API key เมื่อถูกถาม
```

### วิธีที่ 2: Login โดยตรง
```bash
r4r login --key rnd_xxx...
```

### วิธีที่ 3: ผ่าน Environment Variable
```bash
export RENDER_API_KEY=rnd_xxx...
r4r list
```

**หมายเหตุ**: สามารถดึง API key ได้จาก [Render Dashboard](https://dashboard.render.com/u/settings#api-keys)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions:
- Create an issue on [GitHub](https://github.com/your-username/r4r/issues)
- Check the documentation
- Make sure your API key has the correct permissions

---

**หากต้องการความช่วยเหลือ**: สร้าง issue บน GitHub หรือตรวจสอบ API key permissions