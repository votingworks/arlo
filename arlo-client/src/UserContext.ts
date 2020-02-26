import React from 'react'
import { IUser } from './types'

export const emptyUser: IUser = {
  name: '',
  permissions: {
    'create:audits': true,
    'read:audits': true,
    'manage:audits': true,
  },
  id: '',
}

export default React.createContext(emptyUser)
