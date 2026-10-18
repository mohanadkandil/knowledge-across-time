import './globals.css';

export const metadata = {
  title: 'TimeLens — pull history into focus',
  description:
    'Prefix any Wikipedia URL with timelens.to/ to see how human understanding of a topic changed over 250 years — and where the model auditing it fails.',
  icons: {
    icon:
      "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%2312100d'/%3E%3Ccircle cx='32' cy='32' r='27' fill='none' stroke='%23c9a24b' stroke-width='3'/%3E%3Ccircle cx='32' cy='32' r='14' fill='none' stroke='%23c9a24b' stroke-width='1.5' opacity='.7'/%3E%3C/svg%3E",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=IM+Fell+English+SC&family=Archivo:ital,wght@0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:ital,wght@0,400;0,500;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
