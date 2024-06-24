import { Callout } from '@blueprintjs/core'
import React from 'react'
import styled from 'styled-components'

import { ICvrChoiceNameConsistencyError } from '../../../../types'

const CalloutWithBottomMargin = styled(Callout)`
  margin-bottom: 16px;

  p:last-child {
    margin-bottom: 0;
  }
`

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
    <CalloutWithBottomMargin intent="warning">
      <p>
        Choice names do not match across jurisdictions. Below is an example of a
        mismatch. Address these inconsistencies by adding choice names to your
        standardized contests file or updating your CVR files.
      </p>
      <p>
        <strong>
          Choice names in {anomalousJurisdictionName} not found in{' '}
          {jurisdictionNameWithMostCvrChoices}:
        </strong>{' '}
        {anomalousCvrChoiceNames.join(' · ')}
        <br />
        <strong>
          Choice names in {jurisdictionNameWithMostCvrChoices}:
        </strong>{' '}
        {cvrChoiceNamesInJurisdictionWithMostCvrChoices.join(' · ')}
      </p>
    </CalloutWithBottomMargin>
  )
}

export default CvrChoiceNameConsistencyError
