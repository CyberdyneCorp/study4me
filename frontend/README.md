# Study4Me Frontend

A Neobrutalist-styled frontend built with Svelte, Vite, and Tailwind CSS for the Study4Me blockchain-gated study platform.

## Features

- **Neobrutalist Design**: Bold colors, thick borders, high contrast styling
- **Responsive Layout**: Mobile-first design with Tailwind breakpoints
- **Component-Based Architecture**: Reusable Svelte components
- **Type-Safe**: Full TypeScript support
- **Modern Tooling**: Vite for fast development and building

## Tech Stack

- **Framework**: Svelte 5
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom Neobrutalism theme
- **Routing**: svelte-spa-router
- **Language**: TypeScript
- **State Management**: Svelte stores

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Button.svelte
│   ├── Card.svelte
│   ├── Input.svelte
│   ├── Navbar.svelte
│   └── GraphViewer.svelte
├── pages/              # Page components
│   ├── Dashboard.svelte
│   ├── TopicCreation.svelte
│   ├── TopicDetail.svelte
│   └── Settings.svelte
├── stores/             # Svelte stores for state management
│   ├── auth.ts
│   ├── topicStore.ts
│   └── uiStore.ts
├── services/           # API and external service layers
│   ├── api.ts
│   ├── web3.ts
│   └── ipfs.ts
├── App.svelte         # Main app component
├── main.ts            # Entry point
└── app.css            # Global styles and Tailwind imports
```

## Getting Started

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

4. **Preview production build**:
   ```bash
   npm run preview
   ```

## Design System

### Colors
- **Primary Background**: #FFF200 (Yellow)
- **Accent Blue**: #0050FF (Electric Blue)
- **Accent Red**: #FF2C2C (Red Alert)
- **Secondary Text**: #222222 (Dark Gray)
- **Borders & Text**: #000000 (Black)

### Typography
- **Headings**: IBM Plex Mono, JetBrains Mono, Space Mono
- **Body Text**: Inter, DM Sans, Lexend Deca
- **Code**: JetBrains Mono

### Components
- **neo-card**: White cards with black borders
- **neo-button**: Blue buttons that turn red on hover
- **neo-input**: Form inputs with thick black borders

## Development Guidelines

1. **Component Structure**: Keep components small and focused
2. **Styling**: Use Tailwind utility classes, avoid custom CSS
3. **State Management**: Use Svelte stores for global state
4. **Accessibility**: Include proper ARIA labels and keyboard navigation
5. **Responsiveness**: Mobile-first approach with responsive utilities

## Environment Variables

Create a `.env` file with:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_PINATA_JWT=your_pinata_jwt_token
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run check` - Run Svelte type checking

## Contributing

1. Follow the Neobrutalist design principles
2. Maintain component modularity
3. Use TypeScript for type safety
4. Test components before committing
5. Keep accessibility in mind