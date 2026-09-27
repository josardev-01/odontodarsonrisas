export const MAX_SIGNED_DOCUMENT_BYTES = 10 * 1024 * 1024;

export function selectedSignedDocument(data: FormData): File {
  return validateSignedDocument(data.get('attachment'));
}

export function validateSignedDocument(value: FormDataEntryValue | null): File {
  if (!(value instanceof File) || !value.name || value.size === 0) {
    throw new Error('Seleccioná el documento firmado en PDF, JPG o PNG.');
  }
  if (value.size > MAX_SIGNED_DOCUMENT_BYTES) {
    throw new Error('El documento firmado no puede superar 10 MB.');
  }
  if (!/\.(pdf|jpe?g|png)$/i.test(value.name)) {
    throw new Error('El documento debe ser PDF, JPG o PNG.');
  }
  return value;
}
