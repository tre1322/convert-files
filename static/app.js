// ---------- accept filters ----------
function acceptForGroup(group) {
  if (group === 'image') {
    return [
      '.png','.jpg','.jpeg','.tif','.tiff','.gif','.webp','.heic','.bmp','.ico','.avif','.pdf'
    ].join(',');
  }
  return ['.pdf','.docx','.doc','.xlsx','.xls','.pptx','.ppt','.csv','.txt'].join(',');
}

function toExt(v) {
  v = (v || '').toLowerCase();
  if (v === 'word') return 'docx';
  if (v === 'excel') return 'xlsx';
  if (v === 'powerpoint') return 'pptx';
  return v;
}

// ---------- progress ----------
function setupProgress(ids) {
  const wrap = document.getElementById(ids.wrap);
  const bar  = document.getElementById(ids.bar);
  const text = document.getElementById(ids.text);
  function show(){ wrap.classList.remove('d-none'); setDeterminate(0,'Starting upload…'); }
  function hide(){ wrap.classList.add('d-none'); bar.classList.remove('progress-bar-striped','progress-bar-animated'); bar.style.width='0%'; bar.textContent='0%'; text.textContent=''; }
  function setDeterminate(p,label){ bar.classList.remove('progress-bar-striped','progress-bar-animated'); const p2=Math.max(0,Math.min(100,Math.round(p))); bar.style.width=`${p2}%`; bar.textContent=`${p2}%`; text.textContent=label||''; }
  function setIndeterminate(label){ bar.classList.add('progress-bar-striped','progress-bar-animated'); bar.style.width='100%'; bar.textContent=''; text.textContent=label||'Processing…'; }
  return { show, hide, setDeterminate, setIndeterminate };
}

// ---------- dropzone wiring ----------
function wireDropzone({zoneId, browseId, inputId, pickedId, accept}) {
  const zone   = document.getElementById(zoneId);
  const browse = document.getElementById(browseId);
  const input  = document.getElementById(inputId);
  const picked = document.getElementById(pickedId);

  input.setAttribute('accept', accept);

  // click to browse
  const openDialog = () => input.click();
  zone.addEventListener('click', openDialog);
  browse.addEventListener('click', (e)=>{ e.stopPropagation(); openDialog(); });

  // show selected filename
  function showPicked() {
    if (input.files && input.files[0]) {
      picked.textContent = `${input.files[0].name} (${Math.round(input.files[0].size/1024)} KB)`;
      picked.classList.remove('d-none');
    }
  }
  input.addEventListener('change', showPicked);

  // drag & drop
  zone.addEventListener('dragover', (e)=>{ e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', ()=> zone.classList.remove('dragover'));
  zone.addEventListener('drop', (e)=>{
    e.preventDefault(); zone.classList.remove('dragover');
    if (!e.dataTransfer.files.length) return;
    const dt = new DataTransfer();
    dt.items.add(e.dataTransfer.files[0]);
    input.files = dt.files;
    showPicked();
  });
}

// ---------- submit handler (server infers from_type) ----------
function wireConverterForm(opts) {
  const form = document.getElementById(opts.formId);
  const toSel = document.getElementById(opts.toId);
  const fileInp = document.getElementById(opts.fileId);
  const progress = setupProgress(opts.progressIds);

  const resultWrap = document.getElementById(opts.resultIds.wrap);
  const downloadLink = document.getElementById(opts.resultIds.download);
  const previewImg = opts.resultIds.preview ? document.getElementById(opts.resultIds.preview) : null;
  const copyBtn = opts.resultIds.copy ? document.getElementById(opts.resultIds.copy) : null;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!fileInp.files.length) { alert('Please choose or drop a file.'); return; }

    const fd = new FormData();
    fd.append('to_type', toSel.value.toLowerCase()); // backend infers from_type
    fd.append('file', fileInp.files[0]);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/convert');
    xhr.responseType = 'blob';

    progress.show();
    xhr.upload.onprogress = (evt) => {
      if (evt.lengthComputable) progress.setDeterminate((evt.loaded/evt.total)*100, 'Uploading…');
      else progress.setDeterminate(50, 'Uploading…');
    };
    xhr.upload.onload = () => progress.setIndeterminate('Processing on server…');
    xhr.onerror = () => { progress.hide(); alert('Network error while uploading.'); };

    xhr.onreadystatechange = () => {
      if (xhr.readyState !== 4) return;
      progress.hide();

      if (xhr.status < 200 || xhr.status >= 300) {
        try {
          const txt = new TextDecoder().decode(xhr.response);
          alert(`Conversion failed.\n${txt || `Status ${xhr.status}`}`);
        } catch { alert(`Conversion failed. Status ${xhr.status}`); }
        return;
      }

      const blob = xhr.response;
      const url = URL.createObjectURL(blob);
      const ext = toExt(toSel.value);
      const isZip = (xhr.getResponseHeader('Content-Type') || '').includes('zip');

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

// ----- wire everything -----
wireDropzone({ zoneId:'imgDrop',  browseId:'imgBrowse',  inputId:'imgFile',  pickedId:'imgPicked', accept:acceptForGroup('image') });
wireDropzone({ zoneId:'docDrop',  browseId:'docBrowse',  inputId:'docFile',  pickedId:'docPicked', accept:acceptForGroup('doc') });

wireConverterForm({
  formId: 'imageForm',
  toId: 'imgTo',
  fileId: 'imgFile',
  enablePreview: true,
  progressIds: { wrap: 'imgProgressWrap', bar: 'imgProgressBar', text: 'imgProgressText' },
  resultIds: { wrap: 'imgResult', download: 'imgDownloadLink', preview: 'imgPreview', copy: 'imgCopyBtn' }
});
wireConverterForm({
  formId: 'docForm',
  toId: 'docTo',
  fileId: 'docFile',
  enablePreview: false,
  progressIds: { wrap: 'docProgressWrap', bar: 'docProgressBar', text: 'docProgressText' },
  resultIds: { wrap: 'docResult', download: 'docDownloadLink' }
});
