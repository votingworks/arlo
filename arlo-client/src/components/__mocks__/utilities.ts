import { statusStates } from '../AuditForms/_mocks'
import { Audit } from '../../types'

export const api = jest.fn(
  <T>(endpoint: string, options: any): Promise<T | Audit> => {
    switch (endpoint) {
      case '/audit/status':
        return Promise.resolve(statusStates[0]) as Promise<Audit>
      case '/audit/basic':
        return Promise.resolve({}) as Promise<T>
      default:
        return Promise.reject(new Error('Endpoint not found'))
    }
  }
)

export default api
