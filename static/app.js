// ------- Mime/extension map for accept filters -------
function acceptFor(type) {
  const t = (type || '').toLowerCase();
  switch (t) {
    // Images
    case 'jpg': case 'jpeg': return '.jpg,.jpeg,image/jpeg';
    case 'png':               return '.png,image/png';
    case 'gif':               return '.gif,image/gif';
    case 'webp':              return '.webp,image/webp';
    case 'heic':              return '.heic,image/heif,image/heic';
    case 'bmp':               return '.bmp,image/bmp';
    case 'ico':               return '.ico,image/x-icon';
    case 'tif': case 'tiff':  return '.tif,.tiff,image/tiff';
    case 'avif':              return '.avif,image/avif';
    case 'eps':               return '.eps,application/postscript';
    // Documents
    case 'pdf':               return '.pdf,application/pdf';
    case 'word':              return '.docx,.doc,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword';
    case 'excel':             return '.xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel';
    case 'powerpoint':        return '.pptx,.ppt,application/vnd.openxmlformats-officedocument.presentationml.presentation,application/vnd.ms-powerpoint';
    case 'csv':               return '.csv,text/csv';
    case 'text':              return '.txt,text/plain';
    default:                  return ''; // no filter
  }
}

function toExt(value) {
  const v = (value || '').toLowerCase();
  if (v === 'word') return 'docx';
  if (v === 'excel') return 'xlsx';
  if (v === 'powerpoint') return 'pptx';
  return v;
}

// ------- Progress helpers -------
function setupProgress(ids) {
  const wrap = document.getElementById(ids.wrap);
  const bar  = document.getElementById(ids.bar);
  const text = document.getElementById(ids.text);

  function show() {
    wrap.classList.remove('d-none');
    setDeterminate(0, 'Starting upload…');
  }
  function hide() {
    wrap.classList.add('d-none');
    bar.classList.remove('progress-bar-striped', 'progress-bar-animated');
    bar.style.width = '0%';
    bar.textContent = '0%';
    text.textContent = '';
  }
  function setDeterminate(pct, label) {
    bar.classList.remove('progress-bar-striped', 'progress-bar-animated');
    const clamped = Math.max(0, Math.min(100, Math.round(pct)));
    bar.style.width = `${clamped}%`;
    bar.textContent = `${clamped}%`;
    text.textContent = label || '';
  }
  function setIndeterminate(label) {
    bar.classList.add('progress-bar-striped', 'progress-bar-animated');
    bar.style.width = '100%';
    bar.textContent = '';
    text.textContent = label || 'Processing…';
  }
  return { show, hide, setDeterminate, setIndeterminate };
}

// ------- Generic form handler -------
function wireConverterForm(opts) {
  const form = document.getElementById(opts.formId);
  const fromSel = document.getElementById(opts.fromId);
  const toSel   = document.getElementById(opts.toId);
  const fileInp = document.getElementById(opts.fileId);
  const progress = setupProgress(opts.progressIds);

  // Update file dialog filter when "From" changes (and on load)
  function setAcceptFromSelect() {
    fileInp.setAttribute('accept', acceptFor(fromSel.value));
  }
  fromSel.addEventListener('change', setAcceptFromSelect);
  setAcceptFromSelect(); // initial

  const resultWrap   = document.getElementById(opts.resultIds.wrap);
  const downloadLink = document.getElementById(opts.resultIds.download);
  const previewImg   = opts.resultIds.preview ? document.getElementById(opts.resultIds.preview) : null;
  const copyBtn      = opts.resultIds.copy ? document.getElementById(opts.resultIds.copy) : null;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!fileInp.files.length) { alert('Please choose a file.'); return; }

    const fd = new FormData();
    fd.append('from_type', fromSel.value.toLowerCase());
    fd.append('to_type', toSel.value.toLowerCase());
    fd.append('file', fileInp.files[0]);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/convert');
    xhr.responseType = 'blob';

    progress.show();

    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable) progress.setDeterminate((evt.loaded / evt.total) * 100, 'Uploading…');
      else                       progress.setDeterminate(50, 'Uploading…');
    };
    xhr.upload.onload = () => progress.setIndeterminate('Processing on server…');

    xhr.onerror = () => { progress.hide(); alert('Network error while uploading. Please try again.'); };

    xhr.onreadystatechange = () => {
      if (xhr.readyState !== 4) return;
      progress.hide();

      if (xhr.status < 200 || xhr.status >= 300) {
        try {
          const decoder = new TextDecoder();
          const txt = decoder.decode(xhr.response);
          alert(`Conversion failed.\n${txt || `Status ${xhr.status}`}`);
        } catch {
          alert(`Conversion failed. Status ${xhr.status}`);
        }
        return;
      }

      const blob = xhr.response;
      const url = URL.createObjectURL(blob);
      const to = toSel.value.toLowerCase();
      const ext = toExt(to);

      const contentType = xhr.getResponseHeader('Content-Type') || '';
      const isZip = contentType.includes('zip');

      downloadLink.href = url;
      downloadLink.download = isZip ? 'converted.zip' : `converted.${ext}`;
      resultWrap.classList.remove('d-none');

      if (opts.enablePreview) {
        const isImage = ['png','jpg','jpeg','webp','gif','tif','tiff','bmp','ico','avif'].includes(ext) && !isZip;
        if (isImage && previewImg && copyBtn) {
          previewImg.src = url;
          previewImg.classList.remove('d-none');
          copyBtn.classList.remove('d-none');
          copyBtn.onclick = async () => {
            try {
              await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
              copyBtn.textContent = 'Copied!';
              setTimeout(() => (copyBtn.textContent = 'Copy image to clipboard'), 1500);
            } catch { alert('Clipboard copy not supported in this browser.'); }
          };
        } else if (previewImg && copyBtn) {
          previewImg.classList.add('d-none');
          copyBtn.classList.add('d-none');
        }
      }
    };

    xhr.send(fd);
  });
}

// ------- Wire both forms -------
wireConverterForm({
  formId: 'imageForm',
  fromId: 'imgFrom',
  toId: 'imgTo',
  fileId: 'imgFile',
  enablePreview: true,
  progressIds: { wrap: 'imgProgressWrap', bar: 'imgProgressBar', text: 'imgProgressText' },
  resultIds: { wrap: 'imgResult', download: 'imgDownloadLink', preview: 'imgPreview', copy: 'imgCopyBtn' }
});

wireConverterForm({
  formId: 'docForm',
  fromId: 'docFrom',
  toId: 'docTo',
  fileId: 'docFile',
  enablePreview: false,
  progressIds: { wrap: 'docProgressWrap', bar: 'docProgressBar', text: 'docProgressText' },
  resultIds: { wrap: 'docResult', download: 'docDownloadLink' }
});
