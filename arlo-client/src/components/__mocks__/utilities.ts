export const api = <T>(endpoint: string, options: any): Promise<T> => {
  if (endpoint === '/audit/basic') {
    return Promise.resolve({}) as Promise<T>
  } else {
    return Promise.reject(new Error('Endpoint not found'))
  }
}

export default api
