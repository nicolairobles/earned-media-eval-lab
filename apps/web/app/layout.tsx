import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "earned-media-eval-lab",
  description:
    "Production-shaped AI evaluation workbench for earned-media measurement",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <nav className="topnav">
          <div className="inner">
            <a href="/" className="brand">
              earned-media-<span>eval-lab</span>
            </a>
            <a href="/">Releases</a>
            <a href="/evals/">Eval Report</a>
            <a
              href="https://github.com/nicolairobles/earned-media-eval-lab"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
            </a>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
