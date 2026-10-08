/* Public news regression checks. Run: node public_test.js (uses existing jsdom).
   All data stays local; fonts, Firebase and publishers are never contacted. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { JSDOM, VirtualConsole } = require('jsdom');
const html = fs.readFileSync(path.join(__dirname, 'docs', 'index.html'), 'utf8');
const collected = JSON.parse(html.match(/LAST_FETCHED = ("[^"]*"|null)/)[1]);

function boot(storage = 'normal', now = null) {
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM(html, {
    url: 'https://ahmad19sep.github.io/ai-news-updater/',
    runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole,
    beforeParse(w) {
      if (now !== null) w.Date.now = () => now;
      w.fetch = async () => ({ ok: false });
      w.open = () => null;
      w.scrollTo = () => {};
      w.HTMLElement.prototype.scrollIntoView = () => {};
      w.matchMedia = () => ({ matches: false });
      if (storage === 'corrupt') w.localStorage.setItem('air_saved', '{invalid');
      if (storage === 'wrong-type') w.localStorage.setItem('air_saved', '{}');
      if (storage === 'blocked') Object.defineProperty(w, 'localStorage', {
        get() { throw new Error('Storage disabled'); },
      });
    },
  });
  return { dom, w: dom.window, d: dom.window.document, errors };
}

const { dom, w, d, errors } = boot();
const items = w.eval('ITEMS');
const visibleTitles = () => Array.from(d.querySelectorAll('.vtitle'), e => e.textContent);
const input = value => {
  d.getElementById('q').value = value;
  d.getElementById('q').dispatchEvent(new w.Event('input', { bubbles: true }));
};
assert.equal(errors.length, 0, errors.join('\n'));
assert.equal(d.querySelectorAll('.vrow').length, 18);
assert.equal(d.querySelectorAll('main h1').length, 1);
assert.match(d.getElementById('updlabel').textContent, /Last collected/);
assert.match(d.querySelector('.editionnote').textContent, /600 stories/);
assert.equal(d.querySelector('.brand').getAttribute('href'), './');
assert.equal(d.querySelector('a[href="studio.html"]').textContent, 'Newsroom (staff)');
const latest = Array.from(items).sort((a, b) => Date.parse(b.d) - Date.parse(a.d));
assert.equal(visibleTitles()[0], latest[0].t);
console.log('ok - generated feed, publication ordering, collection timestamp and project links');

assert.ok(collected && Number.isFinite(Date.parse(collected)), 'Feed should retain its real collection timestamp');
for (const [age, stale] of [[2, false], [48, true]]) {
  const test = boot('normal', Date.parse(collected) + age * 3600000);
  assert.equal(test.d.getElementById('freshness').classList.contains('stale'), stale);
  assert.equal(test.d.getElementById('updlabel').textContent.includes('older than 24 hours'), stale);
  test.dom.window.close();
}
console.log('ok - collection-age freshness and stale indication');

d.getElementById('more').click();
assert.equal(d.querySelectorAll('.vrow').length, 36);
d.getElementById('fHot').click();
const sortedCounts = w.eval('filtered().map(coverageCount)');
assert.ok(sortedCounts.every((n, i) => i === 0 || n <= sortedCounts[i - 1]));
assert.equal(w.eval('filtered().length'), items.length, 'Coverage view must rank the whole feed');
assert.equal(d.getElementById('fHot').getAttribute('aria-pressed'), 'true');
console.log('ok - pagination and coverage ranking');

d.getElementById('fLatest').click();
const publisher = items[0].s;
input(publisher);
assert.ok(w.eval('filtered().length') > 0, 'Publisher names should be searchable');
assert.ok(w.eval('filtered().every(it => [it.t,it.s,PILLARS[it.p]].join(" ").toLowerCase().includes(q.toLowerCase()))'));
input('no-news-match-8b6435');
assert.equal(d.querySelectorAll('.vrow').length, 0);
assert.ok(!d.getElementById('resetfilters').hidden);
d.querySelector('.empty button').click();
assert.equal(d.querySelectorAll('.vrow').length, 18);
const category = Array.from(d.querySelectorAll('#nav button')).find(b => b.textContent === 'New Tools & Models');
category.click();
assert.ok(w.eval('filtered().every(it => it.p === 1)'));
assert.equal(d.getElementById('feedtitle').textContent, 'New Tools & Models');
d.getElementById('resetfilters').click();
console.log('ok - publisher search, no-result recovery and topic filters');

const savedURL = d.querySelector('.savebtn').dataset.url;
d.querySelector('.savebtn').click();
assert.ok(JSON.parse(w.localStorage.getItem('air_saved')).includes(savedURL));
assert.equal(d.getElementById('savedcount').textContent, '1');
d.getElementById('fSaved').click();
assert.equal(d.querySelectorAll('.vrow').length, 1);
assert.equal(d.querySelector('.savebtn').getAttribute('aria-pressed'), 'true');
d.querySelector('.savebtn').click();
assert.equal(d.querySelectorAll('.vrow').length, 0);
assert.match(d.querySelector('.empty').textContent, /Use Save/);
assert.equal(d.activeElement.id, 'fSaved');
console.log('ok - save, persistence, reading list and remove');

const about = d.querySelector('button[onclick="openPage(\'about\')"]');
about.focus(); about.click();
assert.ok(!d.getElementById('reader').hidden);
assert.equal(d.activeElement.className, 'rback');
assert.equal(d.querySelector('main').inert, true);
d.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true }));
assert.ok(d.getElementById('reader').contains(d.activeElement));
d.dispatchEvent(new w.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
assert.ok(d.getElementById('reader').hidden);
assert.equal(d.activeElement, about);
assert.equal(d.querySelector('main').inert, false);
w.eval('PUBS=[{id:"test/id",title:"Test <script> & feature",cat:"Research Papers",body:"A first paragraph.\\n\\nA second paragraph.",ts:Date.now(),url:"javascript:alert(1)",image:"javascript:alert(1)"}];openArticle(0)');
assert.equal(d.getElementById('reader-title').textContent, 'Test <script> & feature');
assert.equal(d.querySelectorAll('#reader .rbody p').length, 2);
assert.equal(d.querySelectorAll('#reader .srclink').length, 0);
assert.equal(d.querySelectorAll('#reader img').length, 0);
assert.match(w.location.hash, /test%2Fid/);
w.closeArticle();
assert.equal(errors.length, 0, errors.join('\n'));
dom.window.close();
console.log('ok - accessible reader, focus restore, text escaping and invalid link rejection');

for (const storage of ['corrupt', 'wrong-type', 'blocked']) {
  const test = boot(storage);
  assert.equal(test.errors.length, 0, test.errors.join('\n'));
  assert.equal(test.d.querySelectorAll('.vrow').length, 18);
  test.d.querySelector('.savebtn').click();
  test.d.getElementById('fSaved').click();
  assert.equal(test.d.querySelectorAll('.vrow').length, 1);
  if (storage === 'blocked') assert.match(test.d.getElementById('saveannouncement').textContent, /this visit/);
  test.dom.window.close();
}
console.log('ok - corrupted, wrong-type and disabled browser storage');
