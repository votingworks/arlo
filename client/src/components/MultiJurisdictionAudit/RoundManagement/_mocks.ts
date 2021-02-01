import { IBatch } from './useBatchResults'
import { IRound } from '../useRoundsAuditAdmin'
import { FileProcessingStatus } from '../useCSV'

export interface INullResultValues {
  [contestId: string]: {
    [choiceId: string]: null | string | number
  }
}

export const roundMocks: {
  [key in 'incomplete' | 'complete']: IRound
} = {
  incomplete: {
    id: 'round-1',
    roundNum: 1,
    startedAt: '2020-09-14T17:35:19.482Z',
    endedAt: null,
    isAuditComplete: false,
    sampledAllBallots: false,
    drawSampleTask: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-09-14T17:35:19.482Z',
      completedAt: '2020-09-14T17:36:19.482Z',
      error: null,
    },
  },
  complete: {
    id: 'round-1',
    roundNum: 1,
    startedAt: '2020-09-14T17:35:19.482Z',
    endedAt: '2020-09-14T17:35:19.482Z',
    isAuditComplete: true,
    sampledAllBallots: false,
    drawSampleTask: {
      status: FileProcessingStatus.PROCESSED,
      startedAt: '2020-09-14T17:35:19.482Z',
      completedAt: '2020-09-14T17:36:19.482Z',
      error: null,
    },
  },
}

export const resultsMocks: {
  [key in 'emptyInitial' | 'complete']: INullResultValues
} = {
  emptyInitial: {
    'contest-id-1': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
    'contest-id-2': {
      'choice-id-3': null,
      'choice-id-4': null,
    },
  },
  complete: {
    'contest-id-1': {
      'choice-id-1': 1,
      'choice-id-2': 2,
    },
    'contest-id-2': {
      'choice-id-3': 1,
      'choice-id-4': 2,
    },
  },
}

export const batchResultsMocks: {
  [key in 'empty' | 'complete']: INullResultValues
} = {
  empty: {
    'batch-1': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
    'batch-2': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
    'batch-3': {
      'choice-id-1': null,
      'choice-id-2': null,
    },
  },
  complete: {
    'batch-1': {
      'choice-id-1': 1,
      'choice-id-2': 2,
    },
    'batch-2': {
      'choice-id-1': 1,
      'choice-id-2': 2,
    },
    'batch-3': {
      'choice-id-1': 1,
      'choice-id-2': 2,
    },
  },
}

export const batchesMocks: {
  [key in 'emptyInitial' | 'complete']: { batches: IBatch[] }
} = {
  emptyInitial: {
    batches: [
      {
        id: 'batch-1',
        name: 'Batch One',
        numBallots: 100,
        auditBoard: null,
      },
      {
        id: 'batch-2',
        name: 'Batch Two',
        numBallots: 100,
        auditBoard: null,
      },
      {
        id: 'batch-3',
        name: 'Batch Three',
        numBallots: 100,
        auditBoard: null,
      },
    ],
  },
  complete: {
    batches: [
      {
        id: 'batch-1',
        name: 'Batch One',
        numBallots: 100,
        auditBoard: {
          id: 'ab-1',
          name: 'Audit Board One',
        },
      },
      {
        id: 'batch-2',
        name: 'Batch Two',
        numBallots: 100,
        auditBoard: {
          id: 'ab-1',
          name: 'Audit Board One',
        },
      },
      {
        id: 'batch-3',
        name: 'Batch Three',
        numBallots: 100,
        auditBoard: {
          id: 'ab-1',
          name: 'Audit Board One',
        },
      },
    ],
  },
}
