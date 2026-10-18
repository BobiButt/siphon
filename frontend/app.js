// Siphon — Modern Frontend Application Logic (Vanilla JS)

document.addEventListener("DOMContentLoaded", () => {
    const urlInput = document.getElementById("url-input");
    const fetchBtn = document.getElementById("fetch-btn");
    const fetchSpinner = document.getElementById("fetch-spinner");
    const outputDirInput = document.getElementById("output-dir-input");

    const statusBanner = document.getElementById("status-banner");
    const statusText = document.getElementById("status-text");

    const mediaPreview = document.getElementById("media-preview");
    const mediaThumb = document.getElementById("media-thumb");
    const mediaTitle = document.getElementById("media-title");
    const mediaUploader = document.getElementById("media-uploader");
    const mediaDuration = document.getElementById("media-duration");

    const formatsContainer = document.getElementById("formats-container");
    const progressiveList = document.getElementById("progressive-list");
    const videoList = document.getElementById("video-list");
    const audioList = document.getElementById("audio-list");

    let currentUrl = "";

    // Helper: format duration in MM:SS or HH:MM:SS
    function formatDuration(seconds) {
        if (!seconds) return "Unknown duration";
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        if (h > 0) {
            return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
        }
        return `${m}:${s.toString().padStart(2, "0")}`;
    }

    // Helper: format bytes into human readable string
    function formatBytes(bytes) {
        if (!bytes || isNaN(bytes)) return "Approx. size";
        const units = ["B", "KB", "MB", "GB"];
        let size = bytes;
        let unitIdx = 0;
        while (size >= 1024 && unitIdx < units.length - 1) {
            size /= 1024;
            unitIdx++;
        }
        return `${size.toFixed(1)} ${units[unitIdx]}`;
    }

    // Helper: show status banner
    function showStatus(message, type = "info") {
        statusBanner.className = `status-banner ${type}`;
        statusText.textContent = message;
        statusBanner.classList.remove("hidden");
    }

    function hideStatus() {
        statusBanner.classList.add("hidden");
    }

    // Fetch video info
    async function handleFetchInfo() {
        const url = urlInput.value.trim();
        if (!url) {
            showStatus("Please enter a valid YouTube URL.", "error");
            return;
        }

        currentUrl = url;
        showStatus("Fetching video stream information...", "info");
        fetchBtn.disabled = true;
        fetchSpinner.classList.remove("hidden");
        mediaPreview.classList.add("hidden");
        formatsContainer.classList.add("hidden");

        try {
            const resp = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.detail || "Failed to inspect video stream.");
            }

            // Render media details
            mediaTitle.textContent = data.title || "Untitled Video";
            mediaUploader.textContent = data.uploader ? `Channel: ${data.uploader}` : "";
            mediaDuration.textContent = formatDuration(data.duration);
            if (data.thumbnail) {
                mediaThumb.src = data.thumbnail;
                mediaThumb.classList.remove("hidden");
            } else {
                mediaThumb.classList.add("hidden");
            }
            mediaPreview.classList.remove("hidden");

            // Render format lists
            renderFormatList(progressiveList, data.progressive_options, "progressive");
            renderFormatList(videoList, data.video_options, "video");
            renderFormatList(audioList, data.audio_options, "audio");

            formatsContainer.classList.remove("hidden");
            showStatus("Stream formats loaded successfully.", "success");
        } catch (err) {
            showStatus(`Error: ${err.message}`, "error");
        } finally {
            fetchBtn.disabled = false;
            fetchSpinner.classList.add("hidden");
        }
    }

    // Render individual format rows
    function renderFormatList(container, formats, type) {
        container.innerHTML = "";

        if (!formats || formats.length === 0) {
            container.innerHTML = '<div class="format-empty">No streams available in this category.</div>';
            return;
        }

        formats.forEach((fmt) => {
            const row = document.createElement("div");
            row.className = "format-row";

            const meta = document.createElement("div");
            meta.className = "format-meta";

            const quality = document.createElement("span");
            quality.className = "format-quality";
            quality.textContent = fmt.quality || fmt.bitrate || "Standard";

            const ext = document.createElement("span");
            ext.className = "format-ext";
            ext.textContent = fmt.ext || "mp4";

            const size = document.createElement("span");
            size.className = "format-size";
            size.textContent = formatBytes(fmt.filesize);

            meta.appendChild(quality);
            meta.appendChild(ext);
            meta.appendChild(size);

            const downloadBtn = document.createElement("button");
            downloadBtn.className = "btn btn-sm";
            downloadBtn.textContent = "Download";
            downloadBtn.addEventListener("click", () => handleDownload(fmt.format_id, downloadBtn));

            row.appendChild(meta);
            row.appendChild(downloadBtn);
            container.appendChild(row);
        });
    }

    // Trigger media download
    async function handleDownload(formatId, buttonEl) {
        const outputDir = outputDirInput.value.trim() || "~/Downloads";
        const origText = buttonEl.textContent;

        buttonEl.disabled = true;
        buttonEl.textContent = "Downloading...";
        showStatus(`Downloading format ${formatId}... (Muxing if DASH stream)`, "info");

        try {
            const resp = await fetch("/api/download", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: currentUrl,
                    format_id: formatId,
                    output_dir: outputDir,
                }),
            });

            const data = await resp.json();
            if (!resp.ok) {
                throw new Error(data.detail || "Download failed.");
            }

            buttonEl.textContent = "Done!";
            showStatus(`Success! File saved to: ${data.output_path}`, "success");

            setTimeout(() => {
                buttonEl.disabled = false;
                buttonEl.textContent = origText;
            }, 3000);
        } catch (err) {
            buttonEl.disabled = false;
            buttonEl.textContent = "Retry";
            showStatus(`Download Error: ${err.message}`, "error");
        }
    }

    // Event listeners
    fetchBtn.addEventListener("click", handleFetchInfo);
    urlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            handleFetchInfo();
        }
    });
});
