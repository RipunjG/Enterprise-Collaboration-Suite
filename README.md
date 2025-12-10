# Enterprise Collaboration Suite

A modern, full-stack application designed to enhance internal communication and productivity within an organization. This platform integrates core business tools into a single, intuitive interface, built with a focus on security, scalability, and real-time performance.

## Features

-   **Real-time Chat:** An instant messaging system supporting one-on-one and group communication with persistent message history.
-   **Organizational Hierarchy:** A dynamic system to model and visualize the company's reporting structure, complete with tools for assigning managers and employees.
-   **Meeting Management:** A comprehensive suite for scheduling, planning, and managing virtual meetings.
-   **Secure Authentication:** A robust user registration and login system powered by JWTs to ensure secure and authorized access.

## Technology Stack

**Backend**
-   **Framework:** FastAPI (Python) - Chosen for its high performance and asynchronous capabilities, ideal for handling real-time requests.
-   **Real-time Communication:** WebSockets - The standard protocol for low-latency, bi-directional data transfer.
-   **Message Broker:** Redis - Used for its high-speed Pub/Sub functionality, enabling efficient message broadcasting to all connected clients.
-   **Database:** PostgreSQL - An enterprise-grade, relational database providing strong data integrity and powerful schema management.
-   **Authentication:** JWT (JSON Web Tokens) - For secure, stateless authentication.

**Frontend**
-   **Framework:** React.js - For building a dynamic and responsive user interface with a component-based architecture.
-   **Core Languages:** JavaScript, HTML, CSS - The foundation of the web application.

## Architecture

The application follows a clean, layered architecture:

-   **Client:** The React.js frontend sends requests to the backend API and maintains a persistent WebSocket connection for real-time updates.
-   **Server:** A FastAPI backend manages all business logic, authenticates users, and interacts with the database.
-   **Real-time Engine:** WebSocket connections are managed by the FastAPI server, which uses Redis as a message broker to efficiently broadcast messages to all relevant clients.
-   **Data Storage:** A PostgreSQL database securely stores all application data, including user profiles, chat history, and the organizational hierarchy.

## Project Documentation

This project demonstrates a professional understanding of:

-   **Full-Stack Development:** Expertise in both frontend and backend development.
-   **Real-time Systems:** Building and managing real-time applications using WebSockets and Pub/Sub patterns.
-   **Scalable Architecture:** Designing a system that can handle a large number of concurrent users by leveraging asynchronous programming and message brokers.
-   **Security:** Implementing secure authentication and managing sensitive data through best practices like environment variables and JWTs.

## Getting Started

To run the project locally, you will need Python 3.8+ and Docker (for setting up PostgreSQL and Redis).

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/RipunjG/Enterprise-Collaboration-Suite
    cd Enterprise-Collaboration-Suite
    ```

2.  **Set up the backend:**
    -   Create a `.env` file from `.env.example`.
    -   Run `docker-compose up -d` to start the database and Redis.
    -   Create and activate a virtual environment (`python -m venv venv`).
    -   Install dependencies (`pip install -r requirements.txt`).
    -   Run database migrations.
    -   Start the FastAPI server.

3.  **Set up the frontend:**
    -   Navigate to the frontend directory.
    -   Install dependencies (`npm install`).
    -   Start the development server (`npm start`).

*Note: Detailed instructions and specific commands will be provided in the project files.*
