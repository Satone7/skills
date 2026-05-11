---
name: nas-index
description: >
  NAS file system index for /mnt/nas/database. Use this skill whenever the user asks
  about files on the NAS, wants to find something in /mnt/nas/, references downloads,
  backups, media, Docker configs, AI models, photos, or any data stored on the network
  storage. Trigger on phrases like "find on NAS", "in the NAS", "download folder",
  "backup", "media library", "docker config", or any file path starting with /mnt/nas/.
  This skill provides a categorized directory map and search strategy so agents can
  locate files quickly without blind exploration.
---

# NAS File System Index

## Overview

The NAS is mounted at `/mnt/nas/` with a single volume `database` containing the user's
personal data, media, backups, configurations, Docker services, and development files.

**CRITICAL: This skill is READ-ONLY.** Never create, modify, move, or delete any files
under `/mnt/nas/` unless the user explicitly requests it and confirms. The NAS is
shared storage with irreplaceable data.

## Top-Level Directory Map

| Path | Purpose | Notes |
|---|---|---|
| `/mnt/nas/database/Downloads` | General downloads | ISOs, installers, archives, APKs |
| `/mnt/nas/database/backups` | System & personal backups | Desktop backups, archives, important docs |
| `/mnt/nas/database/Configs` | Application configurations | Emby, qBittorrent, GitLab, Gogs, movie tools, xiaoya |
| `/mnt/nas/database/docker-service` | Docker compose & service files | Dify, Emby, GitLab, qBittorrent, nginx, Seafile, etc. |
| `/mnt/nas/database/docker-registry` | Local Docker registry storage | |
| `/mnt/nas/database/emby-library` | Media library for Emby | Movies, TV shows, variety shows, R18, torrents |
| `/mnt/nas/database/Photos` | Photo albums & mobile backups | Dated event albums, mobile backup sync |
| `/mnt/nas/database/MemoSpace` | Memo/note storage | Public and personal (Satone) memos |
| `/mnt/nas/database/Scripts` | Automation scripts | alias-services, qBittorrent downloaders |
| `/mnt/nas/database/ai` | AI/ML related files | exo, models |
| `/mnt/nas/database/Fonts` | Font collections | JetBrains Mono, LXGW Wenkai, FangSong, etc. |
| `/mnt/nas/database/SteamLibrary` | Steam game library | Windows Steam library on NAS |
| `/mnt/nas/database/workspace` | Work/project files | WSL workspace |
| `/mnt/nas/database/wsl` | WSL kernel & config | bzImage, .wslconfig |
| `/mnt/nas/database/ftp` | FTP accessible directories | Downloads, 下载 |
| `/mnt/nas/database/safe_wd8` | WD8 safe backup area | musics, wsp, wsp-local, 资料, backup-logs |
| `/mnt/nas/database/Share` | Shared files | Public share directory |
| `/mnt/nas/database/Caches` | Application caches | Emby cache, ipv6 configs |
| `/mnt/nas/database/logs` | Log storage | var-log, backup test logs |
| `/mnt/nas/database/acme` | ACME SSL certificates | nas.lergo.cc |
| `/mnt/nas/database/云盘缓存文件` | Cloud drive cache | |

## Detailed Subdirectory Index

### Downloads (`/mnt/nas/database/Downloads/`)
Common installers, ISOs, and archives. Typical contents:
- Windows ISOs (`Win11_23H2_...`, `G_WIN10_X64_...`)
- Ubuntu ISOs (`ubuntu-24.04-desktop-amd64.iso`, etc.)
- Software installers (GPU-Z, VMware, WeGame, Clash Verge, etc.)
- Game installers (`植物大战僵尸杂交版`)
- FPGA tools (`FPGAs_AdaptiveSoCs_Unified_2024.1...`)

### Backups (`/mnt/nas/database/backups/`)
- `Important/` — Personal documents (ID cards, marriage cert, diplomas, etc.)
- `desktop-wsp/` — Desktop workspace backups
- `Clash for Windows/` — Application backup
- `eth/`, `wsp/`, `System/` — Various system backups
- `upan_20240209.7z`, `cx1b_20251128.tar.xz` — Dated archive backups
- `~ext4.vhdx/` — VM disk image backup

