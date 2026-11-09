# Deploying VoiceOps AI (v0.9)

The app runs on one Linux server with Docker. Nothing large is uploaded anywhere: the
server downloads the code from GitHub and builds the images itself.

## What you need

| Item | Why | Notes |
|---|---|---|
| A Linux server (Ubuntu 22.04/24.04) | Runs the containers | 4 CPU and 8 GB RAM recommended (Whisper + pyannote are heavy); 30 GB disk |
| A domain or subdomain | Free automatic HTTPS | e.g. `calls.yourdomain.com`; a free DuckDNS name also works |
| Hugging Face token | Downloads the pyannote model once | Accept the terms of `pyannote/speaker-diarization-community-1`, then create a read token |
| (optional) Anthropic API key | Claude-written summaries | Without it, rule-based summaries are used |

## Steps

1. Create the server at a provider of your choice and note its IP address.
2. Add a DNS **A record**: `calls.yourdomain.com` -> the server IP.
3. Connect from PowerShell:

   ```powershell
   ssh root@SERVER_IP
   ```

4. On the server run the setup script (it installs Docker, adds swap, clones the repo
   and generates strong passwords in `/opt/voiceops/.env`):

   ```bash
   curl -fsSL https://raw.githubusercontent.com/srinivasand04/voiceops-ai/main/deploy/server-setup.sh | DOMAIN=calls.yourdomain.com bash
   ```

5. Add your Hugging Face token (and optionally the Anthropic key), then deploy again:

   ```bash
   nano /opt/voiceops/.env
   DOMAIN=calls.yourdomain.com bash /opt/voiceops/deploy/server-setup.sh
   ```

6. Open `https://calls.yourdomain.com`, click Register. **The first account is the admin.**
   The first processed call downloads the models and is slow; later calls are faster.

## Updating later

```bash
DOMAIN=calls.yourdomain.com bash /opt/voiceops/deploy/server-setup.sh
```

## Monitoring

- **Uptime check:** point a free monitor (UptimeRobot, Better Stack) at
  `https://calls.yourdomain.com/api/health/ready`. It also fails when the database is down.
- **Container health:** `docker ps` shows `healthy` for postgres and backend.
- **Logs:** `docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend`
  (logs rotate at 10 MB x 3 files so the disk does not fill up).
- **Restarts:** containers restart automatically after a crash or server reboot.

## Backups

The database lives in the Docker volume `postgres_data`; audio is in `/opt/voiceops/data/audio`.

```bash
docker exec voiceops-postgres pg_dump -U voiceops_user voiceops > /root/voiceops-$(date +%F).sql
```

## Security checklist

- `.env` is created with random secrets and `chmod 600`; it is never committed.
- Only ports 80 and 443 are open to the internet (Caddy); the database is private.
- Enable the provider firewall for ports 22, 80, 443 only.
- Registration is open: after creating your admin account, consider restricting sign-ups (backlog for v1.0).
