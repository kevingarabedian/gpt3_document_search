# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Expose port 5000 for the Flask app
EXPOSE 5000

# Define environment variable for OpenAI API key
ENV OPENAI_API_KEY=YOUR_API_KEY

# Define environment variable for GPT engine
ENV GPT_ENGINE=davinci

# Define the command to run the Flask app when the container starts
CMD ["python", "app.py"]
