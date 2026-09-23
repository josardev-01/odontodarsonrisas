import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import './styles.css';
import './clinical.css';
import './public-site.css';
import './forms-modern.css';
import './landing-video.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode><App /></StrictMode>,
);
