const form = document.getElementById('convertForm');
const result = document.getElementById('result');
const downloadLink = document.getElementById('downloadLink');
const preview = document.getElementById('preview');
const copyBtn = document.getElementById('copyBtn');
const fromSel = document.getElementById('from');
const toSel = document.getElementById('to');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData();
  fd.append('from_type', fromSel.value.toLowerCase());
  fd.append('to_type', toSel.value.toLowerCase());
  fd.append('file', document.getElementById('file').files[0]);

  const res = await fetch('/convert', { method: 'POST', body: fd });
  if (!res.ok) { alert('Conversion failed.'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);

  // After fetch...
const blob = await res.blob();
const url = URL.createObjectURL(blob);

// Guess ext from response headers or selection
const to = toSel.value.toLowerCase();
let ext = (to === 'word') ? 'docx' : (to === 'excel') ? 'xlsx' :
          (to === 'powerpoint') ? 'pptx' : to;

const isZip = res.headers.get('Content-Type')?.includes('zip') || ext === 'zip';
downloadLink.href = url;
downloadLink.download = isZip ? 'converted.zip' : `converted.${ext}`;
result.classList.remove('d-none');

// Only preview/copy if it's a single image (ZIPs & docs → no preview)
const isImage = ['png','jpg','jpeg','webp','gif','tiff'].includes(ext) && !isZip;
if (isImage) {
  preview.src = url;
  preview.classList.remove('d-none');
  copyBtn.classList.remove('d-none');
  copyBtn.onclick = async () => {
    try {
      await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
      copyBtn.textContent = 'Copied!';
      setTimeout(() => copyBtn.textContent = 'Copy image to clipboard', 1500);
    } catch {
      alert('Clipboard copy not supported in this browser.');
    }
  };
} else {
  preview.classList.add('d-none');
  copyBtn.classList.add('d-none');
}


  downloadLink.href = url;
  // filename hint
  const ext = toSel.value.toLowerCase() === 'word' ? 'docx' :
              toSel.value.toLowerCase() === 'excel' ? 'xlsx' :
              toSel.value.toLowerCase();
  downloadLink.download = `converted.${ext}`;
  result.classList.remove('d-none');

  // Preview + copy for images
  const isImage = ['png','jpg','jpeg','webp','gif','tiff'].includes(ext);
  if (isImage) {
    preview.src = url;
    preview.classList.remove('d-none');
    copyBtn.classList.remove('d-none');
    copyBtn.onclick = async () => {
      try {
        await navigator.clipboard.write([
          new ClipboardItem({ [blob.type]: blob })
        ]);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => copyBtn.textContent = 'Copy image to clipboard', 1500);
      } catch {
        alert('Clipboard copy not supported in this browser.');
      }
    };
  } else {
    preview.classList.add('d-none');
    copyBtn.classList.add('d-none');
  }
});
