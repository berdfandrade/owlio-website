# Owlio Website

The official website for **Owlio**, a screenplay editor for film and television.

🌐 **Website:** https://berdfandrade.github.io/owlio-website/  
💻 **Application:** https://github.com/berdfandrade/owlio

The website introduces Owlio, showcases its interface, and highlights its writing and story organization features. It is available in English and Portuguese and is hosted for free using GitHub Pages.

## Technologies

- **Vite** — development server and production builds.
- **JavaScript** — interactions and dynamic functionality.
- **CSS** — visual identity, layouts, and animations.
- **GitHub Actions** — automated build and deployment.
- **GitHub Pages** — website hosting.

## Project Structure

```text
owlio-website/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── public/
│   ├── assets/
│   └── shots/
│       ├── pt/
│       └── en/
├── src/
│   ├── main.js
│   └── site.css
├── en/
│   └── index.html
├── index.html
├── package.json
└── vite.config.js
```

### Pages

- `index.html` — Portuguese version.
- `en/index.html` — English version.

### Visual Assets

- `src/site.css` — styles, layouts, and visual identity.
- `src/main.js` — interactive elements and dynamic download link updates.
- `public/assets/` — visual resources and design system assets.
- `public/shots/` — actual application screenshots, organized by language.

Screenshots are captured directly from Owlio using sample screenplays to showcase the application's interface and features.

## Local Development

Requirements: Node.js and npm.

Clone the repository and install dependencies:

```bash
git clone https://github.com/berdfandrade/owlio-website.git
cd owlio-website
npm install
```

Start the development server:

```bash
npm run dev
```

To generate a production build:

```bash
npm run build
```

The static production files will be generated in the `dist/` directory.

## Dynamic Download Link

The download button automatically points to the latest Windows installer released for Owlio.

The system works in two stages:

1. **During deployment:** a GitHub Action queries the main repository's releases and updates the installer URL across both website versions.
2. **During navigation:** `src/main.js` queries the GitHub API again to check whether a newer version is available.

The installer is identified using the `Owlio-Setup-*.exe` filename pattern.

If no installer has been published yet, the download button redirects visitors to the project's GitHub Releases page.

This approach allows new Owlio versions to be published without manually updating download links on the website.

## Deployment

Deployment is fully automated through GitHub Actions.

Whenever a push is made to the `main` branch, the `.github/workflows/deploy.yml` workflow:

1. Installs project dependencies.
2. Checks the latest Owlio release.
3. Generates the production build.
4. Publishes the contents of `dist/` to GitHub Pages.

The workflow also runs periodically to keep the download link synchronized with the latest available releases.

### GitHub Pages Configuration

The website is hosted at:

`https://berdfandrade.github.io/owlio-website/`

Since the project is deployed under a repository subpath, `vite.config.js` uses `/owlio-website/` as its `base` configuration.

If the project moves to a custom domain, this value should be changed to `/`.

---
