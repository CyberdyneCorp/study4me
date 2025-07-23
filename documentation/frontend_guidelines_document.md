# Frontend Guideline Document for Study4Me

## 1. Frontend Architecture

### Overview
Our frontend is a Single Page Application (SPA) built with Svelte and bundled with Vite. We use Tailwind CSS for styling. Authentication flows (login, NFT checks) are handled via Web3Auth and WalletConnect. The app communicates with our FastAPI backend over REST to fetch or post data (e.g., topics, graphs, audio summaries).

### How It Scales and Stays Maintainable
- **Modular Code:** We break pages and features into small, self-contained Svelte components. This makes it easy to add new features or fix bugs without touching unrelated code.
- **Tailwind Utility Classes:** Instead of writing big CSS files, we use Tailwind’s atomic classes. This keeps styles consistent and avoids naming clashes.
- **Vite’s Fast HMR:** Hot Module Replacement (HMR) means developers can see changes instantly without a full reload.
- **Separation of Concerns:** UI logic lives in Svelte components, styling lives in Tailwind, and API calls live in a dedicated `services/` folder. This clear separation helps new developers understand the codebase quickly.

## 2. Design Principles

### Usability
- **Clear Layouts:** Bold blocks and high-contrast colors guide users through each step. Primary actions (like "New Topic") are always prominent.
- **Simple Flows:** We never ask users for more than one thing at a time (e.g., connect wallet, then choose content).

### Accessibility
- **Keyboard Navigation:** All interactive elements (buttons, links, form fields) have clear focus states and can be used without a mouse.
- **ARIA Labels:** Non-text elements carry `aria-label` attributes to describe their function for screen readers.
- **Color Contrast:** We stick to AA standards or better (e.g., black text (#000000) on yellow background (#FFF200) passes contrast checks).

### Responsiveness
- **Mobile-First Layouts:** Design components to fit small screens first, then scale up. Key elements (menus, buttons) stack vertically on narrow viewports.
- **Fluid Grids & Breakpoints:** We use Tailwind’s responsive utilities (`sm:`, `md:`, `lg:`) to rearrange content based on screen size.

## 3. Styling and Theming

### CSS Methodology
- **Utility-First with Tailwind CSS:** We avoid custom CSS files unless absolutely necessary. Utility classes handle layout, spacing, colors, and typography.

### Neobrutalism Style
- **Glassmorphism, Flat, Material?** We follow a Neobrutalist look:
  - Bold blocks with thick black borders
  - High-contrast color fills
  - Minimal shadows (or none)
  - Sharp corners or slightly rounded (4px) where needed

### Color Palette
- **Primary Background:** #FFF200 (Yellow)  
- **Accent 1:** #0050FF (Electric Blue)  
- **Accent 2:** #FF2C2C (Red Alert)  
- **Secondary Text:** #222222 (Dark Gray)  
- **Borders & Text:** #000000 (Black)

### Typography
- **Headings & Code:** IBM Plex Mono, JetBrains Mono, or Space Mono  
- **Body Copy:** Inter, DM Sans, or Lexend Deca  
- **Code Blocks / Inline Code:** JetBrains Mono

### Theming
All colors and fonts live in `tailwind.config.js`. If we want to switch themes in the future (dark mode, alternate palettes), we’ll add them under a `theme` section and toggle via a top-level CSS class (e.g., `.theme-dark`).

## 4. Component Structure

### Folder Organization
```
src/
  components/
    Button.svelte
    Card.svelte
    GraphViewer.svelte
    Navbar.svelte
    …
  pages/
    Dashboard.svelte
    TopicCreation.svelte
    TopicDetail.svelte
    Settings.svelte
    …
  stores/
    auth.js
    topicStore.js
    uiStore.js
  services/
    api.js
    ipfs.js
    web3.js
  App.svelte
  main.js
```

### Reusability
- **Atomic Components:** Buttons, inputs, cards live under `components/`. They accept props (e.g., `size`, `color`, `onClick`) so we avoid duplication.
- **Composite Components:** Pages assemble atomic components into screens (e.g., Dashboard uses Card, Chart, Button).

## 5. State Management

### Svelte Stores
We use Svelte’s built-in writable and derived stores for global state:
- **auth.js:** Holds wallet connection status, NFT ownership flag, user address.
- **topicStore.js:** Tracks current topics list, selected topic details, ingestion status.
- **uiStore.js:** Manages UI flags (e.g., loading spinners, modals open/closed).

### Sharing State
Components subscribe to these stores. When one component updates a store (e.g., after login), all subscribers reactively update their view.

## 6. Routing and Navigation

### Router Library
We use `svelte-spa-router` for client-side routing. Routes are defined in `main.js`:
```js
import Router from 'svelte-spa-router';
import Dashboard from './pages/Dashboard.svelte';
import TopicCreation from './pages/TopicCreation.svelte';
// …

const routes = {
  '/': Dashboard,
  '/create': TopicCreation,
  '/topic/:id': TopicDetail,
  '/settings': Settings
};
```

### Navigation Structure
- **Navbar:** Links to Dashboard, New Topic, Analytics, Account.
- **Breadcrumbs:** On topic detail pages, we show `Home / Topic Name` for context.
- **Programmatic Navigation:** After a successful content ingestion or wallet connection, we redirect users to the next logical page via the router’s `goto()` function.

## 7. Performance Optimization

- **Code Splitting & Lazy Loading:** Pages are lazy-loaded so the initial bundle only contains core app code. Other pages load on demand.
- **Image & Asset Optimization:** SVG icons inline; larger graphics optimized and lazy-loaded.
- **Tailwind PurgeCSS:** Unused CSS classes are removed in production builds to keep CSS under 50 KB.
- **Svelte Compiler:** Tree-shaking and ahead-of-time compilation eliminate dead code.
- **API Debouncing:** In the query interface, we debounce user input (e.g., 300 ms) to avoid flooding the backend.

## 8. Testing and Quality Assurance

### Unit Testing
- **Vitest + @testing-library/svelte:** We write unit tests for components (e.g., Button renders correctly, GraphViewer reacts to prop changes).

### Integration Testing
- **Testing Library:** Verify interactions between components (e.g., creating a topic updates the topic list).

### End-to-End (E2E) Testing
- **Cypress:** We simulate real user flows—login with a test wallet, ingest content, build a graph, run a query, download audio.

### Linting and Formatting
- **ESLint + Prettier:** Enforce consistent code style and catch common mistakes. Tailwind classes sorted with `eslint-plugin-tailwindcss`.

### Continuous Integration
- **GitHub Actions:** On each PR, we run lint, unit tests, and a headless Cypress smoke test.

## 9. Conclusion and Overall Frontend Summary

Study4Me’s frontend is built for speed, clarity, and growth. By choosing Svelte and Tailwind:
- We deliver a snappy user experience with minimal bundle sizes.
- We keep our codebase easy to read and extend through component-driven design.
- We ensure accessibility and responsiveness so every student can focus on learning, not wrestling with the UI.

All our styling, routing, state, and testing guidelines work together to support Study4Me’s goals: making blockchain-gated, interactive study tools that scale with user needs.

With these guidelines, any new developer or designer can jump in and know exactly where to add features, fix bugs, or tweak the look and feel—all while keeping consistency and quality top of mind.