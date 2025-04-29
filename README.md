# 🧠 Focus Tracker – Automatic Task Logger

A minimal productivity tool that helps you stay on task by **automatically capturing the app or browser tab you're working in**. No need to manually enter what you're doing — just click **"Add Task"**, and let the app do the rest.

## ✨ What It Does

- 🖱️ One-click task tracking — just press **Add Task**
- 🧠 Automatically fetches the **active app or browser tab**
- 🤖 Uses **OpenAI API** to generate a **smart, descriptive title** for each task
- 🧭 Prevents mindless tab switching and forgetting what you were doing
- ✅ Helps build focus and intention by logging actual activity

## 🧪 Example

Suppose you're on a tab with a Zoom meeting, or coding in VSCode. When you hit **Add Task**, the app:

1. Detects the active window or tab (e.g. `Zoom Meeting`, `main.py - VSCode`)
2. Sends context to OpenAI to generate a concise, descriptive task name like:
   - `Team Sync: Marketing Updates`
   - `Bugfixing File Upload in React`

## 📦 Features

- 🚀 Instant task logging from current app/browser
- 🧠 AI-powered task naming (via OpenAI API)
- 📜 History log of tasks you've worked on
- 🔁 Prevents task-hopping with intention-based logging

## 📋 Why This Matters

We all get distracted.  
This tool helps answer the question:  
> *“What was I just doing?”*

By building a real-time log of your activity with smart titles, you're able to:

- Reflect on your work habits
- Stay grounded in what you're doing
- Avoid scattering your attention across apps

## 🛠️ Tech Stack

- Python / JavaScript backend
- [OpenAI API](https://openai.com/api) for natural language task naming
- OS-level window tracking (platform-dependent)
- Optional: Electron/Node integration for GUI or tray app

## 🚧 Future Features (Ideas)

- Daily task summary / export to calendar
- Idle detection (auto stop/start logging)
- Time tracking per task
- User-defined task categories

## 📜 License

MIT — free to use, fork, and improve.

## 🙋‍♀️ Author

Developed by [Nodoka Shibasaki](https://github.com/nodokashibasaki3)
