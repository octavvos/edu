"use client";

import { useState } from "react";
import { FileText, X } from "../Icons";
import { MATERIAL_KIND_LABEL, PREVIEWABLE_MATERIAL_EXTENSIONS, formatFileSize } from "../../lib/materials";

/**
 * "Taqdimot" — yangi tabda ochiladi (oddiy havola).
 * "Vazifa" — sahifaning o'zida, kichikroq preview oynasida ochiladi.
 */
export default function MaterialLink({ material, className, style, children }) {
  const [open, setOpen] = useState(false);

  if (material.kind !== "task") {
    return (
      <a href={material.file} target="_blank" rel="noreferrer" className={className} style={style}>
        {children}
      </a>
    );
  }

  const ext = material.original_filename.includes(".")
    ? material.original_filename.split(".").pop().toLowerCase()
    : "";
  const canEmbed = PREVIEWABLE_MATERIAL_EXTENSIONS.includes(ext);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={className}
        style={{ ...style, background: "none", border: "none", cursor: "pointer", textAlign: "left", font: "inherit" }}
      >
        {children}
      </button>

      {open && (
        <div className="mlk-overlay" onMouseDown={() => setOpen(false)}>
          <div className="card mlk-modal" onMouseDown={(e) => e.stopPropagation()}>
            <div className="row-between">
              <h3 style={{ margin: 0, fontSize: 15 }}>{material.title || material.original_filename}</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>
                <X width={14} height={14} />
              </button>
            </div>

            <div className="row mt-2" style={{ gap: 6 }}>
              <span className="chip" style={{ fontSize: 11 }}>{MATERIAL_KIND_LABEL[material.kind]}</span>
              <span className="dim small">{formatFileSize(material.size_bytes)}</span>
            </div>

            {material.description && <p className="small muted mt-2">{material.description}</p>}

            <div className="mlk-preview mt-3">
              {canEmbed ? (
                ext === "pdf" ? (
                  <iframe src={material.file} title={material.title || material.original_filename} />
                ) : (
                  <img src={material.file} alt={material.title || material.original_filename} />
                )
              ) : (
                <div className="mlk-noembed">
                  <FileText width={26} height={26} className="dim" />
                  <p className="small muted mt-2" style={{ margin: 0 }}>
                    Bu fayl turini shu yerda ko&apos;rish mumkin emas
                  </p>
                </div>
              )}
            </div>

            <a
              href={material.file}
              target="_blank"
              rel="noreferrer"
              className="btn btn-sm mt-3"
              style={{ width: "100%", justifyContent: "center" }}
            >
              Yangi oynada ochish
            </a>
          </div>
        </div>
      )}

      <style jsx>{`
        .mlk-overlay {
          position: fixed;
          inset: 0;
          background: rgba(18, 20, 28, 0.45);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 100;
          padding: 16px;
        }
        .mlk-modal {
          width: 100%;
          max-width: 360px;
          max-height: 70vh;
          overflow-y: auto;
        }
        .mlk-preview {
          border: 1px solid var(--border);
          border-radius: var(--radius);
          overflow: hidden;
          background: var(--bg-subtle);
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 160px;
          max-height: 240px;
        }
        .mlk-preview iframe {
          width: 100%;
          height: 240px;
          border: none;
        }
        .mlk-preview img {
          max-width: 100%;
          max-height: 240px;
          object-fit: contain;
        }
        .mlk-noembed {
          text-align: center;
          padding: 24px;
        }
      `}</style>
    </>
  );
}
