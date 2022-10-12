import { ITallyEntryUser } from '../UserContext'

const useTallyEntryUser = (): ITallyEntryUser => {
  return {
    type: 'tally_entry',
    id: '1',
    loginCode: '123',
    loginConfirmedAt: null,
    members: [],
    jurisdictionId: 'jurisdiction-id',
    jurisdictionName: 'Los Angeles County',
    electionId: 'election-id',
    auditName: 'General Election Nov 2022',
  }
}

export default useTallyEntryUser
