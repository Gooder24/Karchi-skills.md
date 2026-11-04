// Prehľad dvora: renders api/data. Colour = project family, pixel icon = machine.
const $ = s => document.querySelector(s)
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])

// 11×11 pixel glyphs, one string per row.
const ICONS = {
  x270: ['           ', ' ######### ', ' #.......# ', ' #..#.#..# ', ' #...#...# ', ' #.......# ', ' ######### ', '###########', '#.........#', '###########', '           '],
  asus: ['           ', ' ######### ', ' #...#...# ', ' #..##...# ', ' #.#####.# ', ' #...##..# ', ' ####x#### ', '###########', '#.........#', '###########', '           '],
  dell: ['           ', ' ######### ', ' #..###..# ', ' #.#.#.#.# ', ' #.#####.# ', ' #..###..# ', ' ######### ', '###########', '#.........#', '###########', '           '],
  e540: ['           ', ' ######### ', ' #.......# ', ' #.#####.# ', ' #.#...#.# ', ' #.#####.# ', ' ######### ', '###########', '#.........#', '###########', '           '],
  vps: ['           ', '           ', '    ###    ', '  ##...##  ', ' #.......# ', '##.......##', '#.........#', '#.........#', ' ######### ', '           ', '           '],
}
const DEVICE_NAMES = { x270: 'x270', asus: 'asus', dell: 'dell', e540: 'e540', vps: 'vps' }

function icon(device) {
  const g = ICONS[device]
  if (!g) return ''
  let rects = ''
  g.forEach((row, y) => [...row].forEach((ch, x) => { if (ch === '#' || ch === 'x') rects += `<rect x="${x}" y="${y}" width="1" height="1"/>` }))
  return `<svg class="pix" viewBox="0 0 11 11" aria-hidden="true">${rects}</svg>`
}

let state = { data: null, off: { rodiny: new Set(), stroje: new Set() }, strana: 'vsetko' }

function proj(id) {
  const f = state.data.farby
  const p = f.projekty[id] || f.projekty.stroje
  const r = f.rodiny[p.rodina] || f.rodiny.stroje
  return { ...p, id: id || 'stroje', farba: r.farba, rodinaNazov: r.nazov }
}

const visible = (device, projectId) => !state.off.stroje.has(device) && !state.off.rodiny.has(proj(projectId).rodina)

