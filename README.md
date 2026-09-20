# AI Lost & Found Assistant

An AI-powered Lost & Found platform that uses **Natural Language Processing (NLP)** and **Computer Vision** to identify potential matches between lost and found items. The system combines text and image similarity with semantic vector search to make item recovery faster and more efficient.

---

## Overview

The **AI Lost & Found Assistant** is designed to simplify the process of reporting, searching, and recovering lost items.

Users can submit details and images of lost or found items through the application. The system processes the submitted information using AI-based text and image embeddings and searches for semantically similar items using **FAISS**.

By combining textual and visual similarity, the application helps users identify potential matches more efficiently than traditional keyword-based searching.

---

## Features

- **JWT-based Authentication** — Secure user registration and authentication.
- **Lost & Found Reporting** — Submit and manage lost or found item reports.
- **Image Upload** — Upload item images for visual similarity analysis.
- **AI-Based Matching** — Identify potential matches using textual and visual information.
- **Semantic Search** — Use FAISS for efficient vector similarity search.
- **User Dashboard** — Manage submitted items and view relevant information.
- **Match History** — Track previously identified potential matches.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | FastAPI, Python |
| Database | SQLite |
| NLP | Sentence Transformers |
| Computer Vision | OpenCLIP, OpenCV |
| Vector Search | FAISS |
| Image Processing | Pillow |
| Authentication | JWT |

---

## System Workflow

```text
                    User
                     |
                     v
            +------------------+
            |  Web Application  |
            | React + Vite      |
            +--------+---------+
                     |
                     v
            +------------------+
            |   FastAPI API    |
            +--------+---------+
                     |
          +----------+----------+
          |                     |
          v                     v
   +-------------+       +-------------+
   | Text        |       | Image       |
   | Processing  |       | Processing  |
   +------+------+       +------+------+
          |                     |
          v                     v
   Sentence                OpenCLIP
   Transformers            Embeddings
          |                     |
          +----------+----------+
                     |
                     v
              +-------------+
              |    FAISS    |
              |Vector Search|
              +------+------+
                     |
                     v
              Match Detection
                     |
                     v
              Potential Match
