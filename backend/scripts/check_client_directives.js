const fs = require('fs');
const path = require('path');

function walk(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) results = results.concat(walk(fullPath));
    else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) results.push(fullPath);
  });
  return results;
}

const files = walk('./frontend/src');
files.forEach(f => {
  const content = fs.readFileSync(f, 'utf8');
  const hasHooks = content.includes('useState(') || content.includes('useEffect(') || content.includes('useQuery(') || content.includes('useMutation(');
  const startsWithClient = content.startsWith('"use client"') || content.startsWith("'use client'");
  if (hasHooks && !startsWithClient) {
    console.log('MISSING use client:', f);
  }
});
