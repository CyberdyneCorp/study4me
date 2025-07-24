# Frontend Guideline Document for Study4Me

## 1. Frontend Architecture

### Overview

Our frontend is a Single Page Application (SPA) built with Svelte and bundled with Vite. We use Tailwind CSS for Neobrutalism styling. Authentication flows (login, NFT checks) are handled via Web3Auth and WalletConnect. The app communicates with our FastAPI backend over REST to fetch or post data (e.g., topics, graphs, audio summaries).

### How It Scales and Stays Maintainable

- **Modular Code:** We break pages and features into small, self-contained Svelte components. This makes it easy to add new features or fix bugs without touching unrelated code.
- **Tailwind Utility Classes:** Instead of writing big CSS files, we use Tailwind’s atomic classes. This keeps styles consistent and avoids naming clashes.
- **Vite’s Fast HMR:** Hot Module Replacement (HMR) means developers can see changes instantly without a full reload.
- **Separation of Concerns:** UI logic lives in Svelte components, styling lives in Tailwind, and API calls live in a dedicated `services/` folder. This clear separation helps new developers understand the codebase quickly.

## 2. Design Principles

### Usability

- **Clear Layouts:** Bold blocks and high-contrast colors guide users through each step. Primary actions (like "Study") use blue, secondary actions (like "Add/Remove Sources") use warning pink, and special features (like "Graph") use red.
- **Simple Flows:** Dashboard shows all available topics with clear action buttons. Each topic card has three distinct actions with color-coded hierarchy.

### Accessibility

