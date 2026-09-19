# Assiette design system — Canteen Ticket

Signature: each result is a tear-off cafeteria meal ticket. Perforated edges, a circular price token (the CROUS coin), an amber wax-stamp for last-verified, and a monospace receipt row for price / hours / arrondissement.

## Type

| Role | Face | Weights | Use |
|------|------|---------|-----|
| Display | Bricolage Grotesque | 500, 700 | Logo, hero, ticket titles, stamp |
| Body | Public Sans | 400, 500, 600 | Copy, forms, nav |
| Data | Spline Sans Mono | 400, 500 | Prices, times, timestamps, French phrases |

Load with `font-display: swap`. Body 16px, line-height 1.5.

## Colour tokens

Switched by `data-theme` on `<html>`. Both themes designed together; body text ≥ 4.5:1.

### Light (paper)

| Token | Hex | Role |
|-------|-----|------|
| `--paper` | `#F5F2E9` | Page background |
| `--ticket` | `#FFFDF7` | Ticket surface |
| `--ink` | `#1C2B22` | Primary text |
| `--muted` | `#4A5C52` | Secondary text |
| `--green` | `#2E7D4F` | Primary action |
| `--green-strong` | `#1E5A38` | Primary hover / focus |
| `--amber` | `#E0982A` | Verified stamp |
| `--line` | `#D8D2C2` | Perforation, borders |
| `--warn` | `#C2410C` | Error / refused (with text, never colour alone) |

### Dark (after hours)

| Token | Hex | Role |
|-------|-----|------|
| `--paper` | `#141815` | Page background |
| `--ticket` | `#1B211D` | Ticket surface |
| `--ink` | `#ECEFE8` | Primary text |
| `--muted` | `#B3C0B6` | Secondary text |
| `--green` | `#4FB477` | Primary action |
| `--green-strong` | `#6BC891` | Primary hover |
| `--amber` | `#F0B75C` | Verified stamp |
| `--line` | `#2C332D` | Perforation, borders |
| `--warn` | `#F0774A` | Error |

## Motion

150–300ms, transform/opacity only. Stamp settles with a 8° rotate. Disabled under `prefers-reduced-motion`. No entrance animation on every card — first ticket only, if motion allowed.

## Accessibility floor

- 44px touch targets, 8px gaps
- Visible 2px focus rings (`--green`)
- Freshness: stamp text + date, not colour alone
- `aria-live` for results and errors
- Semantic inputs (`email`, labels not placeholders)

## Anti-patterns (do not)

- Emoji as icons (use inline SVG)
- Serif + terracotta “default AI” look
- Colour-only status
- Hover-only interactions
- Gradients on tickets
