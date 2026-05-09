---
title: Docker
nav_order: 6
---

# Docker Deployment

The included `docker-compose.yml` is the recommended way to run defacemon in production.

## Services

| Service | Image | Purpose |
|---|---|---|
| `defacemon` | built from `Dockerfile` | The monitor process + control server + metrics |
| `selenium` | `selenium/standalone-chrome:latest` | Headless Chrome for browser-based resource discovery |

---

## Start

```bash
docker compose up -d --build
```

On startup, defacemon waits for the Selenium container to be healthy before launching.

---

## Control from host

The control port is forwarded to `localhost:9191`, so you can run the CLI directly on your host:

```bash
python defacemon.py add https://example.com
python defacemon.py list
python defacemon.py refresh example.com
python defacemon.py remove example.com
```

Or use the CLI inside the container network:

```bash
docker compose run --rm defacemon python defacemon.py add https://example.com
```

---

## Ports

| Host port | Container port | Purpose |
|---|---|---|
| `9191` | `9191` | TCP control server |
| `9192` | `9192` | Prometheus `/metrics` |
| `4444` | `4444` | Selenium Grid UI / WebDriver endpoint |

---

## Data persistence

Baselines are stored in the `defacemon-data` named volume, mounted at `/data` inside the container. They survive container restarts and rebuilds.

To back up baselines:

```bash
docker run --rm -v defacemon-data:/data -v $(pwd):/backup busybox \
  tar czf /backup/defacemon-baselines.tar.gz /data
```

---

## Logs

```bash
docker compose logs -f defacemon
docker compose logs -f selenium
```

---

## Stopping

```bash
docker compose down          # stop, keep volume
docker compose down -v       # stop + delete volume (destroys all baselines)
```
