// One visual language for both eras, applied at the image-generation boundary.
export const ART_STYLE = [
  'A precise copperplate illustration on luminous warm ivory paper (#ece1cb).',
  'Fine charcoal-sepia lines, delicate cross-hatching, subtle paper grain,',
  'sparse muted brass (#c9a24b) and sage (#7fa08b) hand-tinted accents.',
  'One clear composition with generous negative space, wide 16:9 flat artwork.',
  'Both eras use this same printmaking style.',
  'No photography, 3D rendering, dark background, neon, decorative glow,',
  'text, labels, borders, or watermarks.',
].join(' ');

export function artPrompt(scene) {
  return `${scene}\n\nVisual treatment: ${ART_STYLE}\nDepict only the subject described above; do not substitute an unrelated scientific object.`;
}
