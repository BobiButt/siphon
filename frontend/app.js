// Siphon — YouTube Clone Frontend Logic (Vanilla JS)

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search-input");
    const searchBtn = document.getElementById("search-btn");
    const searchSpinner = document.getElementById("search-spinner");
    const urlInput = document.getElementById("url-input");
    const fetchBtn = document.getElementById("fetch-btn");
    const outputDirInput = document.getElementById("output-dir-input");

    const statusBanner = document.getElementById("status-banner");
    const statusText = document.getElementById("status-text");

    const searchResults = document.getElementById("search-results");
    const resultsGrid = document.getElementById("results-grid");
    const resultsCount = document.getElementById("results-count");

    const playerSection = document.getElementById("player-section");
    const videoPlayer = document.getElementById("video-player");
    const playerFallback = document.getElementById("player-fallback");

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
        if (!seconds || isNaN(seconds)) return "Unknown";
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

    // Reset the video player to a hidden, empty state
    function resetPlayer() {
        videoPlayer.pause();
        videoPlayer.removeAttribute("src");
        videoPlayer.load();
        playerSection.classList.add("hidden");
        playerFallback.classList.add("hidden");
    }

    // Configure the player from an /api/info response (uses its stream_url)
    function applyPlayer(data) {
        if (data.stream_url) {
            videoPlayer.src = data.stream_url;
            playerFallback.classList.add("hidden");
            playerSection.classList.remove("hidden");
        } else {
            // No progressive/muxed stream available for direct playback.
            videoPlayer.removeAttribute("src");
            playerFallback.classList.remove("hidden");
            playerSection.classList.remove("hidden");
        }
    }

    // Load video info for a URL and render metadata, player, and formats.
    // Shared by the direct-URL Fetch button and search-result clicks.
    async function loadVideoInfo(url) {
        currentUrl = url;
        urlInput.value = url;
        showStatus("Fetching video stream information...", "info");
        mediaPreview.classList.add("hidden");
        formatsContainer.classList.add("hidden");
        resetPlayer();

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

        // Configure HTML5 player (progressive/muxed stream only)
        applyPlayer(data);

        // Render format lists
        renderFormatList(progressiveList, data.progressive_options, "progressive");
        renderFormatList(videoList, data.video_options, "video");
        renderFormatList(audioList, data.audio_options, "audio");

        formatsContainer.classList.remove("hidden");
        showStatus("Stream formats loaded successfully.", "success");
    }

    // Fetch video info from the direct URL input
    async function handleFetchInfo() {
        const url = urlInput.value.trim();
        if (!url) {
            showStatus("Please enter a valid YouTube URL.", "error");
            return;
        }

        fetchBtn.disabled = true;
        try {
            await loadVideoInfo(url);
        } catch (err) {
            showStatus(`Error: ${err.message}`, "error");
        } finally {
            fetchBtn.disabled = false;
        }
    }

    // Perform a YouTube search and render the results grid
    async function handleSearch() {
        const query = searchInput.value.trim();
        if (!query) {
            showStatus("Please enter a search query.", "error");
            return;
        }

        showStatus(`Searching for “${query}”...`, "info");
        searchBtn.disabled = true;
        searchSpinner.classList.remove("hidden");

        try {
            const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.detail || "Search failed.");
            }

            renderSearchResults(data);
            if (data.length === 0) {
                showStatus("No results found.", "info");
            } else {
                showStatus(`Found ${data.length} result(s).`, "success");
            }
        } catch (err) {
            showStatus(`Search Error: ${err.message}`, "error");
        } finally {
            searchBtn.disabled = false;
            searchSpinner.classList.add("hidden");
        }
    }

    // Render the search results grid
    function renderSearchResults(results) {
        resultsGrid.innerHTML = "";
        resultsCount.textContent = results.length ? `${results.length} results` : "";

        if (!results || results.length === 0) {
            searchResults.classList.add("hidden");
            return;
        }

        results.forEach((item) => {
            const card = document.createElement("div");
            card.className = "result-card";
            card.addEventListener("click", () => handleSelectResult(item.url));

            const thumbWrap = document.createElement("div");
            thumbWrap.className = "result-thumb-wrap";
            if (item.thumbnail) {
                const img = document.createElement("img");
                img.className = "result-thumb";
                img.src = item.thumbnail;
                img.alt = item.title || "Thumbnail";
                thumbWrap.appendChild(img);
            }
            const durBadge = document.createElement("span");
            durBadge.className = "result-duration";
            durBadge.textContent = formatDuration(item.duration);
            thumbWrap.appendChild(durBadge);

            const body = document.createElement("div");
            body.className = "result-body";

            const title = document.createElement("h3");
            title.className = "result-title";
            title.textContent = item.title || "Untitled";

            const uploader = document.createElement("p");
            uploader.className = "result-uploader";
            uploader.textContent = item.uploader || "";

            body.appendChild(title);
            body.appendChild(uploader);

            card.appendChild(thumbWrap);
            card.appendChild(body);
            resultsGrid.appendChild(card);
        });

        searchResults.classList.remove("hidden");
    }

    // Handle clicking a search result: load its full info
    async function handleSelectResult(url) {
        try {
            await loadVideoInfo(url);
            mediaPreview.scrollIntoView({ behavior: "smooth", block: "start" });
        } catch (err) {
            showStatus(`Error: ${err.message}`, "error");
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

    searchBtn.addEventListener("click", handleSearch);
    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            handleSearch();
        }
    });
});
