const fs = require('fs');
let code = fs.readFileSync('src/pages/loader/LoaderHome.jsx', 'utf8');
const targetStr = 'export default function LoaderHome({ user }) {';
const index = code.indexOf(targetStr);
if (index === -1) throw new Error('Not found');

// Strip out existing component
code = code.substring(0, index);

// Read the new implementation
const newImpl = fs.readFileSync('new_impl.txt', 'utf8');

// Also update imports
code = code.replace("import React, { useState } from 'react';", "import React, { useState, useMemo, useRef, useEffect } from 'react';");

fs.writeFileSync('src/pages/loader/LoaderHome.jsx', code + newImpl);
console.log('Successfully replaced LoaderHome');
