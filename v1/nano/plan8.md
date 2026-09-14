You are given a task to integrate an existing React component in the codebase

The codebase should support:
- shadcn project structure  
- Tailwind CSS
- Typescript

If it doesn't, provide instructions on how to setup project via shadcn CLI, install Tailwind or Typescript.

Determine the default path for components and styles. 
If default path for components is not /components/ui, provide instructions on why it's important to create this folder
Copy-paste this component to /components/ui folder:
```tsx
almoayyed.tsx
// GradientBackground — "Almoayyed", made with the 21st.dev Gradient
// Builder and exported as live CSS (the builder's own Copy-CSS background,
// plus its soften-blur and grain passes). Zero dependencies: one <div> that
// fills its parent. Drop it behind your content:
// <div className="relative h-96"><GradientBackground className="absolute inset-0" /></div>
// Remix the source recipe (colors, mode, finish) in the editor:
// https://21st.dev/community/gradients/editor?from=dc893a4f-0b29-4732-9b29-d4de9c0b70ee
export function GradientBackground({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={className}
      style={{
        position: "relative",
        overflow: "hidden",
        width: "100%",
        height: "100%",
        containerType: "size",
      }}
    >
      <div
        style={{
          position: "absolute",
        inset: 0,
        backgroundColor: "#D7D5D5",
        backgroundImage:
          "url(\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.280'/></svg>\"), radial-gradient(circle at 66.94% 46.43%, rgba(215, 213, 213, 1) 0%, rgba(215, 213, 213, 0.844) 19.02%, rgba(215, 213, 213, 0.5) 38.05%, rgba(215, 213, 213, 0.156) 57.07%, rgba(215, 213, 213, 0) 76.1%), radial-gradient(circle at 34.69% 66.31%, rgba(49, 5, 39, 1) 0%, rgba(49, 5, 39, 0.844) 12.73%, rgba(49, 5, 39, 0.5) 25.45%, rgba(49, 5, 39, 0.156) 38.18%, rgba(49, 5, 39, 0) 50.9%), radial-gradient(circle at 48.93% 19.32%, rgba(57, 5, 31, 1) 0%, rgba(57, 5, 31, 0.844) 16.75%, rgba(57, 5, 31, 0.5) 33.5%, rgba(57, 5, 31, 0.156) 50.25%, rgba(57, 5, 31, 0) 67%), radial-gradient(circle at 80.23% 87.54%, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 0.844) 10.28%, rgba(255, 255, 255, 0.5) 20.55%, rgba(255, 255, 255, 0.156) 30.83%, rgba(255, 255, 255, 0) 41.1%)",
        backgroundSize: "120px 120px, auto, auto, auto, auto",
        backgroundBlendMode: "overlay, normal, normal, normal, normal",
        }}
      />
      <svg
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          opacity: 0.280,
          mixBlendMode: "overlay",
        }}
      >
        <filter id="grain-dc893a4f">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.8"
            numOctaves="2"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain-dc893a4f)" />
      </svg>
    </div>
  )
}


demo.tsx
import { GradientBackground } from "@/components/ui/almoayyed"

export default function GradientBackgroundDemo() {
  return (
    <div className="relative h-[440px] w-full overflow-hidden rounded-xl">
      <GradientBackground className="h-full w-full" />
    </div>
  )
}

```

Implementation Guidelines
 1. Analyze the component structure and identify all required dependencies
 2. Review the component's argumens and state
 3. Identify any required context providers or hooks and install them
 4. Questions to Ask
 - What data/props will be passed to this component?
 - Are there any specific state management requirements?
 - Are there any required assets (images, icons, etc.)?
 - What is the expected responsive behavior?
 - What is the best place to use this component in the app?

Steps to integrate
 0. Copy paste all the code above in the correct directories
 1. Install external dependencies
 2. Fill image assets with Unsplash stock images you know exist
 3. Use lucide-react icons for svgs or logos if component requires them

