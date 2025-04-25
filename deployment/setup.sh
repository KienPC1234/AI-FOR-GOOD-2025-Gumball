#!/bin/bash 
echo "Setting up AI For Good application..." 
mkdir -p /home/ubuntu/ai-for-good/backend /home/ubuntu/ai-for-good/frontend 
cp -r backend/* /home/ubuntu/ai-for-good/backend/ 
cp -r frontend/* /home/ubuntu/ai-for-good/frontend/ 
cd /home/ubuntu/ai-for-good/backend 
python -m venv venv 
source venv/bin/activate 
pip install -r requirements.txt 
python update_db.py 
echo "Creating systemd service..." 
cat > /tmp/backend.service << 'EOL' 
[Unit] 
Description=AI For Good Backend Service 
After=network.target 
 
[Service] 
User=ubuntu 
WorkingDirectory=/home/ubuntu/ai-for-good/backend 
ExecStart=/home/ubuntu/ai-for-good/backend/venv/bin/python run_with_db.py 
Restart=always 
RestartSec=10 
 
[Install] 
WantedBy=multi-user.target 
EOL 
sudo mv /tmp/backend.service /etc/systemd/system/ 
sudo systemctl daemon-reload 
sudo systemctl enable backend.service 
sudo systemctl start backend.service 
echo "Setting up Nginx..." 
cat > /tmp/nginx_config << 'EOL' 
server { 
    listen 80; 
    server_name recyable.ai; 
 
    location / { 
        root /home/ubuntu/ai-for-good/frontend; 
        try_files $uri $uri/ /index.html; 
    } 
 
    location /api { 
        proxy_pass http://localhost:8000; 
        proxy_set_header Host $host; 
        proxy_set_header X-Real-IP $remote_addr; 
    } 
} 
EOL 
sudo mv /tmp/nginx_config /etc/nginx/sites-available/ai-for-good 
sudo ln -sf /etc/nginx/sites-available/ai-for-good /etc/nginx/sites-enabled/ 
sudo nginx -t 
sudo systemctl restart nginx 
echo "Deployment completed successfully!" 
