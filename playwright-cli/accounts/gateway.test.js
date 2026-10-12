// @ts-check
// Run with: node --test accounts/

const assert = require('node:assert');
const crypto = require('node:crypto');
const http = require('node:http');
const test = require('node:test');

const { start, totp, hiddenFields } = require('./gateway');

// RFC 6238 test secret ("12345678901234567890").
const SECRET = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ';

/** A small app with what real ones have: CSRF token, origin check, second factor, session cookie, framing ban. */
function fakeApp() {
  const sessions = new Map();
  let origin = '';
  const server = http.createServer((request, response) => {
    const cookies = Object.fromEntries((request.headers.cookie || '').split('; ').filter(Boolean).map(pair => pair.split('=')));
    const chunks = [];
    request.on('data', chunk => chunks.push(chunk));
    request.on('end', () => {
      const form = new URLSearchParams(Buffer.concat(chunks).toString());
      const sameOrigin = request.headers.origin === origin && request.headers.host === new URL(origin).host;
      if (request.url === '/login' && request.method === 'GET') {
        const csrf = cookies.csrf || crypto.randomUUID();
        response.writeHead(200, { 'set-cookie': `csrf=${csrf}; Path=/` });
        return response.end(`<form method="post"><input type="hidden" name="csrf" value="${csrf}"><input name="user"></form>`);
      }
      if (request.method === 'POST' && (!sameOrigin || (request.url === '/login' && form.get('csrf') !== cookies.csrf))) {
        response.writeHead(403);
        return response.end('forbidden');
      }
      if (request.url === '/login') {
        if (form.get('code') !== totp(SECRET) || form.get('password') !== 'pw-' + form.get('user')) {
          response.writeHead(403);
          return response.end('wrong credentials');
        }
        const sid = crypto.randomUUID();
        sessions.set(sid, form.get('user'));
        response.writeHead(302, { 'set-cookie': `sid=${sid}; Path=/; HttpOnly`, 'location': '/' });
        return response.end();
      }
      if (request.url === '/logout') {
        sessions.delete(cookies.sid);
        response.writeHead(302, { 'set-cookie': 'sid=; Max-Age=0; Path=/', 'location': origin + '/login' });
        return response.end();
      }
      const user = sessions.get(cookies.sid);
      if (!user) {
        response.writeHead(302, { location: origin + '/login' });
        return response.end();
      }
      const page = request.url === '/page';
      response.writeHead(200, { 'x-frame-options': 'DENY', 'content-security-policy': "default-src 'self'; frame-ancestors 'none'", ...(page ? { 'content-type': 'text/html; charset=utf-8' } : {}) });
      response.end(page ? `<body><p>hello ${user}</p></body>` : `hello ${user}`);
    });
  });
  return new Promise(resolve => server.listen(0, '127.0.0.1', () => {
    origin = `http://127.0.0.1:${/** @type {import('net').AddressInfo} */ (server.address()).port}`;
    resolve({ server, origin });
  }));
}

function call(port, method, requestPath, headers = {}) {
  return new Promise((resolve, reject) => {
    const request = http.request({ host: '127.0.0.1', port, method, path: requestPath, headers }, response => {
      const chunks = [];
      response.on('data', chunk => chunks.push(chunk));
      response.on('end', () => resolve({ status: response.statusCode, headers: response.headers, body: Buffer.concat(chunks).toString() }));
    });
    request.on('error', reject);
    request.end();
  });
}

test('several accounts through one gateway', async t => {
  const app = await fakeApp();
  const port = 20000 + Math.floor(Math.random() * 20000);
  const account = user => ({ name: user, login: [{ path: '/login', fields: { user, password: 'pw-' + user, code: { totp: SECRET } } }] });
  const gateway = await start({ port, targets: { app: app.origin }, accounts: [account('anna'), account('boris')] });
  t.after(async () => {
    await gateway.close();
    app.server.closeAllConnections();
    app.server.close();
  });
  const anna = port + 1;
  const boris = port + 2;

  await t.test('every port answers as its own account, whatever cookies the browser sends', async () => {
    assert.deepStrictEqual(gateway.accounts.map(each => each.state), ['logged in', 'logged in']);
    assert.strictEqual((await call(anna, 'GET', '/')).body, 'hello anna');
    assert.strictEqual((await call(boris, 'GET', '/', { cookie: 'sid=somebody-else' })).body, 'hello boris');
  });

  await t.test('the browser never receives the login cookies', async () => {
    assert.strictEqual((await call(anna, 'GET', '/login')).headers['set-cookie'], undefined);
  });

  await t.test('framing bans are removed and the rest of the policy stays', async () => {
    const { headers } = await call(anna, 'GET', '/');
    assert.strictEqual(headers['x-frame-options'], undefined);
    assert.ok(!headers['content-security-policy'].includes('frame-ancestors'));
    assert.ok(headers['content-security-policy'].includes("default-src 'self'"));
  });

  await t.test('an HTML page gets the script that passes the zoom shortcut to the board, other answers stay as they are', async () => {
    const page = await call(anna, 'GET', '/page', { 'accept-encoding': 'gzip' });
    assert.strictEqual(page.body, '<body><p>hello anna</p><script src="/__accounts/pane.js"></script></body>');
    assert.strictEqual(Number(page.headers['content-length']), Buffer.byteLength(page.body));
    assert.strictEqual((await call(anna, 'GET', '/')).body, 'hello anna');
    const script = await call(anna, 'GET', '/__accounts/pane.js');
    assert.ok(script.headers['content-type'].startsWith('text/javascript'));
    assert.ok(script.body.includes(`"accounts:zoom", "http://127.0.0.1:${port}"`));
  });

  await t.test('other sites and foreign host names are refused', async () => {
    assert.strictEqual((await call(anna, 'GET', '/', { 'sec-fetch-site': 'cross-site' })).status, 403);
    assert.strictEqual((await call(anna, 'GET', '/', { host: 'evil.test' })).status, 403);
    assert.strictEqual((await call(anna, 'GET', '/', { 'sec-fetch-site': 'same-site' })).status, 200);
  });

  await t.test('the board lists the accounts', async () => {
    const board = await call(port, 'GET', '/');
    assert.strictEqual(board.status, 200);
    assert.ok(board.body.includes('"name":"anna"') && board.body.includes('"name":"boris"'));
  });

  await t.test('a form passes the origin check, and logging out touches one account only', async () => {
    const out = await call(anna, 'POST', '/logout', { origin: `http://127.0.0.1:${anna}` });
    assert.strictEqual(out.status, 302);
    assert.strictEqual(out.headers.location, `http://127.0.0.1:${anna}/login`);
    assert.strictEqual((await call(anna, 'GET', '/')).status, 302);
    assert.strictEqual((await call(boris, 'GET', '/')).body, 'hello boris');
  });

  await t.test('logging in again restores the account', async () => {
    assert.strictEqual((await call(anna, 'GET', '/__accounts/relogin')).headers.location, '/');
    assert.strictEqual((await call(anna, 'GET', '/')).body, 'hello anna');
  });
});

test('one-time code matches the RFC 6238 test vector', () => {
  assert.strictEqual(totp(SECRET, 59000), '287082');
});

test('hidden fields are read with their entities decoded, visible fields are left out', () => {
  assert.deepStrictEqual(hiddenFields('<input type="hidden" name="token" value="a&amp;b"><input type="text" name="user" value="x">'), { token: 'a&b' });
});
