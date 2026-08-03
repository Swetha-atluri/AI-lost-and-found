# 🤖 AI Lost & Found Assistant

An AI-powered Lost & Found web application that automatically matches lost and found items using text and image similarity. The system sends email notifications when a potential match is identified, making the recovery process faster and more efficient.

---

## 🚀 Features

- 🔐 JWT Authentication
- 📝 Lost & Found Item Reporting
- 🖼️ Image Upload Support
- 🤖 AI-Based Text & Image Matching
- ⚡ FAISS Semantic Search
- 📧 Automatic Email Notifications
- 📊 User Dashboard & Match History

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| Frontend | React, Vite, Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | SQLite |
| AI Models | Sentence Transformers, OpenCLIP |
| Vector Search | FAISS |
| Image Processing | OpenCV, Pillow |
| Authentication | JWT |

---

## 📂 Project Structure

```text
backend/
├── app/
├── static/
├── uploads/
├── test_images/
├── mock_emails/
├── requirements.txt
└── main.py
```

---

## ⚙️ Installation

```bash
git clone https://github.com/Swetha-atluri/AI-lost-and-found.git
cd AI-lost-and-found/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit: **http://localhost:8000**

---

## 📌 Key Highlights

- AI-powered semantic matching for lost and found items.
- Combines NLP and Computer Vision for accurate results.
- Secure authentication with JWT.
- Automated email notifications for matched items.

---

## 👩‍💻 Author

**Swetha Atluri**

- GitHub: https://github.com/Swetha-atluri
- LinkedIn: https://www.linkedin.com/in/swethaatluri
