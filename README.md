# 🚀 SASTRA Apex Converter

SASTRA Apex Converter is a **Windows desktop application** that converts **C++ code into Rust** using both **rule-based logic** and an **AI-powered deep learning model**.  
Built with **Electron** for the frontend and **Flask + PyTorch** for the backend, this tool allows developers and students to explore C++ to Rust translation in an interactive, easy-to-use interface.

## 🧠 Features

- 🔄 **Two Conversion Modes**
  - **Rule-based**: Uses deterministic rules defined in `sastra.py`.
  - **AI-based**: Uses a trained deep learning model (`.pth`) built with PyTorch.

- 🖥️ **Cross-Technology Stack**
  - **Frontend**: HTML/CSS + JavaScript (Electron)
  - **Backend**: Flask API server running Python logic and AI model

- 📁 **File I/O**
  - Choose a `.cpp` input file and an output folder
  - Generates `output_sastra.rs` or `output_ai.rs` based on selected mode

- ⚡ **Self-contained EXE**
  - Bundled as a portable `.exe` with the AI model included
  - No need for Python or Node.js after build

## 🏗️ Technologies Used

- [Electron](https://www.electronjs.org/) – Cross-platform desktop framework
- [Flask](https://flask.palletsprojects.com/) – Lightweight Python web server
- [PyTorch](https://pytorch.org/) – Deep learning framework
- [JavaScript + Node.js](https://nodejs.org/) – For frontend + backend bridge


## 📦 Installation & Running (for Development)

> 💡 This app is built and tested on **Windows**.

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/sastra-apex-converter.git
cd sastra-apex-converter
