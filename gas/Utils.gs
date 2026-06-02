// ═══════════════════════════════════════════════════════
// FILE    : Utils.gs
// PROJECT : Claude Dashboard
// REV     : 01
// DATE    : 02/06/2026
// SUMMARY : Shared date/time helpers
// ───────────────────────────────────────────────────────
// REVISION HISTORY:
// Rev 01 | 02/06/2026 | Initial
// ═══════════════════════════════════════════════════════

function formatDate(d) {
  var y  = d.getFullYear();
  var m  = String(d.getMonth() + 1);
  var dd = String(d.getDate());
  if (m.length  < 2) m  = '0' + m;
  if (dd.length < 2) dd = '0' + dd;
  return y + '-' + m + '-' + dd;
}

function formatTime(d) {
  var hh = String(d.getHours());
  var mm = String(d.getMinutes());
  if (hh.length < 2) hh = '0' + hh;
  if (mm.length < 2) mm = '0' + mm;
  return hh + ':' + mm;
}

function todayStr() {
  return formatDate(new Date());
}
