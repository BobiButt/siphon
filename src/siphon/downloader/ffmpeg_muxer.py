"""FFmpeg stream muxer utilizing bundled static FFmpeg binary."""

import os
from pathlib import Path
import subprocess
from typing import Optional, Union


class MuxingError(Exception):
    """Raised when FFmpeg muxing process fails."""
    pass


def mux_streams(
    video_path: Union[str, Path],
    audio_path: Union[str, Path],
    output_path: Union[str, Path],
    ffmpeg_bin: Union[str, Path] = "assets/ffmpeg/ffmpeg",
    cleanup_sources: bool = True,
) -> Path:
    """Mux separate video and audio streams into a single media file.

    Invokes the bundled static FFmpeg binary using stream copying (-c:v copy)
    and audio re-encoding/copying (-c:a aac) for rapid, lossless video muxing.

    Args:
        video_path: Path to the video stream file.
        audio_path: Path to the audio stream file.
        output_path: Target path for the muxed media file.
        ffmpeg_bin: Path to the static FFmpeg binary (defaults to 'assets/ffmpeg/ffmpeg').
        cleanup_sources: Whether to delete the source video and audio files upon success.

    Returns:
        Path object pointing to the output muxed file.

    Raises:
        MuxingError: If the FFmpeg process exits with a non-zero return code.
    """
    v_path = Path(video_path)
    a_path = Path(audio_path)
    out_path = Path(output_path)

    # Ensure parent output directory exists if output_path has a parent directory
    if out_path.parent and str(out_path.parent) != ".":
        out_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(ffmpeg_bin),
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
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

    # Cleanup temporary source files on success
    if cleanup_sources:
        try:
            if v_path.exists():
                v_path.unlink()
        except OSError:
            pass

        try:
            if a_path.exists():
                a_path.unlink()
        except OSError:
            pass

    return out_path
