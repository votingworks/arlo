import { IAuditSettings } from '../../../../types'

export interface IValues {
  csv: File | null
  state: IAuditSettings['state']
}
