import { IAuditSettings } from '../../useAuditSettings'
import { FileProcessingStatus } from '../../useCSV'

export const settingsMock: {
  [key in 'empty' | 'full' | 'offline' | 'batch']: IAuditSettings
} = {
  empty: {
    state: null,
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
    auditType: 'BALLOT_POLLING',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
  full: {
    state: 'AL',
    electionName: 'Election Name',
    online: true,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'BALLOT_POLLING',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
  offline: {
    state: 'AL',
    electionName: 'Election Name',
    online: false,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'BALLOT_POLLING',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
  batch: {
    state: 'AL',
    electionName: 'Election Name',
    online: false,
    randomSeed: '12345',
    riskLimit: 10,
    auditType: 'BATCH_COMPARISON',
    auditMathType: 'BRAVO',
    auditName: 'Test Audit',
  },
}

export const sampleSizeMock = {
  sampleSizes: {
    'contest-id': [
      { prob: 0.54, size: 46, key: 'asn' },
      { prob: 0.7, size: 67, key: '0.7' },
      { prob: 0.5, size: 88, key: '0.5' },
      { prob: 0.9, size: 125, key: '0.9' },
    ],
  },
  selected: null,
  task: {
    status: FileProcessingStatus.PROCESSED,
    startedAt: '2019-07-18T16:34:07.000+00:00',
    completedAt: '2019-07-18T16:35:07.000+00:00',
    error: null,
  },
}

export default settingsMock
