# Use an official Python runtime as the base image
FROM python:3.12.5

# Set the working directory in the container
# WORKDIR /app makes /app the default folder inside the container.
WORKDIR /app


# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
#COPY . . copies everything from your local LKGPT directory into /app in the container.
COPY . .
# Ensure Creds folder is included
COPY Creds /app/Creds
# Ensure Md files folder is included
COPY Mdfiles /app/Mdfiles

# Expose the port that the application will run on
EXPOSE 8000

# Define the command to run the application
# Replace Main.py with your actual entry-point script name, if it changes.
CMD ["python", "Main.py"]