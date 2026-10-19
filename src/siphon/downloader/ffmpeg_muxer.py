"""FFmpeg stream muxer utilizing bundled static FFmpeg binary."""

import logging
import os
import sys
from pathlib import Path
import subprocess
from typing import Optional, Union

logger = logging.getLogger(__name__)


def get_base_path() -> Path:
    """Get the base path whether running from source or PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    # src/siphon/downloader/ffmpeg_muxer.py -> parents[3] is repo root
    return Path(__file__).resolve().parents[3]


# Default location of the bundled static FFmpeg binary
DEFAULT_FFMPEG_PATH = get_base_path() / "assets" / "ffmpeg" / "ffmpeg"


class MuxingError(Exception):
    """Raised when FFmpeg muxing process fails."""
    pass


def resolve_ffmpeg_path(ffmpeg_bin: Union[str, Path] = None) -> Path:
    """Resolve the FFmpeg binary path, expanding ``~`` and env variables."""
    if ffmpeg_bin is None:
        return DEFAULT_FFMPEG_PATH
    return Path(os.path.expandvars(os.path.expanduser(str(ffmpeg_bin))))


def ffmpeg_available(ffmpeg_bin: Union[str, Path] = None) -> bool:
    """Return True when the bundled static FFmpeg binary exists and is executable."""
    path = resolve_ffmpeg_path(ffmpeg_bin)
    return path.is_file() and os.access(path, os.X_OK)


def check_ffmpeg_or_warn(ffmpeg_bin: Union[str, Path] = None) -> bool:
    """Log a clear warning if the bundled FFmpeg binary is missing."""
    if ffmpeg_available(ffmpeg_bin):
        return True

    logger.warning(
        "Bundled FFmpeg not found at '%s'. DASH high-resolution downloads that require "
        "muxing will fail. Run scripts/fetch_ffmpeg.sh to download the pinned static binary.",
        resolve_ffmpeg_path(ffmpeg_bin),
    )
    return False


def mux_streams(
    video_path: Union[str, Path],
    audio_path: Union[str, Path],
    output_path: Union[str, Path],
    ffmpeg_bin: Union[str, Path] = None,
    cleanup_sources: bool = True,
) -> Path:
    """Mux separate video and audio streams into a single media file."""
    v_path = Path(video_path)
    a_path = Path(audio_path)
    out_path = Path(output_path)

    if ffmpeg_bin is None:
        ffmpeg_bin = DEFAULT_FFMPEG_PATH

    if out_path.parent and str(out_path.parent) != ".":
        out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(ffmpeg_bin),
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        str(output_path),
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise MuxingError(
            f"FFmpeg binary not found at '{ffmpeg_bin}'. Run scripts/fetch_ffmpeg.sh to download it."
        ) from exc
    except Exception as exc:
        raise MuxingError(f"Unexpected error running FFmpeg: {exc}") from exc

    if proc.returncode != 0:
        error_msg = proc.stderr.strip() if proc.stderr else f"Exit code {proc.returncode}"
        raise MuxingError(f"FFmpeg muxing failed (exit {proc.returncode}): {error_msg}")

    if cleanup_sources:
        try:
            if v_path.exists(): v_path.unlink()
            if a_path.exists(): a_path.unlink()
        except OSError:
            pass

    return out_path