document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('id_file');
    const fileLabel = document.getElementById('fileLabel');
    const uploadForm = document.getElementById('uploadForm');

    if (dropZone && fileInput) {
        // Trigger file input click when clicking the zone
        dropZone.addEventListener('click', () => fileInput.click());

        // Highlight drop zone on drag over
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            }, false);
        });

        // Remove highlight on drag leave
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
            }, false);
        });

        // Handle dropped files
        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateFileName(files[0].name);
            }
        });

        // Handle selected files from dialog
        fileInput.addEventListener('change', (e) => {
            if (fileInput.files.length > 0) {
                updateFileName(fileInput.files[0].name);
            }
        });
    }

    function updateFileName(name) {
        if (fileLabel) {
            fileLabel.innerHTML = `<strong>Selected file:</strong> ${name}`;
            fileLabel.style.color = 'var(--primary-color)';
        }
    }
});
