# NeoBell Development Environment Setup Guide

This guide helps you set up the Python development environment for the NeoBell project quickly and easily.

## 📋 Prerequisites

- **Python 3.8+** installed on your system
- **Git** (for version control)
- **Windows**, **macOS**, or **Linux** operating system

## 🚀 Quick Setup (Recommended)

NeoBell now uses a cross-platform Makefile to automate all setup and execution, both on Windows and Linux.

### 1. Install [Make](https://www.gnu.org/software/make/) if needed

- **Linux:** Usually comes pre-installed on most distributions.
- **Windows:**
  - Recommended: install [GnuWin Make](http://gnuwin32.sourceforge.net/packages/make.htm), [Chocolatey](https://community.chocolatey.org/packages/make), or use the WSL terminal.
  - Alternatively, use the Git Bash terminal.

### 2. Set up the environment with a single command

```bash
make setup
```

This command will:
- Create separate virtual environments for `src` and `components_tests`
- Install all dependencies for each environment
- Create required directories
- Suggest configuration of the `.env` file

### 3. Configure the `.env` file

After setup, run:

```bash
make env-config
```

Follow the instructions shown to copy and edit your `.env` file.

### 4. Run the main application

```bash
make run-src
```

### 5. Run the test/components environment

```bash
make run-components
```

### 6. Clean up environments

```bash
make clean
```

See all available commands with:

```bash
make help
```

## 🔧 Configuration

### 1. Environment Variables

Edit the `.env` file with your actual configuration:

```env
# AWS IoT Configuration
CLIENT_ID=your_sbc_client_id_here
AWS_IOT_ENDPOINT=your_aws_iot_endpoint_here.amazonaws.com
PORT=8883
```

**Example values:**
```env
CLIENT_ID=neobell-device-001
AWS_IOT_ENDPOINT=a1b2c3d4e5f6g7-ats.iot.us-east-1.amazonaws.com
PORT=8883
```

### 2. Required Directories

The setup scripts automatically create these directories:

- `data/` - For application data files
- `models/` - For Vosk speech recognition models
- `certifications/` - For AWS IoT certificates

### 3. AWS IoT Certificates

Place your AWS IoT certificates in the `certifications/` directory:

- `10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-certificate.pem.crt`
- `10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-private.pem.key`
- `AmazonRootCA1.pem`

### 4. Vosk Models

Download and place Vosk models in the `models/` directory:

- `models/vosk-model-small-en-us-0.15/` (currently configured)
- `models/vosk-model-en-us-0.22/` (alternative model)

You can download models from: https://alphacephei.com/vosk/models

## 🏃‍♂️ Running the Application

After setup, simply run:

```bash
make run-src
```

To run the test/components environment:

```bash
make run-components
```

## 📁 Project Structure

```
NeoBell/
├── src/                    # Source code
│   ├── main.py            # Main application entry point
│   ├── ai_services/       # AI processing services
│   ├── communication/     # AWS IoT communication
│   ├── config/           # Configuration modules
│   ├── flows/            # Application flows
│   ├── hal/              # Hardware abstraction layer
│   └── services/         # Business logic services
├── venv-src/             # Virtual environment for src (created by Makefile)
├── venv-components/      # Virtual environment for components_tests (created by Makefile)
├── data/                 # Application data (created by setup)
├── models/               # ML models (created by setup)
├── certifications/       # AWS certificates (created by setup)
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your actual environment variables
├── Makefile             # Cross-platform automation (setup, run, clean, etc)
└── SETUP.md            # This setup guide
```

## 🔍 Troubleshooting

### Common Issues

1. **Python version too old:**
   - Ensure you have Python 3.8 or higher
   - Use `python --version` to check

2. **Virtual environment not activating:**
   - Make sure you're in the project root directory
   - Try using the full path to the activation script

3. **Dependencies failing to install:**
   - Upgrade pip: `pip install --upgrade pip`
   - Try installing dependencies one by one

4. **AWS IoT connection issues:**
   - Verify your certificates are in the correct location
   - Check your `.env` file configuration
   - Ensure your AWS IoT endpoint is correct

5. **Audio device not found:**
   - The application looks for "USB PnP Sound Device"
   - Make sure your microphone is connected and recognized

### Getting Help

If you encounter issues:

1. Check the application logs in the terminal
2. Verify all prerequisites are met
3. Ensure all configuration files are properly set up
4. Try running the setup script again

## 🧪 Development

### Adding New Dependencies

1. Activate the virtual environment
2. Install the package: `pip install package_name`
3. Update requirements: `pip freeze > requirements.txt`

### Code Structure

- Follow Python PEP 8 style guidelines
- Use type hints where appropriate
- Add logging for debugging purposes
- Follow the existing project structure



## 📝 Notes

- The Makefile replaces old setup and run scripts.
- The project requires AWS IoT certificates and Vosk models (see above).
- Audio devices must be properly configured for speech recognition.
- The project is designed for Raspberry Pi, but can be developed on other systems.
- Environment variables are loaded from the `.env` file.

---

Happy coding! 🚀