- **Keyboard Navigation:** All interactive elements (buttons, links, form fields) have clear focus states and can be used without a mouse.
- **ARIA Labels:** Non-text elements carry `aria-label` attributes to describe their function for screen readers.
- **Color Contrast:** We stick to AA standards or better (e.g., black text (#000000) on yellow background (#FFF200) passes contrast checks).

### Responsiveness

- **Mobile-First Layouts:** Design components to fit small screens first, then scale up. Key elements (menus, buttons) stack vertically on narrow viewports.
- **Fluid Grids & Breakpoints:** We use Tailwind’s responsive utilities (`sm:`, `md:`, `lg:`) to rearrange content based on screen size.

## 3. Styling and Theming

### CSS Methodology

- **Inline Styles with CSS Variables:** Currently uses inline styles for rapid prototyping and debugging. CSS variables in app.css define the color palette. Tailwind CSS is configured but not actively used in current implementation.

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
- **Warning Pink:** #EC4899 (Pink for secondary actions)
- **Success Green:** #10B981 (Green for status indicators)
- **Secondary Text:** #222222 (Dark Gray)  
- **Borders & Text:** #000000 (Black)

### Typography

- **Headings & Code:** IBM Plex Mono, JetBrains Mono, or Space Mono  
- **Body Copy:** Inter, DM Sans, or Lexend Deca  
- **Code Blocks / Inline Code:** JetBrains Mono

### Theming

All colors and fonts live in `tailwind.config.ts`. If we want to switch themes in the future (dark mode, alternate palettes), we’ll add them under a `theme` section and toggle via a top-level CSS class (e.g., `.theme-dark`).

## 4. Component Structure

### Folder Organization

```
src/
  components/
    Button.svelte
    Card.svelte
    ChatModal.svelte
    GraphViewer.svelte
    Navbar.svelte
    SourcesModal.svelte
    …
  pages/
    Dashboard.svelte
    TopicCreation.svelte
    TopicDetail.svelte
    Settings.svelte
    …
  stores/
    auth.ts
    topicStore.ts
    uiStore.ts
  services/
    api.ts
    ipfs.ts
    web3.ts
  App.svelte
  main.ts
```

### Reusability

- **Atomic Components:** Buttons, inputs, cards live under `components/`. They accept props (e.g., `size`, `color`, `onClick`) so we avoid duplication.
- **Composite Components:** Pages assemble atomic components into screens (e.g., Dashboard uses Card, Chart, Button).

## 5. State Management

### Svelte Stores

We use Svelte’s built-in writable and derived stores for global state:

- **auth.ts:** Holds wallet connection status, NFT ownership flag, user address.
- **topicStore.ts:** Tracks current topics list, selected topic details, ingestion status.
- **uiStore.ts:** Manages UI flags (e.g., loading spinners, modals open/closed, chat modal state, sources modal state).

### Sharing State

Components subscribe to these stores. When one component updates a store (e.g., after login), all subscribers reactively update their view.

## 6. Routing and Navigation

### Router Library

Please don't use Router library

### Navigation Structure

- **Navbar:** Contains Study4Me branding with MCP status indicator below, Dashboard label, and Connect Wallet button.
- **MCP Toggle:** Small status indicator positioned below the Study4Me title showing MCP enabled/disabled state.
- **Topic Cards:** Each card includes "Study" (primary), "Add/Remove Sources" (warning pink), and "Graph" (red, top-right corner) buttons.
- **No Router:** Currently uses single-page design without client-side routing for simplicity.

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

## 9. Current Implementation Details

### Dashboard Layout

- **Header:** Study4Me title with small MCP toggle below, Dashboard indicator, and Connect Wallet button
- **Topic Cards:** White cards with thick black borders containing:
  - Title in IBM Plex Mono font
  - Description text
  - Status badge (completed/processing) with appropriate colors
  - Date information
  - Three action buttons: Study (blue), Add/Remove Sources (pink), Graph (red, top-right)

### Button Color System

- **Study Button:** #0050FF (Electric Blue) - Primary learning action
- **Add/Remove Sources:** #EC4899 (Warning Pink) - Content management
- **Graph Button:** #FF2C2C (Red Alert) - Knowledge graph visualization
- **Connect Wallet:** #0050FF (Electric Blue) - Authentication action
- **MCP Toggle:** #10B981 (Success Green) when enabled

### Typography Hierarchy

- **Main Title:** 1.5rem IBM Plex Mono, bold
- **Card Titles:** 1.25rem IBM Plex Mono, bold
- **Body Text:** Inter font family
- **MCP Status:** 0.65rem IBM Plex Mono (very small)
- **Buttons:** 0.875rem IBM Plex Mono, bold

### Chat Modal Interface

- **Modal Layout:** Centered overlay with four distinct sections:
  - **Header (White):** Topic title, subtitle, and pink close button
  - **Sources Sidebar (Yellow #FFF200):** 25% width, lists all topic sources with blue hover effects
  - **Chat Area (White):** Main conversation interface with message bubbles and input area
  - **Session Sidebar (Yellow #FFF200):** 20% width, content generation actions

- **Interactive Features:**
  - **Source Hover Effects:** Items change to blue background (#0050FF) with white text on hover
  - **Real-time Chat:** Simulated conversation with typing indicators
  - **Keyboard Shortcuts:** Enter to send, Shift+Enter for new line
  - **Session Actions:** Three pink buttons for content generation features
  - **Responsive Design:** 72rem max-width, 80vh height, centered positioning

- **Session Actions Panel:**
  - **Create Podcast:** Pink button (#EC4899) with play icon for audio content generation
  - **Create Mindmap:** Pink button (#EC4899) with network icon for visual knowledge mapping
  - **Summarize Content:** Pink button (#EC4899) with document icon for content summarization
  - **Consistent Sizing:** All buttons 3rem height with 16px SVG icons and white text
  - **No Hover Effects:** Static pink styling for clear action visibility

- **Modal State Management:**
  - **uiStore Integration:** `isChatModalOpen` and `selectedTopicForChat` states
  - **Topic Integration:** Sources loaded from topic data in topicStore
  - **Event Handling:** Study button opens modal, close button/escape/backdrop closes modal

### Sources Modal Interface

- **Modal Layout:** Centered overlay for content management:
  - **Header (White):** Topic title, subtitle, and pink close button
  - **Tab Navigation (Yellow #FFF200):** Three tabs for different source types
  - **Content Area (Light Gray):** Tab-specific interfaces with compact design
  - **Footer (White):** Source counter and action buttons

- **Tab Structure:**
  - **Upload Files Tab:** Drag & drop area, file browser, uploaded files list with file details
  - **Website Tab:** URL input field, scrape button, quick action buttons for content types
  - **YouTube Tab:** Video URL input, add button, feature list in 2-column grid

- **Interactive Features:**
  - **Drag & Drop Upload:** Visual feedback with yellow background on drag hover
  - **File Management:** Display uploaded files with name, size, type, and remove functionality
  - **Tab Switching:** Active tab highlighted with white background
  - **Compact Design:** Smaller fonts and tighter spacing to prevent vertical scrolling

- **Design Optimization:**
  - **Space Efficiency:** Reduced padding, margins, and font sizes for content density
  - **Grid Layouts:** 2-column grids for features and quick actions to maximize horizontal space
  - **Icon Sizing:** Smaller emoji icons (2rem) and compact button layouts
  - **Typography:** Smaller text (0.75rem-0.875rem) while maintaining readability

- **Modal State Management:**
  - **uiStore Integration:** `isSourcesModalOpen` and `selectedTopicForSources` states
  - **Event Handling:** Add/Remove Sources button opens modal, close controls available
  - **File Processing:** Local state management for uploaded files and form inputs

## 10. Conclusion and Overall Frontend Summary

Study4Me's frontend prototype demonstrates the Neobrutalist design principles with a clean, functional dashboard and interactive chat interface. The current implementation focuses on:

- **Bold visual hierarchy** with thick black borders and high-contrast colors
- **Clear user actions** through color-coded button system
- **Interactive chat modal** for study sessions with topic sources and content generation tools
- **Comprehensive sources modal** for file upload, website scraping, and YouTube video integration
- **Functional layout** that prioritizes learning workflows
- **Scalable component structure** ready for future expansion

The prototype successfully establishes the visual identity and core user interactions for the Study4Me platform, including the central chat-based learning interface, providing a solid foundation for further development.
