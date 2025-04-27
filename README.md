# GumMed AI

GumMed AI is a fully designed web application, targeting patients or doctors who wants their medical scans analyzed and reported remotely. In addition, it also involves an LLM to provide guidance and support both distanced patients and hospital doctors gaining more insight into the disease as well as curing them.

## Installation

The repository includes two main parts. The `front-end` powered by node.js and Python fastapi server serves as the `backend`.

We have tested on Node.js version `18.x` (lower than `12.x` doesn't work), and Python `3.12`

1. Setting up front-end

```bash
# CD to the frontend folder
cd ./frontend
# Install required packages
npm install
# Run the server locally
npm run dev -- --hostname localhost
```

2. Setting up back-end

```bash
# CD to the backend folder
cd ./backend
# Install required packages
pip install -r requirements.txt
# Edit .env with your configuration
cp .env.example .env
# Run the server
python run_with_db.py
```

There is also `Celery` inside the package, but currently it isn't needed.
