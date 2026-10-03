import { ImageResponse } from "next/og";

export const alt = "SENTINEL. Production breaks. We trace why.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    <div
      style={{
        background: "#5c7285",
        color: "#fefefc",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: "52px 66px",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          fontSize: 22,
          letterSpacing: -1,
        }}
      >
        <span>SENTINEL</span>
        <span style={{ fontSize: 13, color: "#eef4fb", letterSpacing: 1 }}>
          AI SOFTWARE INCIDENT RESPONSE
        </span>
      </div>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          marginTop: 70,
          fontSize: 100,
          fontWeight: 700,
          lineHeight: 0.99,
          letterSpacing: -7,
        }}
      >
        <span>PRODUCTION</span>
        <span>BREAKS.</span>
        <span>
          WE TRACE <span style={{ color: "#d7cfe6" }}>WHY.</span>
        </span>
      </div>
      <span style={{ display: "flex", marginTop: "auto", fontSize: 20, color: "#eef4fb" }}>
        From the first 500 to the exact line of code.
      </span>
    </div>,
    { ...size },
  );
}
