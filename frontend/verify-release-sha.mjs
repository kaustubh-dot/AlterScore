const releaseSha = process.env.VITE_RELEASE_SHA?.trim() || '';

if (!/^[0-9a-f]{40}$/.test(releaseSha)) {
  console.error('VITE_RELEASE_SHA must be a 40-character lowercase Git SHA.');
  process.exit(1);
}

console.log(`VITE_RELEASE_SHA=${releaseSha}`);
