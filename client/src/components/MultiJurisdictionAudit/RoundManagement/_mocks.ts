import { IBatch } from './useBatchResults'
import { IRound } from '../useRoundsAuditAdmin'
import { FileProcessingStatus } from '../useCSV'
import {
  IOfflineBatchResult,
  IOfflineBatchResults,
} from './useOfflineBatchResults'

export interface INullResultValues {
  [contestId: string]: {
    [choiceId: string]: null | string | number
  }
}

export const roundMocks: {
  [key in 'incomplete' | 'complete' | 'singleIncompleteOffline']: IRound
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
  singleIncompleteOffline: {
    id: 'round-1',
    roundNum: 1,
    startedAt: '2020-09-14T17:35:19.482Z',
    endedAt: null,
    isAuditComplete: false,
    sampledAllBallots: true,
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

export const offlineBatchMocks: {
  [key in
    | 'empty'
    | 'complete'
    | 'updated'
    | 'finalized'
    | 'completeWithMultipleBatch']: IOfflineBatchResults
} = {
  empty: {
    finalizedAt: '',
    results: [],
  },
  complete: {
    finalizedAt: '',
    results: [
      {
        batchName: 'Batch1',
        batchType: 'Other',
        choiceResults: {
          'choice-id-1': 10,
          'choice-id-2': 20,
        },
      },
    ],
  },
  completeWithMultipleBatch: {
    finalizedAt: '',
    results: [
      {
        batchName: 'Batch1',
        batchType: 'Other',
        choiceResults: {
          'choice-id-1': 5,
          'choice-id-2': 15,
        },
      },
      {
        batchName: 'Batch2',
        batchType: 'Provisional',
        choiceResults: {
          'choice-id-1': 5,
          'choice-id-2': 5,
        },
      },
    ],
  },
  updated: {
    finalizedAt: '',
    results: [
      {
        batchName: 'Batch12',
        batchType: 'Other',
        choiceResults: {
          'choice-id-1': 10,
          'choice-id-2': 20,
        },
      },
    ],
  },
  finalized: {
    finalizedAt: '2021-04-13T15:01:00.383031+00:00',
    results: [
      {
        batchName: 'Batch12',
        batchType: 'Other',
        choiceResults: {
          'choice-id-1': 10,
          'choice-id-2': 20,
        },
      },
    ],
  },
}

export const offlineBatchResultsMocks: {
  [key in 'empty' | 'complete' | 'updated']: IOfflineBatchResult
} = {
  empty: {
    batchName: '',
    batchType: '',
    choiceResults: {},
  },
  complete: {
    batchName: 'Batch1',
    batchType: 'Other',
    choiceResults: {
      'choice-id-1': 10,
      'choice-id-2': 20,
    },
  },
  updated: {
    batchName: 'Batch12',
    batchType: 'Other',
    choiceResults: {
      'choice-id-1': 10,
      'choice-id-2': 20,
    },
  },
}
