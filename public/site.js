const progress = document.querySelector('.scroll-progress');
let frame = 0;
function updateProgress() {
  const available = document.documentElement.scrollHeight - innerHeight;
  progress.style.transform = `scaleX(${available > 0 ? Math.min(1, Math.max(0, scrollY / available)) : 0})`;
  frame = 0;
}
function scheduleProgress() { if (!frame) frame = requestAnimationFrame(updateProgress); }
addEventListener('scroll', scheduleProgress, {passive:true});
addEventListener('resize', scheduleProgress, {passive:true});
new ResizeObserver(scheduleProgress).observe(document.body);
updateProgress();

const filters = document.querySelector('.language-filters');
filters.hidden = false;
filters.addEventListener('click', event => {
  const button = event.target.closest('button[data-filter]');
  if (!button) return;
  const selected = button.dataset.filter;
  for (const item of filters.querySelectorAll('button')) item.setAttribute('aria-pressed', String(item===button));
  let visible = 0;
  for (const article of document.querySelectorAll('.world-examples .example')) {
    article.hidden = selected !== 'all' && article.dataset.language !== selected;
    if (!article.hidden) visible++;
  }
  document.querySelector('#filter-status').textContent = document.documentElement.lang==='ja' ? `${visible}件の例文を表示` : `${visible} examples shown`;
});

const dialog = document.querySelector('.specimen-dialog');
const trigger = document.querySelector('[data-specimen]');
trigger.addEventListener('click', event => {
  if (typeof dialog.showModal !== 'function') return;
  event.preventDefault();
  dialog.showModal();
  document.body.classList.add('dialog-open');
});
dialog.querySelector('[data-close-dialog]').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close();});
dialog.addEventListener('close',()=>{document.body.classList.remove('dialog-open');trigger.focus({preventScroll:true});});

// Keep a reader in the same section when changing the page language.
for (const link of document.querySelectorAll('.language-switch a')) {
  link.addEventListener('click',()=>{if(location.hash)link.hash=location.hash;});
}
