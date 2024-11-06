import React from 'react'
import { Classes, Colors, Dialog, H6, HTMLTable } from '@blueprintjs/core'
import styled from 'styled-components'
import {
  IJurisdiction,
  useDiscrepanciesByJurisdiction,
} from '../../useJurisdictions'
import useContestsJurisdictionAdmin from '../../JurisdictionAdmin/useContestsJurisdictionAdmin'
import { IContest } from '../../../types'
import { assert } from '../../utilities'

const ContestDiscrepanciesTable = styled(HTMLTable).attrs({
  bordered: true,
  striped: true,
})`
  background: #ffffff;
  border: 1px solid ${Colors.LIGHT_GRAY1};
  margin-bottom: 32px;
  table-layout: fixed;
  width: 100%;

  td {
    vertical-align: middle;
  }
`

const TableHeader = styled(H6)`
  &:first-child {
    margin-top: 8px;
  }
`

function getContestName(contests: IContest[], contestId: string) {
  const contest = contests.find(c => c.id === contestId)
  assert(contest !== undefined)
  return contest.name
}

function getChoiceName(
  contests: IContest[],
  contestId: string,
  choiceId: string
) {
  const contest = contests.find(c => c.id === contestId)
  assert(contest !== undefined)
  const choice = contest.choices.find(c => c.id === choiceId)
  assert(choice !== undefined)
  return choice.name
}

function formatVoteCount(val: string | number | undefined): string {
  switch (val) {
    case 'o':
      return 'Overvote'
    case 'u':
      return 'Undervote'
    case undefined: // Seen on 'reportedVotes' when a candidate did not have a vote originally
      return '0'
    default:
      if (typeof val === 'string') {
        return val
      }
      return val.toLocaleString()
  }
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

  const discrepanciesByBatchOrBallot = discrepancyQuery.data[jurisdiction.id]
  const contests = contestsQuery.data

  return (
    <Dialog
      isOpen
      onClose={handleClose}
      style={{ width: '600px' }}
      title={`${jurisdiction.name} Discrepancies`}
    >
      <div className={Classes.DIALOG_BODY} style={{ marginBottom: 0 }}>
        {Object.entries(discrepanciesByBatchOrBallot).map(
          ([batchOrBallotName, discrepanciesByContest]) => {
            return Object.entries(discrepanciesByContest).map(
              ([contestId, contestDiscrepancies]) => (
                <div key={contestId}>
                  <TableHeader>
                    {batchOrBallotName} - {getContestName(contests, contestId)}
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
                      {Object.keys(contestDiscrepancies.discrepancies)
                        .filter(
                          choiceID =>
                            contestDiscrepancies.discrepancies[choiceID] !== 0
                        )
                        .map(choiceId => (
                          <tr key={choiceId}>
                            <td>
                              {getChoiceName(contests, contestId, choiceId)}
                            </td>
                            <td>
                              {formatVoteCount(
                                contestDiscrepancies.reportedVotes[choiceId]
                              )}
                            </td>
                            <td>
                              {formatVoteCount(
                                contestDiscrepancies.auditedVotes[choiceId]
                              )}
                            </td>
                            <td>
                              {formatVoteCount(
                                contestDiscrepancies.discrepancies[choiceId]
                              )}
                            </td>
                          </tr>
                        ))}
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
