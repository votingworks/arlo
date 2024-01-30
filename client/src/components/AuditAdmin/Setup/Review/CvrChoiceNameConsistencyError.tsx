import React from 'react'

import { ICvrChoiceNameConsistencyError } from '../../../../types'

interface IProps {
  error: ICvrChoiceNameConsistencyError
  jurisdictionNamesById: { [jurisdictionId: string]: { name: string } }
}

const CvrChoiceNameConsistencyError: React.FC<IProps> = ({
  error,
  jurisdictionNamesById,
}) => {
  const {
    anomalousCvrChoiceNamesByJurisdiction,
    cvrChoiceNamesInJurisdictionWithMostCvrChoices,
    jurisdictionIdWithMostCvrChoices,
  } = error

  // Display details for the first jurisdiction with anomalous CVR choice names if multiple
  const [anomalousJurisdictionId, anomalousCvrChoiceNames] = Object.entries(
    anomalousCvrChoiceNamesByJurisdiction
  )[0]

  const anomalousJurisdictionName =
    jurisdictionNamesById[anomalousJurisdictionId].name
  const jurisdictionNameWithMostCvrChoices =
    jurisdictionNamesById[jurisdictionIdWithMostCvrChoices].name

  return (
    <span>
      Some choice names in {anomalousJurisdictionName} do not match other
      counties.
      <br />
      <strong>
        Choice names in {anomalousJurisdictionName} without matches:
      </strong>{' '}
      {anomalousCvrChoiceNames.join(' · ')}
      <br />
      <strong>
        Choice names in {jurisdictionNameWithMostCvrChoices}:
      </strong>{' '}
      {cvrChoiceNamesInJurisdictionWithMostCvrChoices.join(' · ')}
    </span>
  )
}

export default CvrChoiceNameConsistencyError
