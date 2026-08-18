/** Backend apps/courses/constants.py bilan mos — client tarafida darhol xabar berish uchun. */
export const ALLOWED_MATERIAL_EXTENSIONS = [
  "pdf", "ppt", "pptx", "doc", "docx", "xls", "xlsx",
  "zip", "png", "jpg", "jpeg", "gif", "txt",
];

export const MAX_MATERIAL_SIZE_MB = 50;
export const MAX_MATERIAL_SIZE_BYTES = MAX_MATERIAL_SIZE_MB * 1024 * 1024;

export const MATERIAL_ACCEPT = ALLOWED_MATERIAL_EXTENSIONS.map((ext) => `.${ext}`).join(",");

/** Backend apps/courses/models.py::MaterialKind bilan mos — filtrlash uchun. */
export const MATERIAL_KIND_OPTIONS = [
  { value: "presentation", label: "Taqdimot" },
  { value: "task", label: "Vazifa" },
];
export const MATERIAL_KIND_LABEL = Object.fromEntries(MATERIAL_KIND_OPTIONS.map((o) => [o.value, o.label]));

/** Yuklashdan oldin tekshiradi — noto'g'ri bo'lsa xabar qaytaradi, to'g'ri bo'lsa null. */
export function validateMaterialFile(file) {
  const ext = file.name.includes(".") ? file.name.split(".").pop().toLowerCase() : "";
  if (!ALLOWED_MATERIAL_EXTENSIONS.includes(ext)) {
    return `Ruxsat etilmagan fayl turi (.${ext}). Ruxsat etilgan: ${ALLOWED_MATERIAL_EXTENSIONS.join(", ")}.`;
  }
  if (file.size > MAX_MATERIAL_SIZE_BYTES) {
    return `Fayl hajmi ${MAX_MATERIAL_SIZE_MB} MB dan oshmasligi kerak (yuborilgan: ${(file.size / 1024 / 1024).toFixed(1)} MB).`;
  }
  return null;
}
