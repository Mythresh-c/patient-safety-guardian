# Deployment Guide

## Option 1: Streamlit Cloud (Easiest)

1.  Push this repository to GitHub.
2.  Go to [share.streamlit.io](https://share.streamlit.io/).
3.  Connect your GitHub account.
4.  Select your repository and branch.
5.  Set "Main file path" to `app.py`.
6.  Click **Deploy**.

## Option 2: Docker (Local or Cloud)

1.  **Build the Docker image**:
    ```bash
    docker build -t patient-safety-guardian .
    ```

2.  **Run the container**:
    ```bash
    docker run -p 8501:8501 patient-safety-guardian
    ```

3.  Access the app at `http://localhost:8501`.

## Option 3: Manual Deployment (VM/VPS)

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the app:
    ```bash
    streamlit run app.py
    ```
