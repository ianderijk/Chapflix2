# Docker build command
sudo docker build -t chapflix2 -f infra/docker/Dockerfile .

# Docker run command
sudo docker run  -p 8042:8042  -e DATABASE_URL="postgresql://postgres:<password>@192.168.0.29:5432/chapflix"  -v /media/ianderijk/Backup/Chapflix2/content:/app/content  chapflix2