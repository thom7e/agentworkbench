(function () {
  function toBuf(s) {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    s += '='.repeat((4 - s.length % 4) % 4);
    var bin = atob(s), a = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
    return a.buffer;
  }
  function toB64(buf) {
    var a = new Uint8Array(buf), s = '';
    for (var i = 0; i < a.length; i++) s += String.fromCharCode(a[i]);
    return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function serialize(c) {
    var r = c.response, out = { id: c.id, rawId: toB64(c.rawId), type: c.type, clientExtensionResults: c.getClientExtensionResults(), response: { clientDataJSON: toB64(r.clientDataJSON) } };
    if (c.authenticatorAttachment) out.authenticatorAttachment = c.authenticatorAttachment;
    if (r.attestationObject) {
      out.response.attestationObject = toB64(r.attestationObject);
      if (r.getTransports) out.response.transports = r.getTransports();
    } else {
      out.response.authenticatorData = toB64(r.authenticatorData);
      out.response.signature = toB64(r.signature);
      if (r.userHandle) out.response.userHandle = toB64(r.userHandle);
    }
    return out;
  }
  function post(url, body) {
    return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(function (r) { if (!r.ok) throw new Error(url + ' ' + r.status); return r; });
  }
  function show(el, e) {
    el.textContent = el.textContent.split(' [')[0] + ' [' + ((e && e.name) || 'Fehler') + ': ' + ((e && e.message) || e) + ']';
    el.hidden = false;
  }
  window.awbPasskey = {
    show: show,
    login: function (next) {
      return fetch('/passkey/login/options').then(function (r) { return r.json(); }).then(function (o) {
        o.challenge = toBuf(o.challenge);
        (o.allowCredentials || []).forEach(function (c) { c.id = toBuf(c.id); });
        return navigator.credentials.get({ publicKey: o });
      }).then(function (c) { return post('/passkey/login/verify', { credential: serialize(c) }); })
        .then(function () { location.href = next || '/'; });
    },
    register: function (name) {
      return fetch('/passkey/register/options').then(function (r) { return r.json(); }).then(function (o) {
        o.challenge = toBuf(o.challenge);
        o.user.id = toBuf(o.user.id);
        (o.excludeCredentials || []).forEach(function (c) { c.id = toBuf(c.id); });
        return navigator.credentials.create({ publicKey: o });
      }).then(function (c) { return post('/passkey/register/verify', { credential: serialize(c), name: name }); })
        .then(function () { location.reload(); });
    }
  };
})();