const DAY = new Intl.DateTimeFormat('sk-SK', { weekday: 'long', day: 'numeric', month: 'numeric', timeZone: 'Europe/Bratislava' })
const HM = new Intl.DateTimeFormat('sk-SK', { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Bratislava' })
const dayKey = d => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Bratislava' }).format(d)

function dayLabel(d, now) {
  const k = dayKey(d)
  if (k === dayKey(now)) return 'Dnes'
  if (k === dayKey(new Date(now.getTime() + 864e5))) return 'Zajtra'
  return DAY.format(d)
}

function rowHtml({ time, project, title, sub, device, problem }) {
  const p = proj(project)
  return `<div class="row${problem ? ' problem' : ''}" style="--c:${p.farba}">
    <span class="bar" title="${esc(p.rodinaNazov)}"></span>
    <time>${esc(time || '')}</time>
    <span class="mono-cell"><span class="mono" title="${esc(p.nazov)}">${esc(p.znak)}</span></span>
    <span class="what"><b>${esc(title)}</b><span class="sub">${sub}</span></span>
    <span class="where">${icon(device)}${esc(DEVICE_NAMES[device] || device)}</span>
  </div>`
}

function aiText(r) {
  if (r.ai === 'áno') return `AI: ${esc(r.predplatne)}${r.model && r.model !== '—' ? ', ' + esc(r.model) : ''}`
  if (r.ai === 'spúšťa') return `spúšťa AI na ${esc(r.predplatne)}`
  if (r.ai === '?') return '<span class="flag">nezaradené: neviem, čo robí a kto platí</span>'
  return 'bez AI'
}

function renderRozpis() {
  const d = state.data, now = new Date(d.teraz)
  const items = []
  // Waiting on Karchi: manual updates and leftovers the inventory flags.
  const manual = d.aktualizacie.filter(u => u.stav === 'treba ručne' && visible(u.zariadenie, u.projekt))
  const flagged = d.procesy.filter(r => r.chaos && visible(r.zariadenie, r.projekt))
  let html = ''
  if (manual.length || flagged.length) {
    html += `<p class="group-title">Treba ručne</p>`
    for (const u of manual) {
      const sub = u.caka != null ? `${u.caka} ${u.caka === 1 ? 'balík čaká' : u.caka < 5 ? 'balíky čakajú' : 'balíkov čaká'}${u.posledne ? `, naposledy ${esc(u.posledne)}` : ''}, nič ich neinštaluje samo`
        : `máš ${esc(u.ma)}, vyšlo ${esc(u.najnovsie)}${u.vydane ? ` (${esc(u.vydane)})` : ''}`
      html += rowHtml({ time: 'update', project: u.projekt, title: `Aktualizovať ${u.nazov}`, sub, device: u.zariadenie, problem: true })
    }
    for (const r of flagged)
      html += rowHtml({ time: '', project: r.projekt, title: r.nazov, sub: `<span class="flag">${esc(r.chaos)}</span>, ${esc(r.na_co)}`, device: r.zariadenie, problem: true })
  }
  for (const r of d.procesy)
    if (r.dalsi && r.stav !== 'vypnuté' && visible(r.zariadenie, r.projekt))
      items.push({ at: new Date(r.dalsi), project: r.projekt, title: r.nazov, device: r.zariadenie, sub: `${esc(r.kedy)}. ${esc(r.na_co)}. ${aiText(r)}` })
  for (const u of d.aktualizacie)
    if (u.dalsi && u.caka && visible(u.zariadenie, u.projekt))
      items.push({ at: new Date(u.dalsi), project: u.projekt, title: `Aktualizácia ${u.nazov}`, device: u.zariadenie, sub: `${u.caka} ${u.caka < 5 ? 'balíky' : 'balíkov'}, nainštaluje automatika` })
  items.sort((a, b) => a.at - b.at)
  let last = ''
  for (const it of items) {
    const label = dayLabel(it.at, now)
    if (label !== last) { html += `<p class="group-title">${esc(label[0].toUpperCase() + label.slice(1))}</p>`; last = label }
    html += rowHtml({ ...it, time: HM.format(it.at) })
  }
  $('#rozpis').innerHTML = html || '<p class="hint">Nič nenaplánované pre zvolené filtre.</p>'
}

// What waits on Karchi, company and personal in one list. Live asks first, then the inbox.
const SOURCE = { rerun: 'R', t3: 'T3' }
const STRANY = [['vsetko', 'Všetko'], ['firma', 'Firma'], ['osobne', 'Osobné']]

const DM = new Intl.DateTimeFormat('sk-SK', { day: 'numeric', month: 'numeric', timeZone: 'Europe/Bratislava' })

function cakaRow(r) {
  const firma = state.data.farby.rodiny.esyst.farba
  const at = r.zdroj === 'inbox' ? new Date(r.kedy + 'T12:00:00') : new Date(r.kedy)
  const when = r.zdroj !== 'inbox' && dayKey(at) === dayKey(new Date()) ? HM.format(at) : DM.format(at)
  const device = r.zdroj === 'inbox' ? '' : r.zdroj === 'rerun' ? 'asus' : r.zariadenie
  const where = r.zdroj === 'inbox' ? 'inbox' : r.zdroj === 'rerun' ? 'Rerun' : `${r.zariadenie} · ${r.projekt_t3}`
  return `<div class="row" style="--c:${r.firma ? firma : 'var(--line)'}">
    <span class="bar" title="${r.firma ? 'Firma' : 'Osobné'}"></span>
    <time>${esc(when)}</time>
    <span class="mono-cell"><span class="tag-src">${esc(r.priorita || SOURCE[r.zdroj])}</span></span>
    <span class="what"><b>${esc(r.nazov)}</b><span class="sub">${esc(r.detail)}</span></span>
    <span class="where">${icon(device)}${esc(where)}</span>
  </div>`
}

function renderCaka() {
  const c = state.data.caka || { rows: [] }
  const keep = r => state.strana === 'vsetko' || (state.strana === 'firma') === r.firma
  const rows = c.rows.filter(keep)
  const live = rows.filter(r => r.zdroj !== 'inbox').sort((a, b) => (a.zdroj === 'rerun' ? -1 : 0) - (b.zdroj === 'rerun' ? -1 : 0) || b.kedy.localeCompare(a.kedy))
  const p1 = rows.filter(r => r.priorita === 'P1'), p2 = rows.filter(r => r.priorita === 'P2')
  const count = s => c.rows.filter(r => s === 'vsetko' || (s === 'firma') === r.firma).length
  $('#f-strana').innerHTML = STRANY.map(([id, label]) =>
    `<button data-strana="${id}" aria-pressed="${state.strana === id}">${label} ${count(id)}</button>`).join('')
  const p2open = $('#caka .caka-more')?.open ? ' open' : ''
  let html = ''
  if (live.length) html += `<p class="group-title">Odpovedz alebo pozri</p>` + live.map(cakaRow).join('')
  if (p1.length) html += `<p class="group-title">Inbox P1</p>` + p1.map(cakaRow).join('')
  if (p2.length) html += `<details class="caka-more"${p2open}><summary>Inbox P2, ${p2.length} ďalších</summary>${p2.map(cakaRow).join('')}</details>`
  if (c.missing?.length) html += `<p class="hint">Neozvalo sa: ${esc(c.missing.join(', '))}.</p>`
  $('#caka').innerHTML = html || '<p class="hint">Nič nečaká.</p>'
}

function renderStale() {
  const d = state.data
  const by = {}
  for (const r of d.procesy) {
    if (r.dalsi || r.stav === 'vypnuté' || r.stav === 'neplatné' || !visible(r.zariadenie, r.projekt)) continue
    const dev = (by[r.zariadenie] ??= {})
    const key = r.skupina || r.nazov
    ;(dev[key] ??= { project: r.projekt, rows: [] }).rows.push(r)
  }
  $('#stale').innerHTML = Object.entries(by).map(([device, groups]) => `<div class="device">
      <h3>${icon(device)}${esc(device)}</h3>
      ${Object.entries(groups).map(([name, g]) => `<div class="svc" style="--c:${proj(g.project).farba}">
        <span class="bar"></span><span>${esc(name)}</span><span class="n">${g.rows.length > 1 ? g.rows.length + '×' : esc(g.rows[0].typ)}</span></div>`).join('')}
    </div>`).join('') || '<p class="hint">Nič pre zvolené filtre.</p>'
}

function renderAkt() {
  const d = state.data
  const rows = d.aktualizacie.filter(u => visible(u.zariadenie, u.projekt))
  $('#aktualizacie').innerHTML = `<table><thead><tr><th>Čo</th><th>Kde</th><th>Máš</th><th>Najnovšie</th><th>Stav</th></tr></thead><tbody>
    ${rows.map(u => {
      const p = proj(u.projekt)
      const have = u.caka != null ? `${u.caka} čaká` : esc(u.ma)
      const nw = u.caka != null ? (u.auto ? 'automaticky' : 'ručne') : `${esc(u.najnovsie)}${u.vydane ? ' z ' + esc(u.vydane) : ''}`
      return `<tr class="${u.stav === 'treba ručne' ? 'manual' : ''}" style="--c:${p.farba}"><td><span class="mono">${esc(p.znak)}</span>${esc(u.nazov)}</td>
        <td>${esc(u.zariadenie)}</td><td>${have}</td><td>${nw}</td><td>${esc(u.stav)}</td></tr>`
    }).join('')}</tbody></table>`
}

function renderSucty() {
  const d = state.data
  const live = d.procesy.filter(r => r.stav !== 'vypnuté' && r.stav !== 'neplatné')
  const count = f => live.filter(f).length
  const sums = [
    [live.length, 'procesov spolu'],
    [count(r => r.ai === 'áno'), 'volá AI sám'],
    [count(r => r.ai === 'spúšťa'), 'spúšťa AI inde'],
    [count(r => r.dalsi), 's plánom'],
    [d.procesy.filter(r => r.chaos).length, 'na upratanie'],
    ...['asus', 'dell', 'e540', 'x270', 'vps'].map(dev => [count(r => r.zariadenie === dev), `na ${dev}`]),
  ]
  $('#sucty').innerHTML = sums.map(([n, l]) => `<div class="sum"><strong>${n}</strong><span>${esc(l)}</span></div>`).join('')
}

function renderFilters() {
  const f = state.data.farby
  $('#f-rodiny').innerHTML = Object.entries(f.rodiny).map(([id, r]) =>
    `<button class="chip" data-k="rodiny" data-v="${esc(id)}" aria-pressed="${!state.off.rodiny.has(id)}" style="--c:${r.farba}"><span class="dot"></span>${esc(r.nazov)}</button>`).join('')
  $('#f-stroje').innerHTML = Object.keys(ICONS).map(dev =>
    `<button class="chip" data-k="stroje" data-v="${dev}" aria-pressed="${!state.off.stroje.has(dev)}">${icon(dev)}${dev}</button>`).join('')
}

function renderFarby() {
  const f = state.data.farby
  $('#farby-body').innerHTML = Object.entries(f.rodiny).map(([id, r]) => `<div class="fam">
      <input type="color" value="${esc(r.farba)}" data-rodina="${esc(id)}" aria-label="Farba rodiny ${esc(r.nazov)}">
      <span>${esc(r.nazov)}<span class="src">${esc(r.zdroj || '')}</span></span>
      <span class="projs">${Object.entries(f.projekty).filter(([, p]) => p.rodina === id).map(([pid, p]) =>
        `<label><span class="mono" style="--c:${r.farba}">${esc(p.znak)}</span>${esc(p.nazov)}
          <select data-projekt="${esc(pid)}" aria-label="Rodina projektu ${esc(p.nazov)}">${Object.entries(f.rodiny).map(([rid, rr]) =>
            `<option value="${esc(rid)}"${rid === id ? ' selected' : ''}>${esc(rr.nazov)}</option>`).join('')}</select></label>`).join('')}</span>
    </div>`).join('') + '<button class="save" id="save">Uložiť farby</button><span class="saved" id="saved"></span>'
}

function render() {
  const d = state.data
  const age = d.inventar ? Math.round((Date.now() - Date.parse(d.inventar)) / 60000) : null
  $('#stamp').textContent = (age == null ? 'Inventúra ešte nebežala.' : `Stroje prečítané pred ${age} min.`) +
    (d.chyba.length ? ` Nedostupné: ${d.chyba.join(', ')}.` : '')
  renderFilters(); renderCaka(); renderRozpis(); renderStale(); renderAkt(); renderSucty()
  if (!$('#farby').open) renderFarby()
}

async function load() {
  state.data = await (await fetch('api/data')).json()
  render()
}

document.addEventListener('click', async e => {
  const seg = e.target.closest('[data-strana]')
  if (seg) { state.strana = seg.dataset.strana; return renderCaka() }
  const chip = e.target.closest('.chip')
  if (chip) {
    const set = state.off[chip.dataset.k]
    set.has(chip.dataset.v) ? set.delete(chip.dataset.v) : set.add(chip.dataset.v)
    return render()
  }
  if (e.target.id === 'save') {
    const f = structuredClone(state.data.farby)
    document.querySelectorAll('[data-rodina]').forEach(i => { f.rodiny[i.dataset.rodina].farba = i.value })
    document.querySelectorAll('[data-projekt]').forEach(s => { f.projekty[s.dataset.projekt].rodina = s.value })
    const r = await fetch('api/farby', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Prehlad': '1' }, body: JSON.stringify(f) })
    $('#saved').textContent = r.ok ? 'Uložené.' : 'Neuložilo sa, skús znova.'
    if (r.ok) { await load(); renderFarby() }
  }
})

load()
setInterval(load, 5 * 60 * 1000)
