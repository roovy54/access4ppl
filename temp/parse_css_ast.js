const fs = require('fs');
const postcss = require('postcss');

const css = fs.readFileSync(process.argv[2], 'utf8');
const root = postcss.parse(css);

console.log(JSON.stringify(root, null, 2));
