# NeoBell Smart Intercom: Firmware Documentation

## 1. Project Overview

This document details the firmware for the NeoBell Smart Intercom project, designed to run on a Single-Board Computer (SBC) like the Radxa Rock 5C. The firmware is responsible for all on-device logic, hardware control, and communication with cloud services. It provides a robust, real-time interface for handling visitor interactions and package deliveries.

The system is built on a modular, service-oriented architecture in Python, ensuring that each component is independent and testable. It operates autonomously, initiating interactions via a physical push button and handling all subsequent logic through voice commands, computer vision, and hardware actuation.

### Key Features

- **Dual-Flow Interaction**: Manages two distinct operational flows: a Visitor Flow for recording video messages and a Delivery Flow for secure package drop-offs.
- **Voice-Driven Interface**: Utilizes local Speech-to-Text (STT) and Text-to-Speech (TTS) services to create a natural, hands-free user experience.
- **AI-Powered Vision**: Employs on-device AI for face recognition (to identify known visitors) and Optical Character Recognition (OCR) for reading QR codes and Data Matrix codes on packages.
- **Robust Hardware Control**: A dedicated Hardware Abstraction Layer (HAL) manages GPIO pins for controlling locks, LEDs, and servo motors for the delivery hatch.
- **Real-time RFID Access**: A non-blocking, asynchronous listener continuously monitors for RFID tag swipes to provide an alternative, quick access method for registered users.
- **Cloud Integration**: Securely communicates with an AWS backend via MQTT to validate permissions, package information, and user credentials.
- **Autonomous Operation**: Designed to run as a systemd service, ensuring it starts automatically on boot and restarts on failure.

## 2. System Architecture

The firmware is designed with a clear separation of concerns, making it maintainable and scalable. The core logic is divided into distinct layers and services.

- **main.py (Orchestrator)**: The main entry point of the application. The Orchestrator class is responsible for initializing all services, managing their lifecycle, and running the main interaction loop which waits for a physical button press.
- **flows/ (Application Flows)**: This directory contains the high-level business logic.
  - `visitor_flow.py`: Manages the entire sequence for a visitor interaction.
  - `delivery_flow.py`: Manages the multi-step process for a package delivery.
- **services/ (Core Services)**: These are independent modules that provide specific functionalities to the flows. Examples include TTSService, STTService, RfidListenerService, ServoService, and UserManager. This design allows for easy swapping of implementations (e.g., changing the TTS engine).
- **ai_services/ (AI and Vision Services)**: Contains services that handle complex processing tasks.
  - `face_processing.py`: Manages face recognition and video recording.
  - `ocr_processing.py`: Handles QR code and Data Matrix scanning.
- **communication/ (Cloud Communication)**:
  - `aws_client.py`: A dedicated client for handling all MQTT communication with the AWS backend, abstracting away topics and message formats.
- **hal/ (Hardware Abstraction Layer)**: This layer isolates the application logic from the specific hardware details.
  - `gpio.py`: Low-level GpioManager that interfaces directly with the gpiod library.
  - `pin_service.py`: A high-level GpioService that provides meaningful names to hardware actions (e.g., set_collect_lock()).
- **config/ (Configuration)**:
  - `logging_config.py`: A centralized module to configure application-wide logging.

## 3. Installation and Setup

Follow these steps to set up the firmware environment on a compatible Linux-based SBC (e.g., Radxa Rock 5C running Debian/Ubuntu).

### 3.1. Prerequisites

- A Linux-based operating system.
- Python 3.9 or higher.
- git for cloning the repository.
- System dependencies for required libraries.

### 3.2. Step-by-Step Installation

1. **Clone the Repository**
  ```bash
  git clone <your-repository-url>
  cd NeoBell/Firmware/
  ```

Install System Dependencies
These are required for libraries like pyttsx3 (PicoTTS), sounddevice, and computer vision packages.
bash

  ```bash
   git clone <your-repository-url>
   sudo apt-get update
   sudo apt-get install -y espeak-ng libttspico-utils ffmpeg libasound2-dev portaudio19-dev libgpiod-dev
  ```

