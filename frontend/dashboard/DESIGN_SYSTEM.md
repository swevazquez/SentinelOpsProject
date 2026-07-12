# SentinelOps Dashboard Design System

The dashboard uses a restrained dark interface intended for maintenance managers,
reliability engineers, and operations analysts. Operational meaning takes priority
over decorative styling.

## Foundations

- Use the color, typography, spacing, radius, shadow, and layout variables in
  `tokens.css`. Do not introduce one-off values when an existing token applies.
- Follow the 8-pixel spacing grid. The 4-pixel token is reserved for compact
  alignment within controls and badges.
- Use the sans-serif type scale for interface text and the monospace family for
  asset identifiers, run identifiers, timestamps, and numeric operational data.
- Use an 8-pixel radius for controls and a 10-pixel radius for panels. Shadows
  should remain subtle against the dark canvas.

## Color And Status

Neutral surfaces establish hierarchy. Accent colors communicate state:

- Green: healthy or successful
- Yellow: warning or medium risk
- Orange: elevated or high risk
- Red: critical, failed, or destructive
- Blue: informational, selected, or active

Always pair status color with a text label or icon. Never rely on color alone.

## Components

- Cards and panels use the shared surface, border, radius, and shadow tokens.
- Primary buttons are reserved for the main action in a view. Secondary and icon
  buttons use neutral surfaces; destructive actions use the critical treatment.
- Badges and risk chips use compact labels with the semantic status palette.
- Tables use sticky headers, restrained row separators, aligned numeric columns,
  and a visible hover state. Put row-specific actions in the final column.
- Loading, empty, error, confirmation, and toast states must state what happened
  and what the reviewer can do next.

## Interaction Patterns

- Preserve the current view when opening an asset, workflow run, alert, or
  notification. Show instance details in a dialog; use explicit navigation labels
  such as `View all` or a navigation item when changing views.
- Make the full row interactive when a table or execution-list row represents one
  inspectable object. Provide a trailing chevron as a visual cue, a visible keyboard
  focus state, and Enter/Space activation where native button semantics are not
  available.
- Use the same details dialog regardless of whether an object is opened from a
  table, status panel, notification, alert, or header summary.
- Status summary cards may filter the related collection. Show the selected state
  and provide a clear way to return to the unfiltered collection.
- Action buttons must show an immediate pressed, loading, success, or error state.
  Passive status labels should describe durable system state, not transient actions.

## Icons

- Use Lucide icons at 16 or 18 pixels for controls and 20 pixels for navigation.
- Use one icon family throughout the interface and pair navigation icons with
  labels. Icon-only buttons require an accessible label and a tooltip.
- Icons should clarify a command or status. Do not use them as decoration.

## Charts

- Use the semantic palette consistently across charts and legends.
- Keep chart backgrounds transparent and grid lines low contrast.
- Label units and time ranges, and provide a visible legend where multiple series
  are present.
- Preserve exact values in nearby tables or labels so charts are not the only way
  to interpret operational data.
- Use representative data only when a view explicitly identifies it as such;
  otherwise bind charts to API responses.

## Responsive Behavior

The interface is desktop-first and supports tablet review. At narrower widths,
panels stack, tables scroll horizontally, and secondary navigation metadata is
hidden. Core status, navigation, and operational actions remain available.
