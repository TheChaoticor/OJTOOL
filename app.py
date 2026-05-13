import random
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import streamlit as st


def setup_page() -> None:
    st.set_page_config(page_title="VaultMark", layout="centered")
    st.markdown(
        """
        <style>
        body, .main, .block-container {
            background: #1A1A1A;
            color: #F5F5F5;
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            padding: 48px 24px;
        }
        .css-18e3th9 {
            padding-top: 0rem;
        }
        .reportview-container .main footer, .reportview-container .main header {
            visibility: hidden;
            height: 0;
            margin: 0;
            padding: 0;
        }
        .streamlit-expanderHeader {
            color: #F5F5F5;
        }
        .stButton>button {
            background-color: #BFA77A;
            color: #1A1A1A;
            border: none;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #D4B16A;
        }
        .css-1d391kg {
            max-width: 900px;
            margin: auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def check_ffmpeg_installed() -> bool:
    return shutil.which("ffmpeg") is not None


def parse_usernames(text: str) -> list[str]:
    raw_names = [part.strip() for part in text.replace("\r", "\n").split("\n")]
    names = []
    for raw in raw_names:
        for item in raw.split(","):
            value = item.strip()
            if value:
                names.append(value)
    return names


def sanitize_filename(name: str) -> str:
    safe = "_".join(name.split())
    invalid_chars = "<>:\"/|?*"
    for ch in invalid_chars:
        safe = safe.replace(ch, "_")
    return safe


def get_video_metadata(path: Path) -> tuple[int, int, float] | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
            shell=False,
            check=True,
        )
        width, height, duration = result.stdout.strip().split("\n")
        return int(width), int(height), float(duration)
    except Exception:
        return None


def sanitize_text_for_ffmpeg(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace("%", "%%")
            .replace(":", "\\:")
            .replace("'", "\\'")
            .replace('"', '\\"')
    )


def get_default_system_font() -> Optional[Path]:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/ARIAL.TTF"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def sanitize_font_path(path: Path) -> str:
    safe_path = path.as_posix().replace(":", "\\:")
    return safe_path.replace("'", "\\'")


def build_drawtext_filter(
    username: str,
    width: int,
    height: int,
    duration: float,
    color: str,
    fontsize: int,
    opacity_pct: int,
) -> str:
    safe_text = sanitize_text_for_ffmpeg(f"PROPERTY OF {username}")
    margin = 24
    opacity = max(0.1, min(1.0, opacity_pct / 100.0))

    font_path = get_default_system_font()
    if font_path:
        font_arg = f"fontfile='{sanitize_font_path(font_path)}'"
    else:
        font_arg = "font='DejaVu Sans'"

    x_expr = f"(w-text_w-{margin})/2*(1+sin(t*0.8))"
    y_expr = f"(h-text_h-{margin})/2*(1+cos(t*0.7))"

    return (
        f"drawtext=text='{safe_text}':fontcolor={color}@{opacity:.2f}:fontsize={fontsize}:"
        f"{font_arg}:x={x_expr}:y={y_expr}:shadowcolor=black@0.35:shadowx=2:shadowy=2:"
        f"enable='between(t,0,{duration:.2f})'"
    )


def render_watermarked_video(
    master_path: Path,
    output_path: Path,
    username: str,
    width: int,
    height: int,
    duration: float,
    color: str,
    fontsize: int,
    opacity_pct: int,
) -> None:
    filter_chain = build_drawtext_filter(username, width, height, duration, color, fontsize, opacity_pct)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(master_path),
        "-vf",
        filter_chain,
        "-c:v",
        "libx264",
        "-preset",
        "superfast",
        "-crf",
        "26",
        "-c:a",
        "copy",
        str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, shell=False)


def create_zip_from_files(file_paths: list[Path], zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in file_paths:
            archive.write(file_path, arcname=file_path.name)


def main() -> None:
    setup_page()
    st.title("VaultMark")
    st.write("High-end bulk watermarking for creators. Upload one master video and generate unique copies for each buyer.")

    if not check_ffmpeg_installed():
        st.error(
            "FFmpeg is not available. Install the FFmpeg system binary and add it to your PATH. "
            "On Windows, download it from https://ffmpeg.org/download.html and do not rely on `pip install ffmpeg`. "
            "For Streamlit Cloud, keep `ffmpeg` in `packages.txt`."
        )
        return

    master_file = st.file_uploader("Upload master video", type=["mp4", "mov"])
    usernames_input = st.text_area(
        "Buyer Usernames (comma-separated)",
        placeholder="alice, bob, charlie",
        height=120,
    )
    watermark_color = st.color_picker("Watermark color", "#FFFFFF")
    watermark_size = st.slider(
        "Watermark font size",
        min_value=24,
        max_value=96,
        value=54,
        step=2,
        help="Choose how large the watermark text appears.",
    )
    watermark_opacity = st.slider(
        "Watermark opacity",
        min_value=10,
        max_value=100,
        value=22,
        step=1,
        help="Lower values make the watermark more transparent.",
    )
    pro_access = st.checkbox("Pro access: unlimited watermark exports", value=False)

    if st.button("Protect Content"):
        usernames = parse_usernames(usernames_input)
        if not usernames:
            st.warning("Enter at least one buyer username to continue.")
            return
        if len(usernames) > 3 and not pro_access:
            st.warning(
                "Free tier allows 3 watermarks per day. Check Pro access for unlimited exports."
            )
            return
        if not master_file:
            st.warning("Upload a source video before processing.")
            return

        with st.spinner("Preparing your watermarks..."):
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                master_path = temp_dir_path / "master_video"
                master_path.write_bytes(master_file.read())

                metadata = get_video_metadata(master_path)
                if not metadata:
                    st.error("Unable to read the uploaded video metadata. Confirm the file is valid.")
                    return

                width, height, duration = metadata
                progress_bar = st.progress(0)
                status_text = st.empty()
                result_files = []

                for index, username in enumerate(usernames, start=1):
                    status_text.text(f"Rendering video for {username} ({index}/{len(usernames)})")
                    safe_username = sanitize_filename(username)
                    output_file = temp_dir_path / f"vaultmark_{safe_username}.mp4"
                    try:
                        render_watermarked_video(
                            master_path,
                            output_file,
                            username,
                            width,
                            height,
                            duration,
                            watermark_color,
                            watermark_size,
                            watermark_opacity,
                        )
                        result_files.append(output_file)
                    except subprocess.CalledProcessError as error:
                        st.error(
                            f"FFmpeg failed while processing {username}. Error: {error.stderr.decode(errors='ignore')}"
                        )
                        return
                    progress_bar.progress(index / len(usernames))

                zip_path = temp_dir_path / "vaultmark_output.zip"
                create_zip_from_files(result_files, zip_path)
                zip_bytes = zip_path.read_bytes()

                st.success("All videos protected. Download the ZIP below.")
                st.download_button(
                    "Download Watermarked Videos",
                    zip_bytes,
                    file_name="vaultmark_videos.zip",
                    mime="application/zip",
                )
                status_text.text("Cleanup complete.")

    st.markdown(
        "---\n"
        "**Zero-Cost Deploy:** create a GitHub repo, add `app.py`, `requirements.txt`, and `packages.txt`, then deploy on share.streamlit.io."
    )
    st.info("Free tier allows 3 watermarked exports. Check Pro access for unlimited exports.")


if __name__ == "__main__":
    main()
