// eslint-disable-next-line import/prefer-default-export
export function candidateTotalsByBatchTemplateFilePath({
  electionId,
  jurisdictionId,
}: {
  electionId: string
  jurisdictionId: string
}): string {
  return `/api/election/${electionId}/jurisdiction/${jurisdictionId}/batch-tallies/template`
}
