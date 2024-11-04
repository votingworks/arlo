import React from 'react'
import { Classes, Colors, Dialog, H6, HTMLTable } from '@blueprintjs/core'
import styled from 'styled-components'
import {
  IJurisdiction,
  useDiscrepanciesByJurisdiction,
} from '../../useJurisdictions'
import useContestsJurisdictionAdmin from '../../JurisdictionAdmin/useContestsJurisdictionAdmin'
import { IContest } from '../../../types'

const ContestDiscrepanciesTable = styled(HTMLTable).attrs({
  bordered: true,
  striped: true,
})`
  &.${Classes.HTML_TABLE} {
    background: #ffffff;
    border: 1px solid ${Colors.LIGHT_GRAY1};
    margin-bottom: 32px;
    table-layout: fixed;
    width: 100%;
  }

  &.${Classes.HTML_TABLE} td {
    vertical-align: middle;
  }
`

const TableHeader = styled(H6)`
  &:first-child {
    margin-top: 8px;
  }
`

/* istanbul ignore next */
function getContestName(contests: IContest[], contestId: string) {
  const contest = contests.find(c => c.id === contestId)
  return contest ? contest.name : `Contest Unknown: ID ${contestId}`
}

/* istanbul ignore next */
function getChoiceName(
  contests: IContest[],
  contestId: string,
  choiceId: string
) {
  const contest = contests.find(c => c.id === contestId)
  if (!contest) return `Contest Unknown: ID ${choiceId}`
  const choice = contest.choices.find(c => c.id === choiceId)
  return choice ? choice.name : `Choice Unknown: ID ${choiceId}`
}

export interface IJurisdictionDiscrepanciesProps {
  electionId: string
  handleClose: () => void
  jurisdiction: IJurisdiction
}

const JurisdictionDiscrepancies: React.FC<IJurisdictionDiscrepanciesProps> = ({
  handleClose,
  jurisdiction,
  electionId,
}) => {
  const discrepancyQuery = useDiscrepanciesByJurisdiction(electionId, {})
  const contestsQuery = useContestsJurisdictionAdmin(
    electionId,
    jurisdiction.id
  )

  if (!discrepancyQuery.isSuccess || !contestsQuery.isSuccess) {
    return null
  }

  const discrepanciesByBatch = discrepancyQuery.data[jurisdiction.id]
  const contests = contestsQuery.data

  return (
    <Dialog
      isOpen
      onClose={handleClose}
      style={{ width: '600px' }}
      title={`${jurisdiction.name} Discrepancies`}
    >
      <div className={Classes.DIALOG_BODY} style={{ marginBottom: 0 }}>
        {Object.entries(discrepanciesByBatch).map(
          ([batchName, discrepanciesByContest]) => {
            return Object.entries(discrepanciesByContest).map(
              ([contestId, contestDiscrepancies]) => (
                <div key={contestId}>
                  <TableHeader>
                    {batchName} - {getContestName(contests, contestId)}
                  </TableHeader>
                  <ContestDiscrepanciesTable>
                    <thead>
                      <tr>
                        <th>Choice</th>
                        <th>Reported Votes</th>
                        <th>Audited Votes</th>
                        <th>Discrepancy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.keys(contestDiscrepancies.discrepancies).map(
                        choiceId => (
                          <tr key={choiceId}>
                            <td>
                              {getChoiceName(contests, contestId, choiceId)}
                            </td>
                            <td>
                              {contestDiscrepancies.reportedVotes[choiceId]}
                            </td>
                            <td>
                              {contestDiscrepancies.auditedVotes[choiceId]}
                            </td>
                            <td>
                              {contestDiscrepancies.discrepancies[choiceId]}
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </ContestDiscrepanciesTable>
                </div>
              )
            )
          }
        )}
      </div>
    </Dialog>
  )
}

export { JurisdictionDiscrepancies }
