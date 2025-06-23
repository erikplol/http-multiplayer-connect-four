# Multiplayer Connect Four

## Server (Dockerized)
This project uses Docker to run 2 game servers, 1 load balancer, and Redis automatically.

### Build Docker Image
```sh
docker build -t connect4-server .
```

### Run Docker Container
```sh
docker run -p 5000:5000 -p 5001:5001 -p 5002:5002 -p 6380:6379 connect4-server
```
- Game servers: `localhost:5001` and `localhost:5002`
- Load balancer: `localhost:5000`
- Redis: mapping `localhost:6379` to `localhost:6380`

The load balancer will automatically distribute requests to both game servers and keep all room/game data in sync using Redis.

## Client (Pygame)
You can run the game client outside Docker on your host machine.

### 1. Create Python Virtual Environment

#### Ubuntu/Linux
```sh
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows
```bat
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install Requirements
```sh
pip install -r requirements.txt
```

### 3. Run the Client
```sh
python client/main.py
```

The client will connect to the load balancer at `localhost:5000` for multiplayer gameplay.

## Notes
- Make sure Docker is installed and running on your system.
- You can run multiple clients on different machines in the same network by exposing the ports and using the host IP address.
- If you want to run more game servers, you can modify `supervisord.conf` and expose more ports.
