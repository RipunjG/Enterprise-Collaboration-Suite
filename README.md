# Enterprise Suite

A modern, full-stack application designed to simulate a real-world corporate communication environment. This platform integrates organizational management and real-time messaging into a single, intuitive interface, built with a focus on recursive data structures, security, and low-latency performance.

## Features

-   **Real-time Chat:** An instant messaging system supporting persistent one-on-one and team-based communication using WebSockets.
-   **Organizational Hierarchy:** A dynamic, recursive system to model infinite levels of reporting structures (HQ -> Department -> Team), with visual tree management.
-   **Smart Context:** Users are restricted to communicating only within their assigned teams, enforcing organizational security boundaries.
-   **Secure Authentication:** A robust user registration and login system powered by JWTs (JSON Web Tokens) and Argon2 password hashing.
-   **Modern UI/UX:** A responsive Single Page Application (SPA) featuring Dark Mode, Glassmorphism design, and smooth transitions.

## Technology Stack

**Backend**
-   **Framework:** FastAPI (Python) - Chosen for its high performance and native asynchronous support.
-   **Real-time Communication:** WebSockets - Direct, bi-directional connections for instant message delivery.
-   **Database:** PostgreSQL - An enterprise-grade relational database handling complex recursive queries for organizational trees.
-   **ORM:** SQLAlchemy - Manages database interactions with advanced relationship mapping (Self-Referential/Recursive).
-   **Authentication:** JWT (JSON Web Tokens) - For secure, stateless session management.

**Frontend**
-   **Architecture:** Vanilla JavaScript (ES6+) - A lightweight, dependency-free Single Page Application (SPA) architecture.
-   **Styling:** CSS3 Variables & Flexbox - Custom theming engine with native Dark Mode support.
-   **Interface:** Pure HTML5 - Semantic structure without the overhead of heavy frontend frameworks.

**Infrastructure**
-   **Containerization:** Docker & Docker Compose - Orchestrates the application and database services for consistent deployment.

## Architecture

The application follows a clean, Micro-Monolith architecture:

-   **Client:** The Vanilla JS frontend establishes a persistent WebSocket connection for real-time updates and fetches REST API data for structural changes.
-   **Server:** A FastAPI backend manages all business logic, enforces role-based access control, and routes messages.
-   **Data Layer:** PostgreSQL stores relational data, including the recursive adjacency list used to build the organizational tree.
-   **Security Layer:** Passwords are salted and hashed using Argon2; API endpoints are protected via OAuth2 dependency injection.

## Project Documentation

This project demonstrates a professional understanding of:

-   **Full-Stack Development:** Integrating a Python async backend with a raw JavaScript frontend.
-   **Database Engineering:** Implementing recursive Common Table Expressions (CTEs) and Cascade Delete operations for hierarchical data.
-   **Real-time Systems:** Managing WebSocket lifecycles, broadcasting logic, and connection persistence.
-   **Security Best Practices:** Implementing secure authentication flows and managing sensitive data through environment isolation.

## Getting Started

To run the project locally, you will need **Docker Desktop** installed.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/RipunjG/Enterprise-Collaboration-Suite.git](https://github.com/RipunjG/Enterprise-Collaboration-Suite.git)
    cd enterprise-suite
    ```
    
2.  **Start the System:**
    Run the following command to build the backend image and start the database container:
    ```bash
    docker-compose up --build
    ```
    *Wait for the logs to show "Uvicorn running on http://0.0.0.0:8000".*

3.  **Launch the Application:**
    -   Open the `frontend.html` file in any modern web browser.
    -   Register a new user to get started.

4.  **Usage Tips:**
    -   **Initialize:** If the Organization tree is empty, click the initialization button in the hierarchy view to create the Head Office.
    -   **Dark Mode:** Toggle the theme using the moon icon in the sidebar.
