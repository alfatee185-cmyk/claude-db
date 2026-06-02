// ═══════════════════════════════════════════════════════
// FILE    : SheetConfig.gs
// PROJECT : Claude Dashboard
// REV     : 01
// DATE    : 02/06/2026
// SUMMARY : Sheet ID, column map, headers for LOG sheet
// ───────────────────────────────────────────────────────
// REVISION HISTORY:
// Rev 01 | 02/06/2026 | Initial
// ═══════════════════════════════════════════════════════

var SHEET_ID = '1I5OqL7UOeedIUYbHFbEFlM_p-eQo19Pe87zS4BNB5Y8';

var SHEET = {
  LOG: 'LOG',
};

var COL = {
  LOG: {
    DATE:         0,
    TIME:         1,
    SOURCE:       2,
    MODEL:        3,
    PROJECT:      4,
    TASK:         5,
    CATEGORY:     6,
    TOKENS_IN:    7,
    TOKENS_OUT:   8,
    COST_PCT:     9,
    DURATION_MIN: 10,
    TIMESTAMP:    11,
  },
};

var HEADERS = {
  LOG: [
    'Date', 'Time', 'Source', 'Model', 'Project',
    'Task', 'Category', 'TokensIn', 'TokensOut',
    'Cost%', 'DurationMin', 'Timestamp',
  ],
};

function getOrCreateSheet(name) {
  var ss    = SpreadsheetApp.openById(SHEET_ID);
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    var headers = HEADERS[name] || [];
    if (headers.length) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers])
        .setFontWeight('bold')
        .setBackground('#1a1e27')
        .setFontColor('#ffffff');
      sheet.setFrozenRows(1);
    }
  }
  return sheet;
}
