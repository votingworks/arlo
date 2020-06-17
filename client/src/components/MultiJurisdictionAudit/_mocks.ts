import { IAuditSettings, IContest } from '../../types'
import {
  IJurisdiction,
  FileProcessingStatus,
  IFileInfo,
  JurisdictionRoundStatus,
  IBallotManifestInfo,
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
      endedAt: null,
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000Z',
      id: 'round-1',
    },
  ],
  twoIncomplete: [
    {
      endedAt: null,
      roundNum: 1,
      isAuditComplete: false,
      startedAt: '2019-07-18T16:34:07.000Z',
      id: 'round-1',
    },
    {
      endedAt: null,
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

const manifestMocks: { [key: string]: IBallotManifestInfo } = {
  empty: {
    file: null,
    processing: null,
    numBatches: 0,
    numBallots: 0,
  },
  processed: {
    file: { name: 'manifest.csv', uploadedAt: '2020-06-08T21:39:05.765Z' },
    processing: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-06-08T21:39:05.765Z',
      completedAt: '2020-06-08T21:39:14.574Z',
      error: null,
    },
    numBatches: 10,
    numBallots: 2117,
  },
  errored: {
    file: {
      name: 'manifest.csv',
      uploadedAt: '2020-05-05T17:25:25.663592',
    },
    processing: {
      completedAt: '2020-05-05T17:25:26.099157',
      error: 'Invalid CSV',
      startedAt: '2020-05-05T17:25:26.097433',
      status: FileProcessingStatus.ERRORED,
    },
    numBallots: null,
    numBatches: null,
  },
}

export const jurisdictionMocks: { [key: string]: IJurisdiction[] } = {
  empty: [],
  noManifests: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.empty,
      currentRoundStatus: null,
    },
  ],
  oneManifest: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.errored,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.empty,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: null,
    },
  ],
  allManifests: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: null,
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: null,
    },
  ],
  oneComplete: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.IN_PROGRESS,
        numBallotsAudited: 4,
        numBallots: 10,
        numSamplesAudited: 5,
        numSamples: 11,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.NOT_STARTED,
        numBallotsAudited: 0,
        numBallots: 20,
        numSamplesAudited: 0,
        numSamples: 22,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numBallotsAudited: 30,
        numBallots: 30,
        numSamplesAudited: 31,
        numSamples: 31,
      },
    },
  ],
  allComplete: [
    {
      id: 'jurisdiction-id-1',
      name: 'Jurisdiction 1',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numBallotsAudited: 10,
        numBallots: 10,
        numSamplesAudited: 11,
        numSamples: 11,
      },
    },
    {
      id: 'jurisdiction-id-2',
      name: 'Jurisdiction 2',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numBallotsAudited: 20,
        numBallots: 20,
        numSamplesAudited: 22,
        numSamples: 22,
      },
    },
    {
      id: 'jurisdiction-id-3',
      name: 'Jurisdiction 3',
      ballotManifest: manifestMocks.processed,
      currentRoundStatus: {
        status: JurisdictionRoundStatus.COMPLETE,
        numBallotsAudited: 30,
        numBallots: 30,
        numSamplesAudited: 31,
        numSamples: 31,
      },
    },
  ],
}

export const contestMocks: {
  [key: string]: IContest[]
} = {
  empty: [],
  oneTargeted: [
    {
      id: 'contest-id-1',
      name: 'Contest 1',
      isTargeted: true,
      totalBallotsCast: '30',
      numWinners: '1',
      votesAllowed: '1',
      jurisdictionIds: [
        'jurisdiction-id-1',
        'jurisdiction-id-2',
        'jurisdiction-id-3',
      ],
      choices: [
        {
          id: 'choice-id-1',
          name: 'Choice One',
          numVotes: '10',
        },
        {
          id: 'choice-id-2',
          name: 'Choice Two',
          numVotes: '20',
        },
      ],
    },
    {
      id: 'contest-id-2',
      name: 'Contest 2',
      isTargeted: false,
      totalBallotsCast: '400',
      numWinners: '2',
      votesAllowed: '2',
      jurisdictionIds: ['jurisdiction-id-1', 'jurisdiction-id-2'],
      choices: [
        {
          id: 'choice-id-3',
          name: 'Choice Three',
          numVotes: '300',
        },
        {
          id: 'choice-id-4',
          name: 'Choice Four',
          numVotes: '100',
        },
      ],
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
