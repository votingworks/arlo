import React from 'react'
import { Dialog, Spinner, Intent, Classes, H4 } from '@blueprintjs/core'
import styled from 'styled-components'
import { useSamplePreview } from '../../useRoundsAuditAdmin'
import { FlexTable } from '../../../Atoms/Table'
import { sum } from '../../../../utils/number'

interface IProps {
  electionId: string
  auditType: string
  onClose: () => void
}

const CenteredMessage = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
`

// TODO disable for full-hand tallies?
const SamplePreview: React.FC<IProps> = ({
  electionId,
  auditType,
  onClose,
}) => {
  const samplePreview = useSamplePreview(electionId, {
    refetchInterval: result => (result?.jurisdictions ? 0 : 1000),
  })

  if (!samplePreview.isSuccess) {
    return null
  }

  const { task, jurisdictions } = samplePreview.data

  return (
    <Dialog isOpen title="Sample Preview" onClose={onClose}>
      <div className={Classes.DIALOG_BODY}>
        {(() => {
          if (task.completedAt === null) {
            return (
              <CenteredMessage>
                <Spinner intent={Intent.PRIMARY} />
                <H4 style={{ marginTop: '20px' }}>
                  Drawing a random sample of ballots...
                </H4>
                <p>For large elections, this can take a couple of minutes.</p>
              </CenteredMessage>
            )
          }

          if (task.error) {
            return (
              <CenteredMessage>
                <p>There was an error drawing the sample:</p>
                <p>{task.error}</p>
              </CenteredMessage>
            )
          }
          return (
            <FlexTable
              condensed
              striped
              scrollable
              style={{
                background: 'white',
                height: '100%',
                maxHeight: '70vh',
              }}
            >
              <thead>
                <tr>
                  <th>Jurisdiction</th>
                  <th>Samples</th>
                  <th>
                    Unique{' '}
                    {auditType === 'BATCH_COMPARISON' ? 'Batches' : 'Ballots'}
                  </th>
                </tr>
              </thead>
              <tbody>
                {jurisdictions!.map(jurisdiction => (
                  <tr key={jurisdiction.name}>
                    <td>{jurisdiction.name}</td>
                    <td>{jurisdiction.numSamples.toLocaleString()}</td>
                    <td>{jurisdiction.numUnique.toLocaleString()}</td>
                  </tr>
                ))}
                <tr style={{ borderTopWidth: '1px' }}>
                  <td>
                    <strong>Total</strong>
                  </td>
                  <td>
                    <strong>
                      {sum(
                        jurisdictions!.map(j => j.numSamples)
                      ).toLocaleString()}
                    </strong>
                  </td>
                  <td>
                    <strong>
                      {sum(
                        jurisdictions!.map(j => j.numUnique)
                      ).toLocaleString()}
                    </strong>
                  </td>
                </tr>
              </tbody>
            </FlexTable>
          )
        })()}
      </div>
    </Dialog>
  )
}

export default SamplePreview
