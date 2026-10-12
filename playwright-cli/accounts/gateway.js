#!/usr/bin/env node
/**
 * Multi-account gateway: one local address per test account.
 *
 * The gateway logs every account in, keeps its cookies and adds them to each request it forwards.
 * The browser holds no cookies at all, so one browser (or any HTTP tool) can use several accounts
 * side by side: the account is the port.
 *
 * For test environments with throwaway accounts only. Listens on 127.0.0.1.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// @ts-check

const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const https = require('https');
const path = require('path');

const RELOGIN = '/__accounts/relogin';
const PANE_SCRIPT = '/__accounts/pane.js';
const PANE_TAG = `<script src="${PANE_SCRIPT}"></script>`;
const ZOOM = 'accounts:zoom';
// Account N on target T listens on port + 1 + N + T * TARGET_STEP, hence at most 9 accounts.
const TARGET_STEP = 10;

/**
 * Runs in every page shown in a pane. A pane is another origin than the board, so the board cannot see
 * keys pressed inside it: the page itself has to pass the zoom shortcut (Ctrl+Space) on.
 */
function paneScript(board) {
  return `if (window.parent !== window) {
  addEventListener('keydown', event => {
    if (event.ctrlKey && event.code === 'Space' && !event.altKey && !event.metaKey && !event.shiftKey) {
      event.preventDefault();
      parent.postMessage(${JSON.stringify(ZOOM)}, ${JSON.stringify(board)});
    }
  }, true);
}
`;
}

/** Adds the pane script to an HTML page. Works on bytes, so the page's own encoding does not matter. */
function withPaneScript(body) {
  const html = body.toString('latin1');
  const at = html.toLowerCase().lastIndexOf('</body>');
  return Buffer.from(at < 0 ? html + PANE_TAG : html.slice(0, at) + PANE_TAG + html.slice(at), 'latin1');
}

/** Time-based one-time code (RFC 6238, SHA-1, 30 s, 6 digits) from a base32 secret. */
function totp(secret, now = Date.now()) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  let bits = '';
  for (const char of secret.replace(/[\s=]/g, '').toUpperCase()) {
    const value = alphabet.indexOf(char);
    if (value < 0)
      throw new Error('TOTP secret is not base32');
    bits += value.toString(2).padStart(5, '0');
  }
  const key = Buffer.from((bits.match(/.{8}/g) || []).map(byte => parseInt(byte, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(now / 30000)));
  const digest = crypto.createHmac('sha1', key).update(counter).digest();
  const offset = digest[digest.length - 1] & 15;
  return String((digest.readUInt32BE(offset) & 0x7fffffff) % 1e6).padStart(6, '0');
}

/** One flat cookie jar per account. Ignores Path and Domain, which is enough for one app per gateway. */
class Jar {
  constructor() {
    this.cookies = new Map();
  }

  header() {
    return [...this.cookies].map(([name, value]) => `${name}=${value}`).join('; ');
  }

  store(lines = []) {
    for (const line of lines) {
      const [pair, ...attributes] = line.split(';');
      const index = pair.indexOf('=');
      if (index < 0)
        continue;
      const name = pair.slice(0, index).trim();
      const value = pair.slice(index + 1).trim();
      const expired = attributes.some(attribute => {
        const [key, text = ''] = attribute.trim().split('=');
        if (/^max-age$/i.test(key))
          return Number(text) <= 0;
        return /^expires$/i.test(key) && Date.parse(text) <= Date.now();
      });
      if (expired || value === '' || value === '""')
        this.cookies.delete(name);
      else
        this.cookies.set(name, value);
    }
  }
}

