export const getMetaContent = (name: string): string | undefined =>
  document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`)?.content

export const shouldRedactDominionBatchAuditFilePrepCvrs = (): boolean =>
  getMetaContent('arlo-redact-dominion-batch-audit-file-prep-cvrs') !== 'false'
