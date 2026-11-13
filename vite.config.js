import { resolve } from 'node:path';
import { defineConfig } from 'vite';

// O kit da taste skill fica em public/assets e é servido como arquivos soltos
// (ele carrega os próprios scripts por caminho). O que o Vite empacota vai para _v/.
// O GitHub Pages publica o site em /owlio-website/. Com um domínio próprio, troque por '/'.
export default defineConfig({
  base: '/owlio-website/',
  build: {
    assetsDir: '_v',
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
        en: resolve(import.meta.dirname, 'en/index.html'),
      },
    },
  },
});
