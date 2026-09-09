/**
 * KnowYourSponsor Web Worker Search & Compute Engine (Phase 2 Architecture)
 * Ultra-low-latency off-main-thread search, multi-facet bitmask intersection,
 * and high-throughput NMW & Companies House solvency indexing.
 */

let all = [];
let companyFlags = {};
let licensedSince = {};
let ratingChanges = [];
let nmwData = {};
let addedRows = [];
let removedRows = [];
let downgradedRows = [];

// Pre-computed lowercase search cache for 127k sponsors
let searchIndex = []; // Array of pre-computed search strings: "name town county industry crn"

// Map of (name + '|' + town).toLowerCase() -> index in `all`
let keyToIndexMap = new Map();

// Severity definitions matching statutory pipeline
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
    if (record.flags.includes(flag)) {
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
  return 4;
}

function rankByRelevance(list, query) {
  const needle = query.trim().toLowerCase();
  if (!needle || list.length > 30000) return list;
  return list
    .map((row, i) => [relevance(row, needle), i, row])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1])
    .map(entry => entry[2]);
}

function executeFilter(params) {
  const { query, city, industry, route, rating, view, warn, savedKeys } = params;
  
  let source = all;
  let usePreindexedSearch = true;
  
  if (view === 'added') { source = addedRows; usePreindexedSearch = false; }
  else if (view === 'removed') { source = removedRows; usePreindexedSearch = false; }
  else if (view === 'downgraded') { source = downgradedRows; usePreindexedSearch = false; }
  else if (view === 'saved') {
    const savedSet = new Set(savedKeys || []);
    source = all.filter(s => savedSet.has((s[0] + '|' + s[1]).toLowerCase()));
    usePreindexedSearch = false;
  } else if (view === 'flagged') {
    source = all.filter(s => !!warningFor(s[0]));
    usePreindexedSearch = false;
  } else if (view === 'nmw') {
    source = all.filter(s => !!nmwData[s[0]]);
    usePreindexedSearch = false;
  }

  const qWords = query ? query.trim().toLowerCase().split(/\s+/).filter(Boolean) : [];
  let filtered = [];
  const sourceLen = source.length;

  for (let i = 0; i < sourceLen; i++) {
    const s = source[i];

    // Solvency warning filter
    if (warn) {
      const w = warningFor(s[0]);
      if (!w) continue;
      if (warn === 'serious' && w.severity !== 'serious') continue;
      if (warn === 'notable' && w.severity !== 'notable' && w.severity !== 'serious') continue;
    }

    // Facet filters
    if (city && s[1] !== city) continue;
    if (industry && s[3] !== industry) continue;
    if (route && !s[4].includes(route)) continue;
    if (rating && String(s[5] || '').toUpperCase() !== rating.toUpperCase()) continue;

    // Text search
    if (qWords.length) {
      let haystack = '';
      if (usePreindexedSearch) {
        haystack = searchIndex[i];
      } else {
        const key = (s[0] + '|' + s[1]).toLowerCase();
        const mainIdx = keyToIndexMap.get(key);
        if (typeof mainIdx === 'number' && searchIndex[mainIdx]) {
          haystack = searchIndex[mainIdx];
        } else {
          const record = companyFlags[s[0]];
          const crn = record && record.number ? record.number.toLowerCase() : '';
          haystack = (s[0] + ' ' + crn + ' ' + s[1] + ' ' + s[2] + ' ' + s[3]).toLowerCase();
        }
      }

      let match = true;
      for (let j = 0; j < qWords.length; j++) {
        if (!haystack.includes(qWords[j])) {
          match = false;
          break;
        }
      }
      if (!match) continue;
    }

    filtered.push(s);
  }

  if (query && query.trim()) {
    filtered = rankByRelevance(filtered, query);
  }

  return filtered;
}

