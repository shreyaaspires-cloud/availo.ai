const fs = require('fs');

const filesToPrefix = [
  'frontend/src/components/chat/ChatWindow.tsx',
  'frontend/src/components/condition/SixAnglePhotoUpload.tsx',
  'frontend/src/components/contract/ContractViewer.tsx',
  'frontend/src/components/contract/SignatureCapture.tsx',
  'frontend/src/components/damage/DamageReport.tsx',
  'frontend/src/components/resource/ResourceCard.tsx',
];

filesToPrefix.forEach(file => {
  if (fs.existsSync(file)) {
    let content = fs.readFileSync(file, 'utf8');
    if (!content.startsWith('"use client"')) {
      content = '"use client"\n\n' + content;
      fs.writeFileSync(file, content, 'utf8');
      console.log('Added "use client" to', file);
    }
  }
});
