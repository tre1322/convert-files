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
  const fileInput = document.getElementById('file');
  if (!fileInput.files.length) {
    alert('Please choose a file.');
    return;
  }
  fd.append('file', fileInput.files[0]);

  const res = await fetch('/convert', { method: 'POST', body: fd });
  if (!res.ok) {
    const msg = await res.text().catch(() => '');
    alert(`Conversion failed.\n${msg}`);
    return;
  }

  // Use a single variable name to avoid redeclaration
  const outBlob = await res.blob();
  const objectUrl = URL.createObjectURL(outBlob);

  // Infer extension from selection
  const to = toSel.value.toLowerCase();
  let ext = (to === 'word') ? 'docx' :
            (to === 'excel') ? 'xlsx' :
            (to === 'powerpoint') ? 'pptx' :
            to;

  const isZip = (res.headers.get('Content-Type') || '').includes('zip');

  downloadLink.href = objectUrl;
  downloadLink.download = isZip ? 'converted.zip' : `converted.${ext}`;
  result.classList.remove('d-none');

  // Only preview/copy if it's a single image (not zip/docs/pdf)
  const isImage = ['png','jpg','jpeg','webp','gif','tiff'].includes(ext) && !isZip;
  if (isImage) {
    preview.src = objectUrl;
    preview.classList.remove('d-none');
    copyBtn.classList.remove('d-none');
    copyBtn.onclick = async () => {
      try {
        await navigator.clipboard.write([
          new ClipboardItem({ [outBlob.type]: outBlob })
        ]);
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
});
