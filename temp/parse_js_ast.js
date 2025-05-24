const esprima = require('esprima');
const fs = require('fs');

const jsCode = fs.readFileSync(process.argv[2], 'utf-8');
const ast = esprima.parseScript(jsCode, { tolerant: true, loc: true });

console.log(JSON.stringify(ast, null, 2));
