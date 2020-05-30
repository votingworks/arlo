import { IAuditSettings } from '../../types'
import {
  IJurisdiction,
  FileProcessingStatus,
  IFileInfo,
  JurisdictionRoundStatus,
} from './useJurisdictions' // uses IFileInfo instead of IBallotManifest and allows `file: null`
import { IRound } from './useRoundsJurisdictionAdmin' // has roundNum
import { IAuditBoard } from './useAuditBoards'

export const auditSettings: {
  [key in 'blank' | 'onlyState' | 'otherSettings' | 'all']: IAuditSettings
} = {
  blank: {
    state: null,
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
  },
  onlyState: {
    state: 'AL',
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
  },
  otherSettings: {
    state: null,
    electionName: 'Election Name',
    online: true,
    randomSeed: '12345',
    riskLimit: 10,
  },
  all: {
    state: 'AL',
    electionName: 'Election Name',
    online: true,
    randomSeed: '12345',
    riskLimit: 10,
  },
}

export const roundMocks: {
  [key in
    | 'empty'
    | 'singleIncomplete'
    | 'twoIncomplete'
    | 'singleComplete'
    | 'needAnother']: IRound[]
} = {
  empty: [],
  singleIncomplete: [
    {
      endedAt: '',
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000Z',
      id: 'round-1',
    },
  ],
  twoIncomplete: [
    {
      endedAt: '',
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000Z',
      id: 'round-1',
    },
    {
      endedAt: '',
      roundNum: 2,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000Z',
      id: 'round-2',
    },
  ],
  singleComplete: [
    {
      endedAt: 'a time most proper',
      roundNum: 1,
      isAuditComplete: true,
      startedAt: '2019-07-18T16:34:07.000Z',
      id: 'round-1',
    },
  ],
  needAnother: [
    {
      endedAt: 'a time most proper',
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000Z',
      id: 'round-1',
    },
  ],
}

export const jurisdictionMocks: {
  [key in
    | 'empty'
    | 'twoUnprocessed'
    | 'oneUnprocessedOneProcessed'
    | 'twoProcessed'
    | 'oneComplete'
    | 'twoComplete']: IJurisdiction[]
} = {
  empty: [],
  twoUnprocessed: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction One',
      ballotManifest: { file: null, processing: null },
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction Two',
      ballotManifest: { file: null, processing: null },
      currentRoundStatus: null,
    },
  ],
  oneUnprocessedOneProcessed: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction One',
      ballotManifest: {
        file: null,
        processing: {
          status: FileProcessingStatus.PROCESSED,
          startedAt: 'sometime',
          completedAt: 'a different time',
          error: null,
        },
      },
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction Two',
      ballotManifest: { file: null, processing: null },
      currentRoundStatus: null,
    },
  ],
  twoProcessed: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction One',
      ballotManifest: {
        file: null,
        processing: {
          status: FileProcessingStatus.PROCESSED,
          startedAt: 'sometime',
          completedAt: 'a different time',
          error: null,
        },
      },
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction Two',
      ballotManifest: {
        file: null,
        processing: {
          status: FileProcessingStatus.PROCESSED,
          startedAt: 'sometime',
          completedAt: 'a different time',
          error: null,
        },
      },
      currentRoundStatus: null,
    },
  ],
  oneComplete: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction One',
      ballotManifest: {
        file: null,
        processing: {
          status: FileProcessingStatus.PROCESSED,
          startedAt: 'sometime',
          completedAt: 'a different time',
          error: null,
        },
      },
      currentRoundStatus: {
        status: JurisdictionRoundStatus.IN_PROGRESS,
        numBallotsAudited: 0,
        numBallotsSampled: 30,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction Two',
      ballotManifest: {
        file: null,
        processing: {
          status: FileProcessingStatus.PROCESSED,
          startedAt: 'sometime',
          completedAt: 'a different time',
          error: null,
        },
      },
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numBallotsAudited: 30,
        numBallotsSampled: 30,
      },
    },
  ],
  twoComplete: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction One',
      ballotManifest: {
        file: null,
        processing: {
          status: FileProcessingStatus.PROCESSED,
          startedAt: 'sometime',
          completedAt: 'a different time',
          error: null,
        },
      },
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numBallotsAudited: 30,
        numBallotsSampled: 30,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction Two',
      ballotManifest: {
        file: null,
        processing: {
          status: FileProcessingStatus.PROCESSED,
          startedAt: 'sometime',
          completedAt: 'a different time',
          error: null,
        },
      },
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numBallotsAudited: 30,
        numBallotsSampled: 30,
      },
    },
  ],
}

export const fileProcessingMocks: {
  [key in 'null' | 'processed']: IFileInfo['processing']
} = {
  null: null,
  processed: {
    status: FileProcessingStatus.PROCESSED,
    startedAt: 'sometime',
    completedAt: 'a different time',
    error: null,
  },
}

export const auditBoardMocks: {
  [key in 'empty' | 'unfinished' | 'finished']: IAuditBoard[]
} = {
  empty: [],
  unfinished: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: '',
      passphrase: 'happy rebel base',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 0,
      },
    },
  ],
  finished: [
    {
      id: 'audit-board-1',
      name: 'Audit Board #01',
      signedOffAt: '',
      passphrase: 'happy rebel base',
      currentRoundStatus: {
        numSampledBallots: 30,
        numAuditedBallots: 30,
      },
    },
  ],
}
