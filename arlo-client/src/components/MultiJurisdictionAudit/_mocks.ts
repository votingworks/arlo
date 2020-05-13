import { IAuditSettings } from '../../types'

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

export default auditSettings