self.onmessage = function(e) {
  const msg = e.data;
  if (!msg) return;
  
  if (msg.type === 'INIT') {
    all = msg.all || [];
    companyFlags = msg.companyFlags || {};
    licensedSince = msg.licensedSince || {};
    ratingChanges = msg.ratingChanges || [];
    nmwData = msg.nmwData || {};
    addedRows = msg.addedRows || [];
    removedRows = msg.removedRows || [];

    // Pre-build search cache and key lookup map
    searchIndex = new Array(all.length);
    keyToIndexMap = new Map();
    
    for (let i = 0; i < all.length; i++) {
      const s = all[i];
      const name = s[0];
      const town = s[1];
      const key = (name + '|' + town).toLowerCase();
      keyToIndexMap.set(key, i);

      const record = companyFlags[name];
      const crn = record && record.number ? record.number.toLowerCase() : '';
      searchIndex[i] = (name + ' ' + crn + ' ' + town + ' ' + s[2] + ' ' + s[3]).toLowerCase();
    }

    // Downgrades to B
    downgradedRows = (ratingChanges || [])
      .filter(c => c.action === 'downgraded')
      .map(c => {
        const key = ((c.name || '') + '|' + (c.town || '')).toLowerCase();
        const idx = keyToIndexMap.get(key);
        return typeof idx === 'number' ? all[idx] : null;
      })
      .filter(Boolean)
      .filter(s => String(s[5] || '').trim().toUpperCase() === 'B');

    // Telemetry and macro solvency stats
    let totalSerious = 0;
    let totalNotable = 0;
    let totalFlagged = 0;
    let totalNmw = 0;

    for (let i = 0; i < all.length; i++) {
      const name = all[i][0];
      const w = warningFor(name);
      if (w) {
        totalFlagged++;
        if (w.severity === 'serious') totalSerious++;
        else if (w.severity === 'notable') totalNotable++;
      }
      if (nmwData[name]) totalNmw++;
    }

    self.postMessage({
      type: 'INIT_COMPLETE',
      total: all.length,
      addedCount: addedRows.length,
      removedCount: removedRows.length,
      downgradedCount: downgradedRows.length,
      flaggedCount: totalFlagged,
      seriousCount: totalSerious,
      notableCount: totalNotable,
      nmwCount: totalNmw
    });
  } else if (msg.type === 'QUERY') {
    const filtered = executeFilter(msg);
    const start = typeof msg.offset === 'number' ? msg.offset : 0;
    const count = typeof msg.limit === 'number' ? msg.limit : 200;

    self.postMessage({
      type: 'QUERY_RESULTS',
      requestId: msg.requestId,
      totalCount: filtered.length,
      offset: start,
      results: filtered.slice(start, start + count)
    });
  } else if (msg.type === 'EXPORT_CSV') {
    const filtered = executeFilter(msg);
    const isShortlist = msg.view === 'saved';
    const headers = isShortlist
      ? ['Employer Name', 'Town / City', 'County', 'Industry', 'Approved Visa Routes', 'Rating', 'CRN', 'Status', 'Filing Warning', 'NMW Underpaid', 'Application Status', 'Date Applied', 'Target Role', 'Interview Notes']
      : ['Employer Name', 'Town / City', 'County', 'Industry', 'Approved Visa Routes', 'Rating', 'CRN', 'Status', 'Filing Warning', 'NMW Underpaid'];
    const maxExport = Math.min(filtered.length, 50000);
    const rows = [];
    
    for (let i = 0; i < maxExport; i++) {
      const r = filtered[i];
      const warn = warningFor(r[0]);
      const nmw = nmwData[r[0]];
      const baseRow = [
        r[0], r[1], r[2], r[3],
        (r[4] || []).join('; '),
        r[5],
        warn ? warn.crn : '',
        warn ? warn.status : 'Active',
        warn ? warn.label : '',
        nmw ? 'Yes' : 'No'
      ];
      if (isShortlist) {
        baseRow.push('Shortlisted', '', '', '');
      }
      rows.push(baseRow.map(v => '"' + String(v || '').replace(/"/g, '""') + '"').join(','));
    }

    const csvContent = '\uFEFF' + [headers.join(','), ...rows].join('\r\n');
    self.postMessage({
      type: 'EXPORT_CSV_COMPLETE',
      requestId: msg.requestId,
      csv: csvContent,
      count: maxExport
    });
  }
};
