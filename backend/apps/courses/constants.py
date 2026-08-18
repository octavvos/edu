"""Kurs kontenti bo'yicha umumiy cheklovlar — model va serializer'lar ishlatadi."""

ALLOWED_MATERIAL_EXTENSIONS = {
    "pdf", "ppt", "pptx", "doc", "docx", "xls", "xlsx",
    "zip", "png", "jpg", "jpeg", "gif", "txt",
}
MAX_MATERIAL_SIZE_MB = 50
MAX_MATERIAL_SIZE_BYTES = MAX_MATERIAL_SIZE_MB * 1024 * 1024
