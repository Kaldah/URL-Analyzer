const form = document.getElementById("analyzeForm");
const urlInput = document.getElementById("urlInput");
const resultEl = document.getElementById("result");
const messages = document.getElementById("messages");
const submitBtn = document.getElementById("submitBtn");
let lastSubmittedUrl = null;

function showMessage(text, type = 'info'){
  messages.innerHTML = `<div class="msg ${type}">${text}</div>`;
}

function clearMessage(){ messages.innerHTML = '' }

function renderResult(data){
  if(!data) return;
  // If server returned an error field
  if(data.error){
    showMessage(data.error, 'error');
    resultEl.innerHTML = '';
    return;
  }

  const url = data.url || data.input || urlInput.value;
  const malicious = data.malicious_votes ?? data.malicious ?? 0;
  const harmless = data.harmless_votes ?? data.harmless ?? 0;
  const score = data.score ?? null;

  const badges = [];
  if(Number(malicious) === 0 && Number(harmless) === 0){
    badges.push(`<span class="badge neutral">No votes yet</span>`);
  } else if(Number(malicious) > Number(harmless)) {
    badges.push(`<span class="badge malicious">Malicious: ${malicious}</span>`);
  } else {
    badges.push(`<span class="badge harmless">Harmless: ${harmless}</span>`);
  }

  resultEl.innerHTML = `
    <div class="card">
      <h3>${escapeHtml(url)}</h3>
      ${score !== null ? `<p>Score: <strong>${escapeHtml(String(score))}</strong></p>` : ''}
      <p>Malicious votes: <strong>${escapeHtml(String(malicious))}</strong> — Harmless votes: <strong>${escapeHtml(String(harmless))}</strong></p>
      <div class="badges">${badges.join('')}</div>
    </div>
  `;
}

function escapeHtml(s){ return String(s).replace(/[&<>"']/g, (c)=> ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"})[c]) }

async function handleSubmit(e){
  e.preventDefault();
  clearMessage();
  resultEl.innerHTML = '';

  let url = urlInput.value.trim();
  if(!url){ showMessage('Please enter a URL to analyze.', 'error'); return }

  // Normalize: if scheme missing, prepend http:// to avoid backend errors
  // Accepts inputs like example.com, www.example.com, example.com/path
  if(!/^https?:\/\//i.test(url)){
    url = 'http://' + url;
  }

  // show loader
  const loader = document.createElement('div'); loader.className = 'loader';
  submitBtn.disabled = true; submitBtn.appendChild(loader);

  try{
    lastSubmittedUrl = url; // remember for retry
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ url })
    });

    // Pending: VirusTotal still processing
    if(res.status === 202){
      const detail = await res.text().catch(()=>null);
      showPending(detail);
      return;
    }

    if(!res.ok){
      await handleHttpError(res);
      return;
    }

    const data = await res.json().catch(()=>null);
    if(!data) { showMessage('Invalid JSON response from server', 'error'); return }

    renderResult(data);
    showMessage('Analysis complete.', 'success');
  }catch(err){
    console.error(err);
    showMessage(err.message || 'An unexpected error occurred', 'error');
  }finally{
    // remove loader and re-enable
    const l = submitBtn.querySelector('.loader'); if(l) l.remove();
    submitBtn.disabled = false;
  }
}

form.addEventListener('submit', handleSubmit);

function showPending(detailText){
  const text = typeof detailText === 'string' && detailText.trim() ? detailText : 'Analysis pending at VirusTotal. Try again in a few seconds.';
  messages.innerHTML = `
    <div class="msg info">
      ${escapeHtml(text)}
      <button id="retryBtn" class="retry">Retry</button>
    </div>
  `;
  const retryBtn = document.getElementById('retryBtn');
  if(retryBtn){
    retryBtn.addEventListener('click', async ()=>{
      // Trigger another submission with the same URL
      if(lastSubmittedUrl) urlInput.value = lastSubmittedUrl;
      // Simulate submit
      const ev = new Event('submit');
      form.dispatchEvent(ev);
    });
  }
}

async function handleHttpError(res){
  const status = res.status;
  let msg = `Server returned ${status}`;
  // Try to extract detail
  try{
    const maybeJson = await res.json();
    if(maybeJson && (maybeJson.detail || maybeJson.message)){
      msg = maybeJson.detail || maybeJson.message;
    }
  }catch{
    const text = await res.text().catch(()=>null);
    if(text) msg = text;
  }

  if(status === 404){
    showMessage('No analysis data available yet. Please try again later.', 'info');
  } else if(status === 500){
    showMessage('Server configuration error (missing or invalid API key). Contact admin.', 'error');
  } else if(status === 502){
    showMessage('Upstream request failed (network/VirusTotal). Please retry.', 'error');
  } else {
    showMessage(msg, 'error');
  }
}
