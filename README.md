## Set Up Docker on the VM
**If Docker isn't installed on your VM yet:**

Update the package list:
``sudo apt update``
Install Docker:
``sudo apt install -y docker.io``
Verify the installation:
``docker --version``
(Optional) Add your user to the docker group to run Docker without sudo:
``sudo usermod -aG docker $USER`` --whoami
Log out and log back in for this change to take effect.

**Pull the Docker Image**
Log in to your Docker Hub account on the VM:
``docker login``
Enter your username and password.

Pull the Docker image you pushed from your local machine:
``docker pull your-dockerhub-username/your-image-name:your-tag``
Replace ``your-dockerhub-username``, ``your-image-name``, and ``your-tag`` with the actual names.

**Run the Docker Container**
Run the container with a restart policy so it runs 24/7:
``docker run -d --name your-container-name --restart unless-stopped your-dockerhub-username/your-image-name:your-tag``
Example:
``docker run -d --name my_python_app --restart unless-stopped myusername/myscript:latest``

--name: Assigns a name to your container for easy management.
--restart unless-stopped: Ensures the container restarts automatically if it crashes or the VM reboots.

**Check Container Status**
Verify that your container is running:
``docker ps``

View logs for debugging (if needed):
``docker logs your-container-name``

Expose Ports (Optional)
If your application requires access via HTTP/HTTPS or other protocols, expose ports when running the container:
``docker run -d -p 80:80 --name your-container-name --restart unless-stopped your-dockerhub-username/your-image-name:your-tag``

???  -p 80:80 maps port 80 on the VM to port 80 in the container. ???

**Automate Startup on VM Reboot**
Containers with --restart unless-stopped are automatically restarted after a reboot. If you want to ensure Docker starts on boot:

Enable the Docker service:
``sudo systemctl enable docker``

Reboot your VM and verify the container restarts:
``sudo reboot``
``docker ps``

**Update Your Container (If Needed)**
To update your app:

Stop and remove the old container:
``docker stop your-container-name``
``docker rm your-container-name``

Pull the latest image:
``docker pull your-dockerhub-username/your-image-name:your-tag``

Run the updated container:
``docker run -d --name your-container-name --restart unless-stopped your-dockerhub-username/your-image-name:your-tag``

Monitor and Manage Containers
You can use tools like Portainer or set up monitoring to manage your Docker containers easily.
Let me know if you need assistance with any step!