### Configs (`/mnt/nas/database/Configs/`)
Live application configs (often mounted into Docker containers):
- `acme-ssl/`, `lucky/` — Networking & SSL
- `Emby/`, `Emby-back/` — Media server configs
- `Gitlab/`, `Gogs/` — Git hosting configs
- `moviepilot-v2/`, `movie-robot/`, `mdcx-av/`, `mdcx-fc2/` — Media management
- `qBittorrent/` — Download client
- `rtabby-web-api/` — Web API configs
- `seafile/` — File sync
- `xiaoya/` — Cloud storage proxy configs
- `mysql/` — Database configs

### Docker Services (`/mnt/nas/database/docker-service/`)
Each subdirectory typically contains a `docker-compose.yml`:
- `ai-request-service/` — AI request proxy
- `claude-code-proxy/` — Claude proxy
- `dify/` — LLM app platform
- `emby/`, `emby-r18/` — Media servers
- `gitlab/` — Git hosting
- `grass/` — Grass network node
- `moviepilot-v2/`, `r18/` — Media automation
- `nginx/` — Reverse proxy
- `palworld-server-docker/` — Game server
- `qBittorrent/` — Downloads
- `registry/` — Docker registry
- `seafile/` — File sync
- `tailscale/` — VPN mesh
- `wechat-bot/` — WeChat bot
- `xunlei/` — Thunder/Xunlei downloader

### Emby Library (`/mnt/nas/database/emby-library/`)
- `movies/` — Movie collection
- `tv-shows/` — TV series
- `variety-shows/` — Variety/entertainment shows
- `R18/` — Adult content
- `downloads/` — Pending/temp media
- `tidied/` — Organized media
- `movie-wall/` — Movie wall art/posters
- `torrents/` — Torrent files

### Photos (`/mnt/nas/database/Photos/`)
- `20250510 青岛 家驹婚礼/` — Event album (dated & location)
- `20250621 包头 学妹婚礼/` — Event album
- `MobileBackup/` — Phone photo backups
- `Temporary/` — Temp photo storage

### Safe WD8 (`/mnt/nas/database/safe_wd8/`)
Secondary backup area on WD8 drive:
- `musics/` — Music collection
- `wsp/`, `wsp-local/` — Workspace backups
- `资料/` — Documents
- `backup/`, `backup-logs/`, `Configs/` — Backup infrastructure

### AI (`/mnt/nas/database/ai/`)
- `exo/` — Exo framework
- `models/` — AI/ML model weights

## How to Locate Files

When the user asks for a file on the NAS, follow this strategy:

1. **Consult the index above first.** Check the most likely category directory.
2. **Use `find` with specific names.** Example:
   ```bash
   find /mnt/nas/database -name "*keyword*" -type f 2>/dev/null
   ```
3. **Search by file type in known directories.** Example for media:
   ```bash
   find /mnt/nas/database/emby-library -type f \( -name "*.mp4" -o -name "*.mkv" \) 2>/dev/null
   ```
4. **Use `locate` if available** (requires `mlocate`/`plocate`):
   ```bash
   locate -i keyword | grep /mnt/nas
   ```
5. **For recent downloads**, check `Downloads/` first.
6. **For configs**, check `Configs/<app-name>/`.
7. **For media**, check `emby-library/` or `safe_wd8/musics/`.
8. **For photos**, check `Photos/` with dated album names.
9. **For scripts**, check `Scripts/` and `docker-service/*/docker-compose.yml`.

## Naming Conventions

- Event photos: `YYYYMMDD 地点 事件` format (e.g., `20250510 青岛 家驹婚礼`)
- ISOs: `操作系统_版本_架构.iso`
- Docker services: directory name matches service name
- Backup archives: often dated (`*_YYYYMMDD.*`)

## Read-Only Rules

- NEVER write to `/mnt/nas/` without explicit user confirmation
- NEVER move or rename files
- NEVER delete files (even in `$RECYCLE.BIN`)
- NEVER run `chmod`, `chown`, or permission changes
- Reading, listing, searching, and copying FROM the NAS is always safe
