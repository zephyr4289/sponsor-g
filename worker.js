/**
 * KnowYourSponsor Web Worker Search & Compute Engine
 * Handles off-main-thread indexing, multi-facet bitmask filtering, and relevance ranking.
 */

let all = [];
let companyFlags = {};
let licensedSince = {};
let ratingChanges = [];
let newNames = new Set();
let removedNames = new Set();
let addedRows = [];
let removedRows = [];
let downgradedRows = [];

// Severity definitions matching pipeline
const WARNINGS = [
  ['not_active', null, 'serious', 'Companies House records this company as no longer active (Liquidation, Strike-off, Dissolved).'],
  ['dormant', 'Dormant', 'notable', 'This company files accounts as dormant, reporting no significant trading.'],
  ['accounts_overdue', 'Accounts overdue', 'notable', 'This company has not filed its statutory accounts by the due date.'],
  ['confirmation_statement_overdue', 'Filing overdue', 'context', 'This company has not filed its confirmation statement by the due date.'],
  ['incorporated_recently', 'New company', 'context', 'This company was incorporated within the last year.']
];

const STATUS_LABEL = [
  [/proposal to strike off/i, 'Strike-off proposed'],
  [/voluntary arrangement/i,  'Voluntary arrangement'],
  [/receiver/i,               'Receiver appointed'],
  [/administration/i,         'In Administration'],
  [/liquidation/i,            'Liquidation'],
  [/dissolved/i,              'Dissolved']
];

function shortStatus(status) {
  const s = String(status || '');
  for (const [pattern, label] of STATUS_LABEL) {
    if (pattern.test(s)) return label;
  }
  const plain = s.replace(/^Active\s*-\s*/i, '');
  return plain.length > 22 ? plain.slice(0, 21) + '…' : (plain || 'Not active');
}

function warningFor(name) {
  const record = companyFlags[name];
  if (!record || !record.flags || !record.flags.length) return null;
  for (const [flag, label, severity, explanation] of WARNINGS) {
    if (!record.flags.includes(flag)) continue;
    return {
      label: label || shortStatus(record.status),
      severity: severity,
      status: record.status || '',
      crn: record.number || '',
      incorporated: record.incorporated || '',
      accounts: record.accounts || '',
      flags: record.flags,
      explanation: explanation
    };
  }
  return null;
}

function relevance(row, needle) {
  const name = String(row[0]).toLowerCase();
  if (name === needle) return 0;
  if (name.startsWith(needle)) return 1;
  let at = name.indexOf(needle);
  while (at !== -1) {
    const before = at === 0 ? ' ' : name.charAt(at - 1);
    if (before < '0' || (before > '9' && before < 'a') || before > 'z') {
      return 2;
    }
    at = name.indexOf(needle, at + 1);
  }
  if (name.includes(needle)) return 3;
  return 4; // Locality, county, or industry match
}

function rankByRelevance(list, query) {
  const needle = query.trim().toLowerCase();
  if (!needle || list.length > 20000) return list;
  return list
    .map((row, i) => [relevance(row, needle), i, row])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
    .map(entry => entry[2]);
}

self.onmessage = function(e) {
  const msg = e.data;
  if (msg.type === 'INIT') {
    all = msg.all || [];
    companyFlags = msg.companyFlags || {};
    licensedSince = msg.licensedSince || {};
    ratingChanges = msg.ratingChanges || [];
    addedRows = msg.addedRows || [];
    removedRows = msg.removedRows || [];
    
    newNames = new Set(addedRows.map(r => r[0].toLowerCase()));
    removedNames = new Set(removedRows.map(r => r[0].toLowerCase()));

    // Downgrades to B
    const byKey = new Map(all.map(s => [(s[0] + '|' + s[1]).toLowerCase(), s]));
    downgradedRows = (ratingChanges || [])
      .filter(c => c.action === 'downgraded')
      .map(c => byKey.get(((c.name || '') + '|' + (c.town || '')).toLowerCase()))
      .filter(Boolean)
      .filter(s => String(s[5] || '').trim().toUpperCase() === 'B');

    // Telemetry and statistics
    let totalSerious = 0;
    let totalNotable = 0;
    let totalFlagged = 0;

    for (let i = 0; i < all.length; i++) {
      const w = warningFor(all[i][0]);
      if (w) {
        totalFlagged++;
        if (w.severity === 'serious') totalSerious++;
        else if (w.severity === 'notable') totalNotable++;
      }
    }

    self.postMessage({
      type: 'INIT_COMPLETE',
      total: all.length,
      addedCount: addedRows.length,
      removedCount: removedRows.length,
      downgradedCount: downgradedRows.length,
      flaggedCount: totalFlagged,
      seriousCount: totalSerious,
      notableCount: totalNotable
    });
  } else if (msg.type === 'QUERY') {
    const { query, city, industry, route, rating, view, warn, savedKeys, requestId } = msg;
    
    let source = all;
    if (view === 'added') source = addedRows;
    else if (view === 'removed') source = removedRows;
    else if (view === 'downgraded') source = downgradedRows;
    else if (view === 'saved') {
      const savedSet = new Set(savedKeys || []);
      source = all.filter(s => savedSet.has((s[0] + '|' + s[1]).toLowerCase()));
    }

    const qWords = query ? query.trim().toLowerCase().split(/\s+/).filter(Boolean) : [];
    
    let filtered = source.filter(s => {
      // Warning / Solvency level filter
      if (warn) {
        const w = warningFor(s[0]);
        if (!w) return false;
        if (warn === 'serious' && w.severity !== 'serious') return false;
        if (warn === 'notable' && w.severity !== 'notable' && w.severity !== 'serious') return false;
      }

      // City filter
      if (city && s[1] !== city) return false;

      // Industry filter
      if (industry && s[3] !== industry) return false;

      // Route filter
      if (route && !s[4].includes(route)) return false;

      // Rating filter
      if (rating && String(s[5] || '').toUpperCase() !== rating.toUpperCase()) return false;

      // Search term matching across company, CRN, town, county, industry
      if (qWords.length) {
        const record = companyFlags[s[0]];
        const crn = record && record.number ? record.number.toLowerCase() : '';
        const haystack = (s[0] + ' ' + crn + ' ' + s[1] + ' ' + s[2] + ' ' + s[3]).toLowerCase();
        for (let j = 0; j < qWords.length; j++) {
          if (!haystack.includes(qWords[j])) return false;
        }
      }

      return true;
    });

    if (query && query.trim()) {
      filtered = rankByRelevance(filtered, query);
    }

    self.postMessage({
      type: 'QUERY_RESULTS',
      requestId: requestId,
      totalCount: filtered.length,
      results: filtered.slice(0, 500) // Transmit leading slice
    });
  }
};
