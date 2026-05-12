# VaultMark

A single-file Streamlit app for high-end bulk video watermarking. Upload one master video and generate a unique watermarked copy for each username in a comma-separated list.

## Files

- `app.py` – Streamlit application
- `requirements.txt` – Python dependency list
- `packages.txt` – Streamlit Cloud package support for `ffmpeg`

## Features

- Quiet luxury dark UI with custom CSS
- `.mp4` and `.mov` upload support
- Buyer username list parsing
- Dynamic moving watermark using FFmpeg `drawtext`
- Per-video progress and status updates
- Zip download for all rendered videos
- Cleanup of temporary files after packaging
- Free tier limit: 3 exports per run unless Pro access is enabled

## Deploy to Streamlit Cloud

1. Create a new GitHub repository.
2. Add `app.py`, `requirements.txt`, `packages.txt`, and `README.md`.
3. Go to https://share.streamlit.io and connect your GitHub account.
4. Select the repo and deploy.

Streamlit Cloud will install Python requirements from `requirements.txt` and `ffmpeg` from `packages.txt`.

## Run locally

1. Install Streamlit:

```bash
pip install streamlit
```

2. Install FFmpeg as a system tool:

- Download from https://ffmpeg.org/download.html
- Add the FFmpeg binary to your system `PATH`
- Confirm with `ffmpeg -version`

3. Run the app:

```bash
streamlit run app.py
```

## Notes

- Ensure `ffmpeg` is installed when running locally.
- The app automatically detects missing FFmpeg and shows a clear error message.
- The watermark text is rendered with reduced opacity to preserve the video experience.
