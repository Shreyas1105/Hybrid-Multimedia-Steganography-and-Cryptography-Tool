// Project Developed by Shreyas M Shenoy
// Frontend JS — vanilla, clean UX, progress
const fileEl = document.getElementById('file');
const containerSel = document.getElementById('container');
const modeSel = document.getElementById('mode');
const secretField = document.getElementById('secretField');
const preview = document.getElementById('preview');
const statusEl = document.getElementById('status');
const form = document.getElementById('form');
const output = document.getElementById('output');
const progressBar = document.getElementById('progressBar');
const progress = document.getElementById('progress');

function resetUI() {
    preview.innerHTML = 'No file selected';
    output.textContent = '';
    statusEl.textContent = 'Ready';
    progress.style.display = 'none';
    progressBar.style.width = '0%';
}
resetUI();

modeSel.addEventListener('change', () => {
    secretField.style.display = modeSel.value === 'embed' ? 'block' : 'none';
    output.textContent = '';
});

fileEl.addEventListener('change', () => {
    const f = fileEl.files[0];
    preview.innerHTML = '';
    if (!f) { preview.textContent = 'No file selected'; return; }
    const url = URL.createObjectURL(f);
    if (f.type.startsWith('image/')) {
        const img = document.createElement('img'); img.src = url; preview.appendChild(img);
    } else if (f.type.startsWith('audio/')) {
        const a = document.createElement('audio'); a.controls = true; a.src = url; preview.appendChild(a);
    } else if (f.type.startsWith('video/')) {
        const v = document.createElement('video'); v.controls = true; v.src = url; preview.appendChild(v);
    } else {
        preview.textContent = `Selected: ${f.name}`;
    }
});

document.getElementById('reset').addEventListener('click', () => {
    form.reset(); resetUI();
});

// helper to stream progress from server (simple)
async function postFormAndStream(endpoint, formData, onProgress) {
    // use XMLHttpRequest for progress events (upload)
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', endpoint, true);
        xhr.responseType = 'json';
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable && onProgress) {
                onProgress(Math.round((e.loaded / e.total) * 100));
            }
        };
        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(xhr.response);
            } else {
                try { reject(new Error(xhr.response?.detail || xhr.response || xhr.statusText)); }
                catch (e) { reject(new Error('Server error')); }
            }
        };
        xhr.onerror = () => reject(new Error('Network error'));
        xhr.send(formData);
    });
}

form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    output.textContent = ''; statusEl.textContent = 'Processing...';
    progress.style.display = 'block'; progressBar.style.width = '0%';

    const file = fileEl.files[0];
    const container = containerSel.value;
    const mode = modeSel.value;
    const password = document.getElementById('password').value;
    const secret = document.getElementById('secret').value;

    if (!file) { alert('Choose a file'); return; }
    if (!password) { alert('Provide a password'); return; }
    if (mode === 'embed' && !secret) { alert('Provide a secret to embed'); return; }

    const fd = new FormData();
    fd.append('file', file);
    fd.append('password', password);
    fd.append('container', container);
    fd.append('mode', mode);
    if (mode === 'embed') { fd.append('secret_text', secret); }

    try {
        const resp = await postFormAndStream(`/api/process`, fd, (p) => {
            progressBar.style.width = p + '%';
        });

        // For embed, server returns a file blob (but xhr.responseType json cannot return blob).
        // To simplify: server will return JSON with either { download: true, filename: "...", url: "/download/..." }
        if (resp && resp.download && resp.url) {
            const a = document.createElement('a');
            a.href = resp.url;
            a.download = resp.filename;
            a.textContent = `Download ${resp.filename}`;
            output.innerHTML = '';
            output.appendChild(a);
            statusEl.textContent = 'Done — file ready';
            progressBar.style.width = '100%';
        } else if (resp && resp.plaintext !== undefined) {
            output.textContent = `Extracted plaintext:\n\n${resp.plaintext}`;
            statusEl.textContent = 'Done — extracted';
            progressBar.style.width = '100%';
        } else {
            output.textContent = JSON.stringify(resp, null, 2);
            statusEl.textContent = 'Done';
            progressBar.style.width = '100%';
        }
    } catch (err) {
        output.textContent = 'Error: ' + (err.message || err);
        statusEl.textContent = 'Error';
        progress.style.display = 'none';
    }
});