/** Hidden form fields of a page, such as a CSRF token. */
function hiddenFields(html) {
  const entities = { amp: '&', quot: '"', '#39': "'", '#x27': "'", lt: '<', gt: '>' };
  const fields = {};
  for (const [tag] of html.matchAll(/<input\b[^>]*>/gi)) {
    const name = /\bname=["']([^"']*)["']/i.exec(tag);
    if (!name || !/\btype=["']?hidden/i.test(tag))
      continue;
    const value = /\bvalue=["']([^"']*)["']/i.exec(tag);
    fields[name[1]] = value ? value[1].replace(/&(amp|quot|#39|#x27|lt|gt);/g, (_, entity) => entities[entity]) : '';
  }
  return fields;
}

/** The request path is passed on verbatim, so a path like //other.host/ can never redirect the cookies elsewhere. */
function upstreamOptions(target, method, requestPath, headers) {
  return { protocol: target.protocol, hostname: target.hostname, port: target.port, method, path: requestPath, headers };
}

function client(target) {
  return target.protocol === 'https:' ? https : http;
}

/** A request the gateway makes on its own, used for logging in. */
function send(target, jar, method, requestPath, headers = {}, body = '') {
  return new Promise((resolve, reject) => {
    const cookie = jar.header();
    const all = { ...headers, ...(cookie ? { cookie } : {}), ...(body ? { 'content-length': Buffer.byteLength(body) } : {}) };
    const request = client(target).request(upstreamOptions(target, method, requestPath, all), response => {
      jar.store(response.headers['set-cookie']);
      const chunks = [];
      response.on('data', chunk => chunks.push(chunk));
      response.on('end', () => resolve({ status: response.statusCode, location: response.headers.location, body: Buffer.concat(chunks).toString() }));
    });
    request.on('error', reject);
    request.end(body);
  });
}

/** Runs the account's login steps: open the page, take its hidden fields, add ours, post. */
async function login(account, target) {
  account.jar.cookies.clear();
  for (const step of account.login || []) {
    const page = await send(target, account.jar, 'GET', step.path);
    const fields = hiddenFields(page.body);
    for (const [name, value] of Object.entries(step.fields || {}))
      fields[name] = value && typeof value === 'object' ? totp(value.totp) : String(value);
    await send(target, account.jar, 'POST', step.path, {
      'content-type': 'application/x-www-form-urlencoded',
      'origin': target.origin,
      'referer': new URL(step.path, target).href,
    }, new URLSearchParams(fields).toString());
  }
  const home = await send(target, account.jar, 'GET', account.home);
  account.state = home.status === 200 ? 'logged in' : `LOGIN FAILED (home answered ${home.status}${home.location ? ' -> ' + home.location : ''})`;
  return home.status === 200;
}

/**
 * Only this machine's browser may talk to the gateway: a foreign Host header means DNS rebinding,
 * and a cross-site request means another website trying to ride on the injected login.
 */
function allowed(request, port) {
  const host = request.headers.host;
  return (host === `127.0.0.1:${port}` || host === `localhost:${port}`) && request.headers['sec-fetch-site'] !== 'cross-site';
}

function refuse(response) {
  response.writeHead(403, { 'content-type': 'text/plain; charset=utf-8' });
  response.end('Refused. Open this address directly in the browser; requests coming from other sites are not accepted.\n');
}

/** Forwards one account's port to one target. */
function forward(account, target, loginTarget, port, boardPort) {
  return http.createServer((request, response) => {
    if (!allowed(request, port))
      return refuse(response);
    const here = `http://${request.headers.host}`;
    if (request.url === PANE_SCRIPT) {
      response.writeHead(200, { 'content-type': 'text/javascript; charset=utf-8', 'cache-control': 'no-store' });
      return response.end(paneScript(`http://${new URL(here).hostname}:${boardPort}`));
    }
    if (request.url === RELOGIN) {
      login(account, loginTarget).catch(() => false).then(() => {
        response.writeHead(302, { location: account.home });
        response.end();
      });
      return;
    }

    const headers = { ...request.headers, host: target.host };
    delete headers.cookie;
    delete headers.connection;
    // Pages are asked for uncompressed, so that the pane script can be added to them.
    delete headers['accept-encoding'];
    if (headers.origin)
      headers.origin = target.origin;
    if (headers.referer)
      headers.referer = headers.referer.replace(here, target.origin);
    const cookie = account.jar.header();
    if (cookie)
      headers.cookie = cookie;

    const upstream = client(target).request(upstreamOptions(target, request.method, request.url, headers), answer => {
      account.jar.store(answer.headers['set-cookie']);
      const out = { ...answer.headers };
      delete out['set-cookie'];
      delete out['connection'];
      delete out['keep-alive'];
      // The board shows every account in a frame, so the framing bans have to go.
      delete out['x-frame-options'];
      const policy = out['content-security-policy'];
      if (typeof policy === 'string')
        out['content-security-policy'] = policy.replace(/frame-ancestors[^;]*;?\s*/i, '');
      if (out.location && out.location.startsWith(target.origin))
        out.location = here + out.location.slice(target.origin.length);
      if (!/^text\/html\b/i.test(answer.headers['content-type'] || '') || answer.headers['content-encoding']) {
        response.writeHead(answer.statusCode || 502, out);
        answer.pipe(response);
        return;
      }
      // An HTML page is held back whole, so that the pane script can be added to it.
      const chunks = [];
      answer.on('data', chunk => chunks.push(chunk));
      answer.on('error', () => response.destroy());
      answer.on('end', () => {
        let body = Buffer.concat(chunks);
        if (body.length) {
          body = withPaneScript(body);
          delete out['transfer-encoding'];
          out['content-length'] = String(body.length);
        } else if (request.method === 'HEAD') {
          delete out['content-length'];
        }
        response.writeHead(answer.statusCode || 502, out);
        response.end(body);
      });
    });
    upstream.on('error', error => {
      if (!response.headersSent)
        response.writeHead(502, { 'content-type': 'text/plain; charset=utf-8' });
      response.end(`The target ${target.origin} is not answering: ${error.message}\n`);
    });
    request.pipe(upstream);
  });
}

function boardPage(config, accounts, targets) {
  const data = {
    port: config.port,
    step: TARGET_STEP,
    relogin: RELOGIN,
    zoom: ZOOM,
    targets: targets.map(target => target.name),
    accounts: accounts.map(account => ({ name: account.name, home: account.home, follow: account.follow !== false, state: account.state })),
  };
  return fs.readFileSync(path.join(__dirname, 'board.html'), 'utf8').replace('/*DATA*/null', JSON.stringify(data).replace(/</g, '\\u003c'));
}

function listen(server, port) {
  return new Promise((resolve, reject) => {
    server.once('error', error => reject(new Error(`Cannot listen on 127.0.0.1:${port}: ${error.message}`)));
    server.listen(port, '127.0.0.1', () => resolve(server));
  });
}

/** Logs all accounts in and starts the board and one port per account and target. */
async function start(config) {
  const port = config.port = config.port || 4300;
  const targets = Object.entries(config.targets || {}).map(([name, address]) => ({ name, url: new URL(address) }));
  const accounts = (config.accounts || []).map(account => ({ home: '/', ...account, jar: new Jar(), state: '' }));
  if (!targets.length || !accounts.length)
    throw new Error('The config needs at least one target and one account.');
  if (accounts.length >= TARGET_STEP)
    throw new Error(`At most ${TARGET_STEP - 1} accounts fit on one board.`);

  for (const account of accounts) {
    await login(account, targets[0].url).catch(error => {
      account.state = `LOGIN FAILED (${error.message})`;
    });
  }

  const servers = [];
  const board = http.createServer((request, response) => {
    if (!allowed(request, port))
      return refuse(response);
    response.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' });
    response.end(boardPage(config, accounts, targets));
  });
  servers.push(await listen(board, port));
  const address = (accountIndex, targetIndex) => port + 1 + accountIndex + targetIndex * TARGET_STEP;
  for (const [targetIndex, target] of targets.entries()) {
    for (const [accountIndex, account] of accounts.entries())
      servers.push(await listen(forward(account, target.url, targets[0].url, address(accountIndex, targetIndex), port), address(accountIndex, targetIndex)));
  }

  return {
    board: `http://127.0.0.1:${port}/`,
    accounts: accounts.map((account, accountIndex) => ({
      name: account.name,
      state: account.state,
      urls: Object.fromEntries(targets.map((target, targetIndex) => [target.name, `http://127.0.0.1:${address(accountIndex, targetIndex)}${account.home}`])),
    })),
    close: () => Promise.all(servers.map(server => new Promise(resolve => {
      server.closeAllConnections();
      server.close(resolve);
    }))),
  };
}

async function main() {
  const file = process.argv[2];
  if (!file) {
    console.error('Usage: node accounts/gateway.js <accounts.json>');
    process.exit(1);
  }
  const running = await start(JSON.parse(fs.readFileSync(file, 'utf8')));
  console.log(`Board  ${running.board}`);
  for (const account of running.accounts)
    console.log(`${account.name}  ${Object.entries(account.urls).map(([target, url]) => `${target}: ${url}`).join('  ')}  ${account.state}`);
}

if (require.main === module) {
  main().catch(error => {
    console.error(error.message);
    process.exit(1);
  });
}

module.exports = { start, totp, hiddenFields, Jar };
