import React from 'react';
import Login from '../storemanager/StoreManagerLogin';
export default function BrandLogin(props) { return <Login {...props} expectedBrand="tech" defaultUsername="tech@waypoint.local" />; }
