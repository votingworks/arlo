import { IAuditSettings } from '../../../../types'

export interface IValues {
  electionName: IAuditSettings['electionName']
  online: IAuditSettings['online']
  randomSeed: IAuditSettings['randomSeed']
  riskLimit: IAuditSettings['riskLimit']
}
