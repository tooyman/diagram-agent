#!/usr/bin/env node
const ELK = require('elkjs');
const elk = new ELK();

let stdin = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { stdin += chunk; });
process.stdin.on('end', async () => {
  try {
    const graph = JSON.parse(stdin);
    const result = await elk.layout(graph);
    process.stdout.write(JSON.stringify(result));
  } catch (e) {
    process.stderr.write(`ELK error: ${e.message}\n${e.stack || ''}\n`);
    process.exit(1);
  }
});
