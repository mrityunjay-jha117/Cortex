# Cognitive Automator - UI/UX Design System

## 🎨 Theme & Concept
**"Modern Minimalist"**
A clean, premium interface utilizing a stark white and soft-grey palette, accented by subtle shadows, rounded geometry, and a structured dot-grid canvas that gives a technical, graph-based feel.

## 1. Color Palette

The color scheme is completely desaturated (white, greys, and near-blacks) to keep the aesthetic ultra-modern and minimalistic.

| Token | Hex Value | Usage |
| :--- | :--- | :--- |
| **Background (Canvas)** | `#FDFDFD` | The absolute background layer. |
| **Surface (Cards/Panels)** | `#FFFFFF` | Floating panels, node cards, and popups. |
| **Border (Light)** | `#E5E7EB` | Subtle outlines, dividers, and node borders. |
| **Text Primary** | `#111827` | Headings and primary data points. |
| **Text Secondary** | `#6B7280` | Subtitles, helper text, and secondary data. |
| **Text Tertiary** | `#9CA3AF` | Disabled states and placeholder text. |
| **Accent / Hover** | `#F3F4F6` | Button hovers, selected node states. |
| **Shadow Tone** | `rgba(0, 0, 0, 0.05)` | Drop shadows for depth and elevation. |

## 2. Background Canvas (The Dot Grid)

To achieve the modern, spacious dot-grid background (similar to the image provided but with greater distance between the dots), we will use a CSS radial gradient with a generously spaced `background-size`. 
with large sized dots 
**CSS Implementation:**
```css
body, .canvas-container {
  background-color: #FDFDFD;
  background-image: radial-gradient(#D1D5DB 1.5px, transparent 1.5px);
  /* The spacing is set to 40px to create a wider distance between dots */
  background-size: 40px 40px; 
  /* Optional: Smooth panning transition for the canvas */
  transition: background-position 0.1s ease;
}
```

## 3. Typography

**Primary Font:** `Inter` or `Geist` (Modern Sans-Serif)
A highly legible, geometric sans-serif font is crucial for the "tech-minimalist" vibe.

* **Headers (H1/H2):** Font-weight: 600 (Semi-Bold), Letter-spacing: -0.02em, Color: `#111827`
* **Body Text:** Font-weight: 400 (Regular), Letter-spacing: 0em, Color: `#6B7280`
* **Mono/Code (for variables):** `JetBrains Mono` or `Fira Code`, Font-weight: 400

## 4. UI Elements & Styling

### 4.1. Elevation & Shadows (Depth)
Since the colors are flat white and grey, we rely heavily on shadows to distinguish hierarchy and depth on the canvas.
* **Level 1 (Panels):** `box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);`
* **Level 2 (Active Nodes/Hover):** `box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);`
* **Level 3 (Modals/Popups):** `box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.12);`

### 4.2. Borders & Radii (Softness)
* **Standard Elements (Buttons, Inputs):** `border-radius: 8px;`
* **Large Containers (Cards, Nodes):** `border-radius: 12px;`
* **Borders:** 1px solid `#E5E7EB` applied globally to delineate boundaries between white spaces.

### 4.3. Interactive Micro-animations
Elements should feel alive and responsive but not distracting.
* **Hover State:** Slight scale up (`transform: translateY(-2px)`) and a shadow increase.
* **Transitions:** `transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);`

## 5. Components Layout

### Nodes (Graph Elements)
Nodes on the canvas should be stark white cards with thin grey borders, sitting above the dotted grid.
```css
.node-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.node-card:hover {
  border-color: #D1D5DB;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
```

### Controls / Sidebars
The sidebar and property panels should seamlessly blend with the background or float as slightly elevated, separate modules (with white background and soft shadow) to maintain the minimal aesthetic.

## 6. Design Principles
1. **Whitespace is crucial:** Give every element room to breathe. Do not cramp text, icons, or inputs. Padding should be generous (e.g., 16px to 24px inner padding).
2. **Visual Hierarchy:** Use font-weight and text colors (Primary vs. Secondary) rather than different hues to establish importance.
3. **Consistency:** The border-radius, shadows, and greyscale palette must be strictly adhered to across all application components to maintain the premium feel.
