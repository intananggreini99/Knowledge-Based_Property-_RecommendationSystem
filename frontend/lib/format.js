// Small shared formatting helpers.

export const rupiah = (v) =>
  v === null || v === undefined || Number.isNaN(Number(v))
    ? '-'
    : 'Rp ' + Number(v).toLocaleString('id-ID');

export const clamp01 = (v) => Math.max(0, Math.min(1, Number(v) || 0));
