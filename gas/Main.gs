// ═══════════════════════════════════════════════════════
// FILE    : Main.gs
// PROJECT : Claude Dashboard
// REV     : 01
// DATE    : 02/06/2026
// SUMMARY : Router — saveClaudeLog, getClaudeLogs, ping
// ───────────────────────────────────────────────────────
// REVISION HISTORY:
// Rev 01 | 02/06/2026 | Initial — router for Claude usage dashboard
// ═══════════════════════════════════════════════════════

function doGet(e) {
  return jsonOut({ ok: true, service: 'Claude Dashboard', ts: new Date().toISOString() });
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonOut({ ok: false, error: 'No POST body' });
    }
    var body;
    try {
      body = JSON.parse(e.postData.contents);
    } catch(err) {
      return jsonOut({ ok: false, error: 'Invalid JSON: ' + err.message });
    }
    return handleAction(body);
  } catch(err) {
    Logger.log('doPost error: ' + err.message);
    return jsonOut({ ok: false, error: err.message });
  }
}

function handleAction(body) {
  var result;
  switch (body.action) {
    case 'saveClaudeLog': result = ClaudeLog.save(body.data || {});     break;
    case 'getClaudeLogs': result = ClaudeLog.getAll(body.filter || {}); break;
    case 'ping':          result = { ok: true, ts: new Date().toISOString() }; break;
    default:              result = { ok: false, error: 'Unknown action: ' + body.action };
  }
  return jsonOut(result);
}

function jsonOut(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function testPing() {
  var res = handleAction({ action: 'ping' });
  Logger.log(res.getContent());
}
