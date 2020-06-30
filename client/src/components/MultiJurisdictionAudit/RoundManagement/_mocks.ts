import { IAuditBoard } from '../useAuditBoards'

export const auditBoardMocks: {
  [key in
    | 'empty'
    | 'single'
    | 'double'
    | 'noBallots'
    | 'started'
    | 'signedOff']: IAuditBoard[]
} = {
  empty: [],
  single: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: '',
      passphrase: 'happy randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
  ],
  double: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: '',
      passphrase: 'happy randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
    {
      id: 'audit-board-2',
      name: 'Audit Board #02',
      signedOffAt: '',
      passphrase: 'happy secondary randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
  ],
  noBallots: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: '',
      passphrase: 'happy randomness',
      currentRoundStatus: {
        numSampledBallots: 0,
        numAuditedBallots: 0,
      },
    },
    {
      id: 'audit-board-2',
      name: 'Audit Board #02',
      signedOffAt: '',
      passphrase: 'happy secondary randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
  ],
  started: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: '',
      passphrase: 'happy randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 15,
      },
    },
  ],
  signedOff: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: 'a time in the temporal continuum',
      passphrase: 'happy randomness',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 30,
      },
    },
  ],
}

export default auditBoardMocks
