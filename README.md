# WgpArch Forensic File Repair

<div align="center">

[![Website](https://img.shields.io/badge/Visit-Website-1793d1?style=for-the-badge&logo=firefox)](https://wgparch.github.io/wgparch-data-recovery/)
[![South Africa](https://img.shields.io/badge/South_Africa-Only-007749?style=for-the-badge&logo=googlemaps)]()
[![No Fix No Fee](https://img.shields.io/badge/No_Fix_No_Fee-Guaranteed-2ecc71?style=for-the-badge)]()
[![Pricing](https://img.shields.io/badge/Pricing-R50_R150-e67e22?style=for-the-badge)]()

</div>

---

## 🔧 Services

Professional forensic file repair using advanced Linux recovery tools that most shops don't have.

| Category | Formats |
|----------|---------|
| 📸 Photos | JPEG, PNG, WebP, GIF |
| 🎥 Video | MP4, AVI, MKV, MOV |
| 🎵 Music | MP3, WAV, FLAC, AAC |
| 📄 Documents | PDF, DOCX, XLSX, ODT |
| 📦 Archives | ZIP, RAR, 7Z |

## 💰 Pricing

- **R50** — Non-refundable analysis fee
- **R150** — Repair fee (only if successful)
- **R200 total** — Maximum cost per file
- ✅ **No Fix, No Fee Guarantee**

## 📍 Service Area

**South Africa only** — EFT payment to GoTyme Bank

## 🌐 Website

**[https://wgparch.github.io/wgparch-data-recovery/](https://wgparch.github.io/wgparch-data-recovery/)**

Submit your corrupted file for professional analysis and repair.

---

## 🔧 Technical Implementation: R2 File Upload System

### Architecture
- **Frontend**: Direct browser upload via presigned URLs (no server relay)
- **Backend**: Cloudflare Worker (`wgparch-r2-uploader`) generates SigV4-signed PUT URLs
- **Storage**: Cloudflare R2 bucket `wgparch-uploads` (10GB free tier, $0 egress)
- **Integration**: Uploaded file URL auto-fills Brevo form field → parsed by email watcher → stored in GTK tracker DB

### Security Model
- R2 credentials stored **only** in `~/.config/wgparch-data-recovery/config.yaml` (never committed to Git)
- Wrangler secrets encrypted at edge; never exposed to browser or logs
- Presigned URLs expire after 1 hour; scoped to specific upload key
- CORS restricted to authorized origins only

### Local Development
```bash
# Test site locally
cd ~/.dotfiles/wgparch-data-recovery
python3 -m http.server 8080

# Update Worker (requires Wrangler auth + secrets)
cd ~/.config/projects/wgparch-r2-worker
wrangler deploy
