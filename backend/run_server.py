import env_setup
import uvicorn

# Set environment variables
env_setup.set_envs()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
