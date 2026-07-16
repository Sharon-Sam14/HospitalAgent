# Design System & Aesthetics Guidelines — MediTriage

To convey safety, professionalism, and rapid response capability, MediTriage uses a modern, clean, clinical design system. It moves away from standard Streamlit layouts to deliver a white-labeled, premium-feel medical application.

---

## 1. Color Palette

The system implements a curated, harmonious color scheme representing sterile safety, warning categories, and operational clarity.

| Token | Hex Value | Application / Meaning |
| :--- | :--- | :--- |
| **Primary (Teal)** | `#0F766E` | Main branding, successful CTA buttons, and active tabs. Offers a clinical, trusted environment. |
| **Hover (Dark Teal)** | `#0B5E57` | Hover states for primary controls. |
| **Accent (Navy)** | `#1E3A8A` | Sidebar highlights and clinic information cards. |
| **Background (Slate Light)**| `#F5F8FA` | Overall app backdrop. High contrast against active surfaces. |
| **Surface (White)** | `#FFFFFF` | Form containers, patient lists, and card containers. |
| **Text (Slate Dark)** | `#0F172A` | Default readable text. High contrast, low eye-strain. |
| **Muted (Slate Grey)** | `#475569` | Secondary text, captions, and placeholders. |
| **Border (Light Grey)** | `#E2E8F0` | Dividers and field borders. |
| **Danger (Red)** | `#DC2626` | Emergency designations, crisis notifications, and cancellation alerts. |
| **Warning (Amber)** | `#D97706` | High priority status tags and warning alerts. |
| **Success (Green)** | `#16A34A` | "Free" doctor indicator, completed cases, and resolved statuses. |
| **Info (Blue)** | `#0284C7` | Queue statuses and information labels. |

---

## 2. Typography

We load typography externally to bypass generic system sans-serif fonts:
*   **Primary Font:** `Inter` (loaded via Google Fonts).
*   **Fallback Fonts:** `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, `Helvetica Neue`, `Arial`.
*   **Header Weights:** Semi-Bold (`600`) for headers (`h1` through `h6`) to display authority and clean layout structure.
*   **Body Text:** Regular (`400`) or Medium (`500`) for label texts.
*   **Line Height:** Structured at `1.65` for optimal readability of symptom queries.

---

## 3. UI Layout & Component Styling

All elements are custom styled in `app.py` via CSS injection (`_inject_css()`):

### 3.1 Containers & Inputs
*   **Roundness:** Uniform border-radius: `8px` (`--r: 8px`) applied to buttons, input fields, containers, and cards.
*   **Borders:** Subtle `1.5px solid var(--border)` for standard inputs.
*   **Focus State:** Border shifts to `var(--primary)` (Teal) with a light teal box-shadow glow when the user focuses on inputs:
    ```css
    box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12)
    ```

### 3.2 Premium Feel & Clean Brand
*   **White-label Design:** Streamlit native branding components are hidden to make it look like a standalone custom medical tool:
    *   Header bar background set to transparent.
    *   Footer and "Made with Streamlit" links hidden (`visibility: hidden`).
    *   Development toolbar and decoration bars hidden (`display: none`).
*   **Paddings:** Responsive padding parameters applied globally to the wrapper to remove awkward, oversized Streamlit margins:
    ```css
    div.block-container {
      padding-top: 2rem !important;
      padding-bottom: 2rem !important;
      padding-left: 2.5rem !important;
      padding-right: 2.5rem !important;
    }
    ```

### 3.3 Status Badges
*   Use custom markdown badges to identify statuses at a glance instead of boring text listings:
    *   `🚑 Emergency` (Red background badge)
    *   `🧠 Mental Health` (Purple background badge)
    *   `🏥 General` (Teal background badge)
    *   `● Free` (Green text tag)
    *   `● Busy` (Orange/Amber text tag)
