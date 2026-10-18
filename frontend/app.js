// Siphon — YouTube Clone Frontend Logic (Vanilla JS)

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search-input");
    const searchBtn = document.getElementById("search-btn");
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
    const streamQualitySelect = document.getElementById("stream-quality-select");
    const loadingOverlay = document.getElementById("loading-overlay");

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

    function formatDuration(seconds) {
        if (!seconds || isNaN(seconds)) return "Unknown";
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        if (h > 0) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
        return `${m}:${s.toString().padStart(2, "0")}`;
    }

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

    function showStatus(message, type = "info") {
        statusBanner.className = `status-banner ${type}`;
        statusText.textContent = message;
        statusBanner.classList.remove("hidden");
    }

    function resetPlayer() {
        videoPlayer.pause();
        videoPlayer.removeAttribute("src");
        videoPlayer.load();
        playerSection.classList.add("hidden");
        playerFallback.classList.add("hidden");
    }

    // Fetch stream URL via our proxy to prevent Qt from blocking it
    async function applyPlayer(url, formatId = "") {
        if (streamQualitySelect) streamQualitySelect.disabled = true;
        showStatus("Loading video stream...", "info");
        
        try {
            const endpoint = formatId 
                ? `/api/stream?url=${encodeURIComponent(url)}&format_id=${formatId}`
                : `/api/stream?url=${encodeURIComponent(url)}`;
                
            const resp = await fetch(endpoint);
            if (!resp.ok) throw new Error("Stream resolution failed");
            
            const data = await resp.json();
            
            if (data.stream_url) {
                // Point the video tag to our local FastAPI proxy
                videoPlayer.src = `/api/proxy?url=${encodeURIComponent(data.stream_url)}`;
                playerFallback.classList.add("hidden");
                playerSection.classList.remove("hidden");
                showStatus(`Streaming in ${data.quality || "Auto"}`, "success");
            } else {
                throw new Error("No stream URL");
            }
        } catch (err) {
            videoPlayer.removeAttribute("src");
            playerFallback.classList.remove("hidden");
            playerSection.classList.remove("hidden");
            showStatus(`Stream Error: ${err.message}`, "error");
        } finally {
            if (streamQualitySelect) streamQualitySelect.disabled = false;
        }
    }

    async function loadVideoInfo(url) {
        currentUrl = url;
        urlInput.value = url;
        
        // 1. Show blurred overlay
        if (loadingOverlay) loadingOverlay.classList.remove("hidden");
        
        mediaPreview.classList.add("hidden");
        formatsContainer.classList.add("hidden");
        resetPlayer();
        
        if (streamQualitySelect) {
            streamQualitySelect.innerHTML = '<option value="">Auto (Default)</option>';
        }
        
        try {
            const resp = await fetch(`/api/info?url=${encodeURIComponent(url)}`);
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || "Failed to inspect video.");

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

            // Populate dropdown with progressive (playable) formats
            if (streamQualitySelect && data.progressive_options && data.progressive_options.length > 0) {
                data.progressive_options.forEach(fmt => {
                    const opt = document.createElement("option");
                    opt.value = fmt.format_id;
                    opt.textContent = `${fmt.quality} (${fmt.ext})`;
                    if (fmt.quality === "480p" || fmt.quality === "360p") {
                        opt.selected = true;
                    }
                    streamQualitySelect.appendChild(opt);
                });
            }

            // Load initial player
            await applyPlayer(url);

            // Render download lists
            renderFormatList(progressiveList, data.progressive_options, "progressive");
            renderFormatList(videoList, data.video_options, "video");
            renderFormatList(audioList, data.audio_options, "audio");

            formatsContainer.classList.remove("hidden");
        } catch (err) {
            showStatus(`Error: ${err.message}`, "error");
        } finally {
            // 2. Hide blurred overlay
            if (loadingOverlay) loadingOverlay.classList.add("hidden");
        }
    }

    async function handleFetchInfo() {
        const url = urlInput.value.trim();
        if (!url) return showStatus("Please enter a valid YouTube URL.", "error");
        await loadVideoInfo(url);
    }

    async function handleSearch() {
        const query = searchInput.value.trim();
        if (!query) return showStatus("Please enter a search query.", "error");

        showStatus(`Searching for “${query}”...`, "info");
        searchBtn.disabled = true;
        const origText = searchBtn.textContent;
        searchBtn.innerHTML = '<span class="btn-spinner"></span> Searching';
        
        try {
            const resp = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=20`);
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || "Search failed.");

            renderSearchResults(data);
            if (data.length === 0) showStatus("No results found.", "info");
            else showStatus(`Found ${data.length} result(s).`, "success");
            
        } catch (err) {
            showStatus(`Search Error: ${err.message}`, "error");
        } finally {
            searchBtn.disabled = false;
            searchBtn.textContent = origText;
        }
    }

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

            const metaContainer = document.createElement("div");
            metaContainer.className = "result-meta-container";

            const uploader = document.createElement("p");
            uploader.className = "result-uploader";
            uploader.textContent = item.uploader || "";

            const date = document.createElement("span");
            date.className = "result-date";
            date.textContent = item.upload_date && item.upload_date !== "Unknown" 
                ? `• ${item.upload_date}` 
                : "";

            metaContainer.appendChild(uploader);
            metaContainer.appendChild(date);

            body.appendChild(title);
            body.appendChild(metaContainer);
            card.appendChild(thumbWrap);
            card.appendChild(body);
            resultsGrid.appendChild(card);
        });

        searchResults.classList.remove("hidden");
    }

    async function handleSelectResult(url) {
        await loadVideoInfo(url);
        mediaPreview.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function renderFormatList(container, formats, type) {
        container.innerHTML = "";
        if (!formats || formats.length === 0) {
            container.innerHTML = '<div class="format-empty">No streams available.</div>';
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

    async function handleDownload(formatId, buttonEl) {
        const outputDir = outputDirInput.value.trim() || "~/Downloads";
        const origText = buttonEl.textContent;

        buttonEl.disabled = true;
        buttonEl.innerHTML = '<span class="btn-spinner"></span> Saving';
        showStatus(`Downloading format ${formatId}... (Muxing if DASH)`, "info");

        try {
            const resp = await fetch("/api/download", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: currentUrl, format_id: formatId, output_dir: outputDir }),
            });

            const data = await resp.json();
            if (!resp.ok) throw new Error(data.detail || "Download failed.");

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

    // --- EVENT LISTENERS ---
    fetchBtn.addEventListener("click", handleFetchInfo);
    urlInput.addEventListener("keydown", (e) => { if (e.key === "Enter") handleFetchInfo(); });
    searchBtn.addEventListener("click", handleSearch);
    searchInput.addEventListener("keydown", (e) => { if (e.key === "Enter") handleSearch(); });
    
    if (streamQualitySelect) {
        streamQualitySelect.addEventListener("change", (e) => {
            if (currentUrl) {
                applyPlayer(currentUrl, e.target.value);
            }
        });
    }
});