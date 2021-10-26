import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { HTMLTable, Colors, Button, Classes } from '@blueprintjs/core'
import { useForm } from 'react-hook-form'
import styled from 'styled-components'
import useContestsJurisdictionAdmin from './useContestsJurisdictionAdmin'
import { useBatches, IBatch, useRecordBatchResults } from './useBatchResults'
import { IRound } from '../useRoundsAuditAdmin'
import { sum } from '../../../utils/number'
import { IContest } from '../../../types'

const ResultsTable = styled(HTMLTable).attrs({
  striped: true,
  bordered: true,
})`
  position: relative;
  width: 100%;
  table-layout: fixed;
  border-collapse: separate;

  // th {
  //   position: sticky;
  //   top: 0;
  //   z-index: 1;
  //   border-bottom: 1px solid ${Colors.GRAY2};
  //   background: ${Colors.WHITE};
  // }

  thead tr th {
    box-shadow: none !important;
    vertical-align: bottom;
  }

  tr td {
    vertical-align: middle;
    word-wrap: break-word;
  }

  /* Exclude edit buttons from copy/paste */
  th:first-child,
  td:first-child {
    -moz-user-select: none; /* stylelint-disable-line property-no-vendor-prefix */
    -webkit-user-select: none; /* stylelint-disable-line property-no-vendor-prefix */
    user-select: none;
  }
`

const AngledTH = styled.th`
  /* Something you can count on */
  height: 140px;
  white-space: nowrap;
  position: relative;

  > div {
    // /* Magic Numbers */ translate(25px, 51px)
    transform: rotate(315deg);
    width: 0px;
    position: absolute;
    right: 10px;
    bottom: 0px;
  }
  > div > span {
    border-bottom: 1px solid #ccc;
    padding: 5px 10px;
  }
`

const ChoiceTD = styled.td`
  width: 100px;
  vertical-align: middle;
  min-width: 50px;
`

const totalStyle = { color: Colors.BLUE3, fontWeight: 600 }

const BatchResultsForm = ({
  electionId,
  jurisdictionId,
  roundId,
  contest,
  batch,
  closeForm,
}: {
  electionId: string
  jurisdictionId: string
  roundId: string
  contest: IContest
  batch: IBatch
  closeForm: () => void
}) => {
  const recordBatchResults = useRecordBatchResults(
    electionId,
    jurisdictionId,
    roundId
  )
  const { register, handleSubmit, watch, formState } = useForm<{
    [choiceId: string]: number
  }>({
    defaultValues:
      batch.results ||
      Object.fromEntries(contest.choices.map(c => [c.id, undefined])),
  })

  const onSubmit = (results: { [choiceId: string]: number }) => {
    recordBatchResults.mutate(
      { batchId: batch.id, results },
      { onSuccess: closeForm }
    )
  }

  return (
    <tr key={batch.id}>
      <td>{batch.name}</td>
      {contest.choices.map(choice => (
        <ChoiceTD key={`${batch.name}-${choice.id}`}>
          <input
            className={Classes.INPUT}
            type="number"
            name={choice.id}
            ref={register({
              valueAsNumber: true,
              min: 0,
              max: Number.MAX_SAFE_INTEGER,
            })}
            style={{ width: '100%' }}
          />
        </ChoiceTD>
      ))}
      <td style={totalStyle}>
        {sum(Object.values(watch()).filter(n => n)).toLocaleString()}
      </td>
      <td style={{ paddingRight: 0 }}>
        <Button
          intent="primary"
          icon="tick"
          onClick={handleSubmit(onSubmit)}
          loading={formState.isSubmitting}
        >
          Save
        </Button>
        <Button
          small
          minimal
          style={{ marginLeft: '5px' }}
          icon="cross"
          onClick={closeForm}
          loading={formState.isSubmitting}
        />
      </td>
    </tr>
  )
}

const BatchRoundDataEntry = ({ round }: { round: IRound }) => {
  const { electionId, jurisdictionId } = useParams<{
    electionId: string
    jurisdictionId: string
  }>()
  const contests = useContestsJurisdictionAdmin(electionId, jurisdictionId)
  const batchesResp = useBatches(electionId, jurisdictionId, round.id)
  const [editingBatch, setEditingBatch] = useState<IBatch['id'] | null>(null)

  if (!contests || !batchesResp.isSuccess) return null

  // Batch comparison audits only support a single contest
  const [contest] = contests
  const { batches } = batchesResp.data

  const total = (choiceId: string) =>
    sum(
      batches
        .filter(batch => batch.results !== null)
        .map(batch => batch.results![choiceId])
    )

  return (
    <div>
      <p>
        When you have examined all the ballots assigned to you, enter the number
        of votes recorded for each candidate/choice from the audited ballots.
      </p>
      <ResultsTable id="results-table">
        <thead>
          <tr>
            <th>Batch Name</th>
            {contest.choices.map(choice => (
              <AngledTH key={`th-${choice.id}`}>
                <div>
                  <span>{choice.name}</span>
                </div>
              </AngledTH>
            ))}
            <AngledTH style={totalStyle}>
              <div>
                <span>Total Votes in Batch</span>
              </div>
            </AngledTH>
            <th style={{ width: '120px' }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {batches.map(batch =>
            batch.id === editingBatch ? (
              <BatchResultsForm
                electionId={electionId}
                jurisdictionId={jurisdictionId}
                roundId={round.id}
                contest={contest}
                batch={batch}
                key={batch.id}
                closeForm={() => setEditingBatch(null)}
              />
            ) : (
              <tr key={batch.id}>
                <th>{batch.name}</th>
                {contest.choices.map(choice => (
                  <ChoiceTD key={`${batch.name}-${choice.id}`}>
                    {batch.results && batch.results[choice.id].toLocaleString()}
                  </ChoiceTD>
                ))}
                <td style={totalStyle}>
                  {batch.results &&
                    sum(Object.values(batch.results)).toLocaleString()}
                </td>
                <td>
                  <Button
                    icon="edit"
                    disabled={editingBatch !== null}
                    onClick={() => setEditingBatch(batch.id)}
                  >
                    Edit
                  </Button>
                </td>
              </tr>
            )
          )}
          <tr>
            <td style={totalStyle}>Total Votes</td>
            {contest.choices.map(choice => (
              <td style={totalStyle} key={`total-${choice.id}`}>
                {total(choice.id).toLocaleString()}
              </td>
            ))}
            <td style={totalStyle}>
              {sum(
                contest.choices.map(choice => total(choice.id))
              ).toLocaleString()}
            </td>
            <td />
          </tr>
        </tbody>
      </ResultsTable>
    </div>
  )
}

export default BatchRoundDataEntry
