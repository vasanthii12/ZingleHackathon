# SQL Lineage Dashboard

## Table of Contents
- [Overview](#Overview)
- [Project Components](#Project-Components)
- [Features](#Features)
- [Technologies Used](#Technologies-Used)
- [Installation](#Installation)
- [Steps to Install](#Steps-to-Install)
- [Usage](#Usage)

## Overview
This is a web-based SQL Lineage Dashboard designed to visualize the relationships between SQL tables and columns using interactive graphs. It allows users to upload .sql files, generate a lineage graph, and explore how SQL queries are structured.

### Project Components:
1. **AI & ML**: Automatically generate descriptions for SQL query columns using AI.
2. **Backend Development**: APIs to store and process SQL files.
3. **Frontend Development**: Interactive dashboard for SQL Lineage visualization.

## Features
- **AI-Generated Column Descriptions**: Automatically generate and display descriptions for SQL columns.
- **Graph Visualization**: The app generates a lineage graph that visualizes SQL tables and columns and their relationships.
Tables are represented as nodes with their names.
Columns are linked to their respective tables via edges.
-**File Upload**: Allows users to upload multiple .sql files, which are sent to the backend for processing.
- **Search and Filters**: Easily search and filter SQL queries, columns.
- **Responsive UI**: A user-friendly interface built with React (Vite) and TailwindCSS.
 Notifications are provided to indicate the status of file uploads and graph generation.

## Technologies Used
- **Frontend**: React.js, Vite, TailwindCSS, ReactFlow, Custom styles with TailwindCSS and Material-UI
- **Backend**: Python (Flask/FastAPI), SQL File Handling, Data Processing APIs

## Installation

Before running the app, ensure you have the following installed on your machine:
- Python 3.7+
- Node.js (for React/Vite)
- npm 
- A text editor or IDE (e.g., VSCode, PyCharm)

### Steps to Install:

By following these steps, you'll be up and running the application locally! 
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/zingleHackathon.git
   cd zingleHackathon

2. **Backend Setup**

**Install dependencies (e.g., Flask or other Python packages):**
 
   pip install -r requirements.txt

 Start the backend server:
  
  python app.py

  - Make sure the frontend (React app) and backend are running on their respective ports. Update the API URLs in the frontend to match the backend server URLs.
-  you can use the auto-generated API documentation, which is available at http://localhost:8000/docs. This is powered by Swagger UI and provides an interactive way to explore and test your API endpoints.

3. **Frontend Setup**

**Install dependencies:**
npm install
**Run the development server:**
npm run dev
- By default, Vite will run your app on http://localhost:5173.

### Usage

**Upload SQL Files:**
- Click on the "Upload SQL Files" button to select multiple .sql files from your computer.
- The app will process the files, sending them to the backend for analysis.

**Generate Lineage Graph:**

-After the files are uploaded, click on "Create Lineage" to generate the lineage graph.
-The graph will display tables as nodes and columns connected to their respective tables through edges.

**Interactive Graph:**
- The generated graph can be zoomed in/out and panned for better navigation.
- Each table and column node can be visually inspected for relationships.

**Notifications:**

- Success or error messages will appear in a notification bar on screen.
- The notifications inform users about the status of file uploads and lineage graph generation.


Thank you! have a great day :)
