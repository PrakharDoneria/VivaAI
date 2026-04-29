# 🎙️ VivaAI: AI Interview Platform

VivaAI is a next-generation AI-powered interview platform designed to streamline the hiring process through real-time communication and intelligent assessment. Built with cutting-edge technologies, VivaAI provides a seamless, professional interviewing experience for both recruiters and candidates.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/prakhardoneria/)
[![Instagram](https://img.shields.io/badge/Instagram-Follow-purple?style=flat-square&logo=instagram)](https://instagram.com/prakhardoneria)

---

## 🚀 Features

- **Real-time Video/Audio**: Powered by WebRTC for low-latency communication.
- **AI-Driven Assessment**: Integrated with SarvamAI for intelligent feedback and question generation.
- **Seamless Signaling**: SocketIO integration for instantaneous state synchronization.
- **Premium UI**: Modern, responsive, and intuitive design for a superior user experience.
- **Automated Workflow**: From scheduling to assessment reports.

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Real-time**: SocketIO, WebRTC
- **AI Integration**: SarvamAI
- **Database**: SQLite (via SQLAlchemy)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/prakhardoneria/VivaAI.git
cd VivaAI
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file in the root directory and add your environment variables (refer to `.env.example`):
```env
SARVAM_API_KEY=your_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

### 5. Run the Application
```bash
python app.py
```
The application will be available at `http://localhost:5000`.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Connect with Me

- **Prakhar Doneria**
- LinkedIn: [in/prakhardoneria](https://www.linkedin.com/in/prakhar-doneria/)
- Instagram: [@prakhardoneria](https://instagram.com/prakhardoneria)
`