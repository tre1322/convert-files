const form = document.getElementById('convertForm');
const result = document.getElementById('result');
const downloadLink = document.getElementById('downloadLink');
const preview = document.getElementById('preview');
const copyBtn = document.getElementById('copyBtn');
const fromSel = document.getElementById('from');
const toSel = document.getElementById('to');

const progressWrap = document.getElementById('progressWrap');
const progressBar  = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');

function showProgress() {
  progressWrap.classList.remove('d-none');
  setDeterminate(0, 'Starting upload…');
}

function hideProgress() {
  progressWrap.classList.add('d-none');
  // reset visuals for next time
  progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
  progressBar.style.width = '0%';
  progressBar.textContent = '0%';
  progressText.textContent = '';
}

function setDeterminate(pct, label) {
  progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
  const clamped = Math.max(0, Math.min(100, Math.round(pct)));
  progressBar.style.width = `${clamped}%`;
  progressBar.textContent = `${clamped}%`;
  progressText.textContent = label || '';
}

function setIndeterminate(label) {
  // Show a busy/processing state
  progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
  progressBar.style.width = '100%';
  progressBar.textContent = '';
  progressText.textContent = label || 'Processing…';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const fileInput = document.getElementById('file');
  if (!fileInput.files.length) {
    alert('Please choose a file.');
    return;
  }

  // Prepare form data
  const fd = new FormData();
  fd.append('from_type', fromSel.value.toLowerCase());
  fd.append('to_type', toSel.value.toLowerCase());
  fd.append('file', fileInput.files[0]);

  // Use XHR for upload progress
  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/convert');
  xhr.responseType = 'blob';

  showProgress();

  // Upload progress (bytes sent to server)
  xhr.upload.onprogress = (evt) => {
    if (evt.lengthComputable) {
      const pct = (evt.loaded / evt.total) * 100;
      setDeterminate(pct, 'Uploading…');
    } else {
      // Fallback if total size unknown
      setDeterminate(50, 'Uploading…');
    }
  };

  // When upload finishes and server starts processing, switch to indeterminate
  xhr.upload.onload = () => {
    setIndeterminate('Processing on server…');
  };

  xhr.onerror = () => {
    hideProgress();
    alert('Network error while uploading. Please try again.');
  };

  xhr.onreadystatechange = () => {
    if (xhr.readyState !== 4) return; // wait for DONE

    hideProgress();

    if (xhr.status < 200 || xhr.status >= 300) {
      // Try to extract any error text
      try {
        const decoder = new TextDecoder();
        const text = decoder.decode(xhr.response);
        alert(`Conversion failed.\n${text || `Status ${xhr.status}`}`);
      } catch {
        alert(`Conversion failed. Status ${xhr.status}`);
      }
      return;
    }

    const outBlob = xhr.response;
    const objectUrl = URL.createObjectURL(outBlob);

    const to = toSel.value.toLowerCase();
    let ext = (to === 'word') ? 'docx'
            : (to === 'excel') ? 'xlsx'
            : (to === 'powerpoint') ? 'pptx'
            : to;

    const contentType = xhr.getResponseHeader('Content-Type') || '';
    const isZip = contentType.includes('zip');

    downloadLink.href = objectUrl;
    downloadLink.download = isZip ? 'converted.zip' : `converted.${ext}`;
    result.classList.remove('d-none');

    const isImage = ['png','jpg','jpeg','webp','gif','tif','tiff'].includes(ext) && !isZip;
    if (isImage) {
      preview.src = objectUrl;
      preview.classList.remove('d-none');
      copyBtn.classList.remove('d-none');
      copyBtn.onclick = async () => {
        try {
          await navigator.clipboard.write([new ClipboardItem({ [outBlob.type]: outBlob })]);
          copyBtn.textContent = 'Copied!';
          setTimeout(() => (copyBtn.textContent = 'Copy image to clipboard'), 1500);
        } catch {
          alert('Clipboard copy not supported in this browser.');
        }
      };
    } else {
      preview.classList.add('d-none');
      copyBtn.classList.add('d-none');
    }
  };

  xhr.send(fd);
});
