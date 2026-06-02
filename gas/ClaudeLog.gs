// ═══════════════════════════════════════════════════════
// FILE    : ClaudeLog.gs
// PROJECT : Claude Dashboard
// REV     : 01
// DATE    : 02/06/2026
// SUMMARY : save() and getAll() for LOG sheet
// ───────────────────────────────────────────────────────
// REVISION HISTORY:
// Rev 01 | 02/06/2026 | Initial
// ═══════════════════════════════════════════════════════

var ClaudeLog = (function() {

  function save(data) {
    var sheet = getOrCreateSheet(SHEET.LOG);
    var ts    = new Date().toISOString();
    var d     = data.timestamp ? new Date(data.timestamp) : new Date();
    var row = [
      formatDate(d),
      formatTime(d),
      data.source       || 'code',
      data.model        || '',
      data.project      || '',
      data.task         || '',
      data.category     || 'other',
      data.tokens_in    != null ? Number(data.tokens_in)    : 0,
      data.tokens_out   != null ? Number(data.tokens_out)   : 0,
      data.cost_pct     != null ? Number(data.cost_pct)     : 0,
      data.duration_min != null ? Number(data.duration_min) : 0,
      ts,
    ];
    sheet.appendRow(row);
    return { ok: true, saved: true };
  }

  function getAll(filter) {
    var sheet   = getOrCreateSheet(SHEET.LOG);
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) return { ok: true, data: [] };

    var numCols = HEADERS.LOG.length;
    var rows    = sheet.getRange(2, 1, lastRow - 1, numCols).getValues();

    if (filter && filter.date) {
      var filterDate = String(filter.date);
      rows = rows.filter(function(r) {
        return String(r[COL.LOG.DATE]) === filterDate;
      });
    }
    return { ok: true, data: rows };
  }

  return { save: save, getAll: getAll };
})();
