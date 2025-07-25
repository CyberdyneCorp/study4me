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

#### Neo-Brutalism Extended Palette
- **Cyan:** #7DF9FF (Context mode indicators)
- **Red:** #FF4911 (Graph mode indicators)  
- **Magenta:** #FF00F5 (Book character accents)
- **Yellow:** #FFFF00 (Book character primary)

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
    ConfirmModal.svelte
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
    topicStore.ts      # Backend integrated CRUD operations
    uiStore.ts         # Modal and UI state management
    web3AuthStore.ts   # Web3Auth integration
  services/
    api.ts             # Backend API service with TypeScript interfaces
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
- **topicStore.ts:** Manages study topics with full backend CRUD integration, loading states, error handling, and fallback mechanisms.
- **uiStore.ts:** Manages UI flags (e.g., loading spinners, modals open/closed, chat modal state, sources modal state, confirmation modal state with customizable actions).
- **web3AuthStore.ts:** Handles Web3Auth integration for social authentication and wallet connections.

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

- **Header:** Study4Me title with Dashboard indicator, refresh button, and Connect Wallet button
- **Topic Cards:** White cards with thick black borders containing:
  - **Book Character Icon:** Cute yellow book mascot in top-left corner with smiling face and magenta bookmark
  - **Dynamic Mode Flags:** Top-right corner indicators based on backend configuration:
    - 🔴 **Red "Graph" flag:** Topics with `use_knowledge_graph: true` (with network icon)
    - 🔵 **Cyan "Context" flag:** Topics with `use_knowledge_graph: false` (with document icon)
  - Title in IBM Plex Mono font with left padding to accommodate book icon
  - Description text
  - Status badge (completed/processing) with appropriate colors
  - Date information in YYYY-MM-DD format
  - Three action buttons: Study (blue), Add/Remove Sources (pink)
  - Delete button (red, bottom-right corner) with trash icon for topic removal
- **Card Sizing:** Fixed dimensions with minimum width of 20rem and maximum width of 30rem to prevent stretching when cards are deleted
- **Loading States:** Animated spinner and loading messages during API operations
- **Error Handling:** Error displays with retry functionality

### Button Color System

- **Study Button:** #0050FF (Electric Blue) - Primary learning action
- **Add/Remove Sources:** #EC4899 (Warning Pink) - Content management
- **Graph Button:** #FF2C2C (Red Alert) - Knowledge graph visualization
- **Delete Button:** #FF2C2C (Red Alert) - Destructive action with confirmation modal
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

### Confirmation Modal Interface

- **Modal Layout:** Centered overlay for destructive action confirmation:
  - **Header (White):** Customizable title and pink close button
  - **Content Area (White):** Warning message and action description
  - **Footer (White):** Cancel and confirm buttons with appropriate styling

- **Interactive Features:**
  - **Dangerous Actions:** Red confirm button for destructive operations (e.g., topic deletion)
  - **Safe Actions:** Blue confirm button for non-destructive confirmations
  - **Customizable Text:** Title, message, and button labels can be configured per use case
  - **Keyboard Support:** Enter to confirm, Escape to cancel

- **Design Elements:**
  - **Visual Hierarchy:** Clear distinction between cancel (gray) and confirm buttons
  - **Consistent Styling:** Matches overall Neobrutalist design with thick black borders
  - **Responsive Design:** Centered positioning with appropriate padding and spacing
  - **Icon Integration:** Trash icon for delete confirmations, customizable for other actions

- **State Management:**
  - **uiStore Integration:** `isConfirmModalOpen` and `confirmModalData` with ConfirmModalData interface
  - **Flexible Configuration:** Supports custom title, message, button text, and callback functions
  - **Safe Defaults:** Provides reasonable fallback values for all configurable properties
  - **Event Handling:** Delete button triggers modal, modal handles confirmation flow

- **Usage Patterns:**
  - **Topic Deletion:** Primary use case with "Are you sure you want to delete..." messaging
  - **Extensible Design:** Can be reused for other destructive actions across the application
  - **Callback System:** onConfirm function allows for flexible action handling per use case

## 10. Backend Integration and API Management

### Study Topics API Integration

The frontend integrates seamlessly with the Study4Me FastAPI backend for complete topic lifecycle management:

#### API Service Architecture
- **Centralized Service:** All backend communication handled through `services/api.ts`
- **TypeScript Interfaces:** Full type safety with backend response models
- **Error Handling:** Comprehensive error catching and user feedback
- **Environment Configuration:** Backend URL configurable via `VITE_BACKEND_URL`

#### Topic CRUD Operations
```typescript
// Create new topic
const response = await apiService.createStudyTopic({
  name: 'Topic Name',
  description: 'Optional description',
  use_knowledge_graph: true
})

// Load all topics
const topics = await apiService.getStudyTopics(limit, offset)

// Delete topic with confirmation
await apiService.deleteStudyTopic(topicId)
```

#### Topic Store Integration
- **Reactive Updates:** Svelte stores automatically update UI when data changes
- **Loading States:** Global loading indicators during API operations
- **Error Management:** Centralized error handling with retry mechanisms
- **Fallback Data:** Sample topics displayed if backend unavailable

#### Data Flow Architecture
1. **Dashboard Mount:** Auto-loads topics from backend via `topicActions.loadTopics()`
2. **Topic Creation:** Modal form calls backend API, updates local store on success
3. **Topic Deletion:** Confirmation modal → backend API call → local store update
4. **Error Handling:** Failed operations display user-friendly error messages with retry options

#### Visual Backend Integration Indicators
- **Dynamic Flags:** Red/Cyan flags based on `use_knowledge_graph` backend setting
- **Date Consistency:** YYYY-MM-DD format matching backend timestamps
- **Status Mapping:** Backend status fields mapped to frontend display states
- **Real-time Refresh:** Manual refresh button to sync with backend state

#### Offline Resilience
- **Graceful Degradation:** Fallback to sample data if backend unreachable
- **Loading Feedback:** Clear indicators when operations are in progress
- **Error Recovery:** Retry mechanisms for failed operations
- **State Consistency:** Local state only updated after successful backend operations

## 11. Conclusion and Overall Frontend Summary

Study4Me's frontend demonstrates Neobrutalist design principles with comprehensive backend integration and real-time study topic management. The current implementation focuses on:

- **Bold visual hierarchy** with thick black borders and high-contrast colors
- **Backend-Integrated CRUD Operations** for study topics with proper error handling
- **Dynamic Visual Indicators** showing knowledge graph vs context-only mode
- **Cute Book Character Mascot** adding personality to each topic card
- **Real-time Data Synchronization** with manual refresh and auto-loading capabilities
- **Interactive chat modal** for study sessions with topic sources and content generation tools
- **Comprehensive sources modal** for file upload, website scraping, and YouTube video integration
- **Safe deletion workflow** with confirmation modal and backend API integration
- **Resilient Error Handling** with fallback data and retry mechanisms
- **Functional layout** that prioritizes learning workflows
- **Scalable component structure** ready for future expansion

The implementation successfully establishes a production-ready integration between frontend and backend systems, providing users with reliable topic management, visual feedback for different study modes, and a solid foundation for the complete Study4Me learning platform.
