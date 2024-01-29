import React from 'react'

import { IContest } from '../../../../types'

interface IContestChoiceNameConsistencyError {
  anomalousJurisdictionId: string
  anomalousChoiceNames: string[]
  jurisdictionIdWithMostChoices: string
  choiceNamesInJurisdictionWithMostChoices: string[]
}

/**
 * For a given contest in a ballot comparison audit, validates CVR choice names across
 * jurisdictions, returning error details or undefined if there's no error.
 *
 * Returns no error if the audit did not require CVR upload, i.e., wasn't a ballot comparison
 * audit.
 */
export function contestChoiceNameConsistencyError(
  contest: IContest
): IContestChoiceNameConsistencyError | undefined {
  const { cvrChoiceNamesByJurisdiction } = contest
  if (
    !cvrChoiceNamesByJurisdiction ||
    Object.keys(cvrChoiceNamesByJurisdiction).length === 0
  ) {
    return undefined
  }

  const [
    jurisdictionIdWithMostChoices,
    choiceNamesInJurisdictionWithMostChoices,
  ] = Object.entries(cvrChoiceNamesByJurisdiction).reduce(
    (largest, current) =>
      current[1].length > largest[1].length ? current : largest,
    ['', []]
  )
  for (const [jurisdictionId, choiceNamesInJurisdiction] of Object.entries(
    cvrChoiceNamesByJurisdiction
  )) {
    const anomalousChoiceNames: string[] = []
    for (const choiceName of choiceNamesInJurisdiction) {
      if (!choiceNamesInJurisdictionWithMostChoices.includes(choiceName)) {
        anomalousChoiceNames.push(choiceName)
      }
    }
    if (anomalousChoiceNames.length > 0) {
      return {
        anomalousJurisdictionId: jurisdictionId,
        anomalousChoiceNames,
        jurisdictionIdWithMostChoices,
        choiceNamesInJurisdictionWithMostChoices,
      }
    }
  }
  return undefined
}

interface IProps {
  error: IContestChoiceNameConsistencyError
  jurisdictionNamesById: { [jurisdictionId: string]: { name: string } }
}

export const ContestChoiceNameConsistencyError: React.FC<IProps> = ({
  error,
  jurisdictionNamesById,
}) => {
  const {
    anomalousChoiceNames,
    anomalousJurisdictionId,
    choiceNamesInJurisdictionWithMostChoices,
    jurisdictionIdWithMostChoices,
  } = error
  const anomalousJurisdictionName =
    jurisdictionNamesById[anomalousJurisdictionId].name
  const jurisdictionNameWithMostChoices =
    jurisdictionNamesById[jurisdictionIdWithMostChoices].name

  return (
    <span>
      Some choice names in {anomalousJurisdictionName} do not match other
      counties.
      <br />
      <strong>
        Choice names in {anomalousJurisdictionName} without matches:
      </strong>{' '}
      {anomalousChoiceNames.join(' · ')}
      <br />
      <strong>Choice names in {jurisdictionNameWithMostChoices}:</strong>{' '}
      {choiceNamesInJurisdictionWithMostChoices.join(' · ')}
    </span>
  )
}
