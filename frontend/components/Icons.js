/** Yengil inline SVG ikonkalar — tashqi kutubxona shart emas. */

const base = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export const Eye = (p) => (
  <svg {...base} {...p}>
    <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z" />
    <circle cx="12" cy="12" r="3" />
  </svg>
);

export const EyeOff = (p) => (
  <svg {...base} {...p}>
    <path d="M10.6 5.2A9.9 9.9 0 0 1 12 5c6.4 0 10 7 10 7a17.6 17.6 0 0 1-3.2 4.2M6.2 6.2A17.7 17.7 0 0 0 2 12s3.6 7 10 7a9.7 9.7 0 0 0 4.3-1" />
    <path d="m3 3 18 18" />
    <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
  </svg>
);

export const Check = (p) => (
  <svg {...base} {...p}>
    <path d="m20 6-11 11-5-5" />
  </svg>
);

export const X = (p) => (
  <svg {...base} {...p}>
    <path d="M18 6 6 18M6 6l12 12" />
  </svg>
);

export const Users = (p) => (
  <svg {...base} {...p}>
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" />
  </svg>
);

export const Clock = (p) => (
  <svg {...base} {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </svg>
);

export const Calendar = (p) => (
  <svg {...base} {...p}>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M16 3v4M8 3v4M3 11h18" />
  </svg>
);

export const Book = (p) => (
  <svg {...base} {...p}>
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
  </svg>
);

export const Inbox = (p) => (
  <svg {...base} {...p}>
    <path d="M22 12h-6l-2 3h-4l-2-3H2" />
    <path d="M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.7 4H7.3a2 2 0 0 0-1.8 1.1Z" />
  </svg>
);

export const Swap = (p) => (
  <svg {...base} {...p}>
    <path d="m16 3 4 4-4 4" />
    <path d="M20 7H4" />
    <path d="m8 21-4-4 4-4" />
    <path d="M4 17h16" />
  </svg>
);

export const LogOut = (p) => (
  <svg {...base} {...p}>
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
    <path d="m16 17 5-5-5-5M21 12H9" />
  </svg>
);

export const Plus = (p) => (
  <svg {...base} {...p}>
    <path d="M12 5v14M5 12h14" />
  </svg>
);

export const Upload = (p) => (
  <svg {...base} {...p}>
    <path d="M12 16V4M7 9l5-5 5 5" />
    <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
  </svg>
);

export const FileText = (p) => (
  <svg {...base} {...p}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
    <path d="M14 2v6h6M8 13h8M8 17h8M8 9h2" />
  </svg>
);

export const ChevronDown = (p) => (
  <svg {...base} {...p}>
    <path d="m6 9 6 6 6-6" />
  </svg>
);

export const ChevronRight = (p) => (
  <svg {...base} {...p}>
    <path d="m9 6 6 6-6 6" />
  </svg>
);

export const HelpCircle = (p) => (
  <svg {...base} {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.5-2 2-2 3.5M12 17.5v.01" />
  </svg>
);

export const Hourglass = (p) => (
  <svg {...base} {...p}>
    <path d="M7 2h10M7 22h10" />
    <path d="M17 2v3.5a5 5 0 0 1-2.5 4.3L12 11l-2.5-1.2A5 5 0 0 1 7 5.5V2" />
    <path d="M7 22v-3.5a5 5 0 0 1 2.5-4.3L12 13l2.5 1.2a5 5 0 0 1 2.5 4.3V22" />
  </svg>
);

export const Send = (p) => (
  <svg {...base} {...p}>
    <path d="m22 2-20 7 8.5 3.5L14 21l8-19Z" />
    <path d="M10.5 12.5 22 2" />
  </svg>
);

export const Trophy = (p) => (
  <svg {...base} {...p}>
    <path d="M8 21h8M12 17v4" />
    <path d="M7 4h10v5a5 5 0 0 1-10 0V4Z" />
    <path d="M7 5H4a3 3 0 0 0 3 4M17 5h3a3 3 0 0 1-3 4" />
  </svg>
);