Create a Python Virtual Environment
This isolates the project's dependencies.

   ```bash
    python3 -m venv venv
    source venv/bin/activate
   ```

Install Python Libraries
Install all required Python packages from the requirements.txt file.

   ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
   ```

Configure Environment Variables
The application uses a .env file to manage sensitive credentials.

    Copy the template file:

   ```bash
    cp .env.example .env
   ```

Edit the new .env file with your specific AWS credentials:

   ```bash
    nano .env
   ```

Fill in the following values:
   ```ini
    # AWS IoT Configuration
    CLIENT_ID=your_sbc_client_id_here
    AWS_IOT_ENDPOINT=your_aws_iot_endpoint_here.amazonaws.com
    PORT=8883
   ```

Place Required Assets

  AWS Certificates: Place your AWS IoT certificate files inside the certifications/ directory.
   ```bash
  your-certificate.pem.crt
  your-private.pem.key
  AmazonRootCA1.pem
   ```
  (Ensure the paths in communication/aws_client.py match the filenames).

## 4. Running the Application

There are two ways to run the firmware: for development/testing and as an autonomous service on boot.
### 4.1. For Development and Testing

This method allows you to see live log output directly in your terminal.

Navigate to the src directory:
  ```bash
  cd /path/to/NeoBell/Firmware/src
  ```

Activate the virtual environment:
  ```bash
  source venv/bin/activate
  ```

Run the main script:
  ```bash
  python main.py
  ```
Press Ctrl+C to stop the application.

### 4.2. For Deployment (Automatic Startup)

To make the NeoBell run automatically every time the Radxa board is powered on, we will create a systemd service.

Create the Service File
Use a text editor like nano to create the service definition file:
  ```bash
  sudo nano /etc/systemd/system/neobell.service
  ```

Add the Service Configuration
Copy and paste the following content into the file. Ensure the paths are correct for your system.
```ini

[Unit]
Description=NeoBell Main Application Service
# Ensures the service starts after the network and sound system are ready
After=network.target sound.target

[Service]
# Run the service as the 'radxa' user (or your username)
User=radxa
Group=radxa

# Set the working directory to your project's src folder
WorkingDirectory=/home/radxa/Desktop/NeoBell/src

# The command to execute, using the absolute path to the venv's Python
ExecStart=/home/radxa/Desktop/NeoBell/src/venv/bin/python /home/radxa/Desktop/NeoBell/src/main.py

# Restart the service automatically if it fails
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Manage the Service
After saving the file, run these commands to enable and start the service:

Reload systemd to recognize the new file:
  ``` bash
  sudo systemctl daemon-reload
  ```

Enable the service to start on boot:
  ```bash
  sudo systemctl enable neobell.service
  ```

Start the service immediately:
  ```bash
  sudo systemctl start neobell.service
  ```

#### Useful Service Commands:
  Check status and recent logs: 
  ```bash
    sudo systemctl status neobell.service
  ```
  View live logs:
  ```bash
     sudo journalctl -u neobell.service -f
  ```
  Stop the service: 
  ```bash
    sudo systemctl stop neobell.service
  ```
  Restart the service: 
  ```bash
    sudo systemctl restart neobell.service
  ```


## 5. Project Structure
```text
Firmware/
├── ai_services/        # Computer Vision and other AI services
├── certifications/     # Directory for AWS IoT certificates
├── communication/      # AWS IoT communication client
├── config/             # Centralized configuration modules (e.g., logging)
├── data/               # Directory for runtime data (e.g., captures, user db)
├── flows/              # High-level business logic for user interactions
├── hal/                # Hardware Abstraction Layer (GPIO, Servos)
├── services/           # Core application services (TTS, STT, RFID, etc.)
├── main.py             # Main application entry point and Orchestrator
├── phrases.py          # Centralized user-facing text phrases
├── .env.example        # Template for environment variables
├── README.md           # This file
└── requirements.txt    # List of Python dependencies for pip
```
