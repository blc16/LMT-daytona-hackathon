# LLM Market Timeline - Frontend

Beautiful Next.js frontend for the LLM Market Timeline application.

## Features

- 🎨 Beautiful, modern UI with gradient backgrounds and smooth animations
- 📊 Interactive timeline charts comparing LLM decisions vs market odds
- 🔍 Detailed drill-down into each interval's reasoning and evidence
- ⚡ Real-time experiment configuration and execution
- 🌙 Dark mode support

## Getting Started

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Project Structure

- `app/` - Next.js app router pages
  - `page.tsx` - Main experiment configuration page
  - `experiment/[id]/page.tsx` - Experiment results visualization
- `components/ui/` - Reusable UI components
- `lib/api.ts` - API client for backend integration

## Tech Stack

- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Beautiful charts
- **Lucide React** - Icons
- **date-fns** - Date formatting
