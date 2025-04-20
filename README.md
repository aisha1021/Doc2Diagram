# Doc2Diagram

**Doc2Diagram** is a prototype AI-powered web application that transforms documentation, images, and hand-drawn sketches into clear and professional workflow diagrams. This project serves as an extension to previous work on AI agent development, envisioning future deployment alongside tools such as **Microsoft Copilot** for seamless integration into workplace productivity environments.

## 🔍 Overview

This application demonstrates the capabilities of an intelligent assistant that can analyze content and generate structured visual outputs. Whether it's handwritten notes or technical documents, Doc2Diagram translates them into usable and visually digestible diagrams — streamlining documentation workflows in both academic and professional settings.

## 🛠️ Technologies Used

- **Frontend**: React + TypeScript + Vite  
- **Backend**: Python (Flask)  
- **AI Model**: Google Gemini (via `google.generativeai`)  
- **Deployment**:  
  - Frontend hosted as a static site (e.g., Render)  
  - Backend deployed as a web service (e.g., Render)

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/Doc2Diagram.git](https://github.com/aisha1021/Doc2Diagram.git)
cd Doc2Diagram
```

### 2. Run the Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Ensure your environment contains a valid `GEMINI_API` key in a `.env` file.

### 3. Run the Frontend

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Your application should now be live at `http://localhost:5173` (or the port Vite specifies).

## 🧠 Example Workflow

### Input: Hand-Drawn Diagram

Upload a scanned or photographed image of a handwritten diagram to the interface.

### Output: Digital Diagram

The AI analyzes the content and produces a cleaned-up, readable, and logical digital workflow diagram, ready for further editing or sharing.

> ✨ This feature is particularly useful for converting whiteboard notes and meeting sketches into formal documentation.

## 🚀 Future Scope

As a working prototype, **Doc2Diagram** offers a glimpse into the future of intelligent productivity tools. Planned enhancements include:

- Diagram editing and customization features  
- Integration with Microsoft 365 and Google Workspace  
- Personalized diagram suggestions based on user profiles  
- Natural language input for diagram generation
